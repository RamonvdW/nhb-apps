# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BestelMutatie
"""

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.utils import DataError, OperationalError, IntegrityError
from django.db.models import Count
from django.db import transaction
from Bestel.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_WACHT_OP_BETALING,
                               BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD,
                               BESTELLING_STATUS2STR, BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK,
                               BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN, BESTEL_MUTATIE_WEBWINKEL_KEUZE,
                               BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN, BESTEL_MUTATIE_VERWIJDER,
                               BESTEL_MUTATIE_MAAK_BESTELLINGEN, BESTEL_MUTATIE_BETALING_AFGEROND,
                               BESTEL_MUTATIE_OVERBOEKING_ONTVANGEN, BESTEL_MUTATIE_RESTITUTIE_UITBETAALD,
                               BESTEL_MUTATIE_ANNULEER, BESTEL_MUTATIE_TRANSPORT,
                               BESTEL_TRANSPORT_OPHALEN, BESTEL_TRANSPORT2STR)
from Bestel.models import BestelProduct, BestelMandje, Bestelling, BestelHoogsteBestelNr, BestelMutatie
from Bestel.plugins.product_info import beschrijf_product, beschrijf_korting
from Bestel.plugins.wedstrijden import (wedstrijden_plugin_automatische_kortingen_toepassen,
                                        wedstrijden_plugin_inschrijven, wedstrijden_plugin_verwijder_reservering,
                                        wedstrijden_plugin_afmelden, wedstrijden_plugin_inschrijving_is_betaald)
from Bestel.plugins.webwinkel import (webwinkel_plug_reserveren, webwinkel_plugin_verwijder_reservering,
                                      webwinkel_plugin_bepaal_kortingen, webwinkel_plugin_bepaal_verzendkosten_mandje,
                                      webwinkel_plugin_bepaal_verzendkosten_bestelling)
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Functie.models import Functie
from Mailer.operations import mailer_queue_email, render_email_template
from NhbStructuur.models import NhbVereniging
from Overig.background_sync import BackgroundSync
from Wedstrijden.definities import (INSCHRIJVING_STATUS_RESERVERING_BESTELD, INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_KORTING_COMBI)
from mollie.api.client import Client, RequestSetupError
from types import SimpleNamespace
from decimal import Decimal
import traceback
import datetime
import sys

EMAIL_TEMPLATE_BACKOFFICE_VERSTUREN = 'email_bestel/backoffice-versturen.dtl'
EMAIL_TEMPLATE_BEVESTIG_BESTELLING = 'email_bestel/bevestig-bestelling.dtl'
EMAIL_TEMPLATE_BEVESTIG_BETALING = 'email_bestel/bevestig-betaling.dtl'


def _beschrijf_bestelling(bestelling):
    producten = (bestelling
                 .producten
                 .select_related('wedstrijd_inschrijving',
                                 'wedstrijd_inschrijving__wedstrijd',
                                 'wedstrijd_inschrijving__sessie',
                                 'wedstrijd_inschrijving__sporterboog',
                                 'wedstrijd_inschrijving__sporterboog__boogtype',
                                 'wedstrijd_inschrijving__sporterboog__sporter',
                                 'wedstrijd_inschrijving__sporterboog__sporter__bij_vereniging',
                                 'wedstrijd_inschrijving__korting',
                                 'webwinkel_keuze',
                                 'webwinkel_keuze__product')
                 # .prefetch_related('wedstrijd_inschrijving__korting__voor_wedstrijden')
                 .order_by('pk'))       # vaste volgorde (primitief, maar functioneel)

    regel_nr = 0
    for product in producten:

        # nieuwe regel op de bestelling
        regel_nr += 1
        product.regel_nr = regel_nr
        product.beschrijving = beschrijf_product(product)

        if product.wedstrijd_inschrijving:
            korting = product.wedstrijd_inschrijving.korting
            if korting:
                product.gebruikte_korting_str, combi_redenen = beschrijf_korting(product)
                if korting.soort == WEDSTRIJD_KORTING_COMBI:
                    product.combi_reden = " en ".join(combi_redenen)
    # for

    producten = list(producten)

    # voeg de eventuele verzendkosten toe als aparte regel op de bestelling
    if bestelling.verzendkosten_euro > 0.001:

        # nieuwe regel op de bestelling
        regel_nr += 1

        verzendkosten_euro_str = "%.2f" % bestelling.verzendkosten_euro
        verzendkosten_euro_str = verzendkosten_euro_str.replace('.', ',')       # nederlandse komma

        product = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=[("Verzendkosten", "")],       # TODO: specialiseren in pakket/briefpost
                        prijs_euro=verzendkosten_euro_str)
        producten.append(product)

    if bestelling.transport == BESTEL_TRANSPORT_OPHALEN:

        # nieuwe regel op de bestelling
        regel_nr += 1

        product = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=[("Ophalen op het bondsbureau", "")],
                        prijs_euro="0,00")
        producten.append(product)

    # voeg de eventuele BTW toe
    for btw_euro, btw_tekst in [(bestelling.btw_euro_cat1, bestelling.btw_percentage_cat1),
                                (bestelling.btw_euro_cat2, bestelling.btw_percentage_cat2),
                                (bestelling.btw_euro_cat3, bestelling.btw_percentage_cat3)]:

        if btw_euro > 0.001:

            product = SimpleNamespace(
                            regel_nr=0,     # geen nummer tonen
                            beschrijving=[(btw_tekst, "")],
                            prijs_euro=btw_euro)
            producten.append(product)
    # for

    return producten


def _beschrijf_transacties(bestelling):
    transacties = (bestelling
                   .transacties
                   .all()
                   .order_by('when'))  # chronologisch

    for transactie in transacties:
        transactie.when_str = timezone.localtime(transactie.when).strftime('%Y-%m-%d om %H:%M')
    # for

    return transacties


def stuur_email_naar_koper_bestelling_details(bestelling):
    """ Stuur een e-mail naar de koper met details van de bestelling en betaalinstructies """

    account = bestelling.account

    producten = _beschrijf_bestelling(bestelling)

    status = bestelling.status
    if status == BESTELLING_STATUS_NIEUW:
        status = BESTELLING_STATUS_WACHT_OP_BETALING

    totaal_euro_str = "%.2f" % bestelling.totaal_euro
    totaal_euro_str = totaal_euro_str.replace('.', ',')       # nederlandse komma

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'producten': producten,
        'bestel_status': BESTELLING_STATUS2STR[status],
        'kan_betalen': bestelling.status not in (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD),
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BESTELLING)

    mailer_queue_email(account.bevestigde_email,
                       'Bestelling op MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


def stuur_email_naar_koper_betaalbevestiging(bestelling):
    """ Stuur een e-mail om de betaalde bestelling te bevestigen """

    account = bestelling.account

    producten = _beschrijf_bestelling(bestelling)

    transacties = _beschrijf_transacties(bestelling)

    totaal_euro_str = "%.2f" % bestelling.totaal_euro
    totaal_euro_str = totaal_euro_str.replace('.', ',')       # nederlandse komma

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'producten': producten,
        'transacties': transacties,
        'wil_ophalen': bestelling.transport == BESTEL_TRANSPORT_OPHALEN,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BETALING)

    mailer_queue_email(account.bevestigde_email,
                       'Bevestiging aankoop via MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


def stuur_email_webwinkel_backoffice(bestelling, email_backoffice):
    """ Stuur een e-mail om de betaalde bestelling te bevestigen """

    account = bestelling.account
    sporter = account.sporter_set.first()

    producten = _beschrijf_bestelling(bestelling)
    transacties = _beschrijf_transacties(bestelling)

    totaal_euro_str = "%.2f" % bestelling.totaal_euro
    totaal_euro_str = totaal_euro_str.replace('.', ',')       # nederlandse komma

    context = {
        'koper_sporter': sporter,       # bevat postadres
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'producten': producten,
        'transacties': transacties,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BACKOFFICE_VERSTUREN)

    mailer_queue_email(email_backoffice,
                       'Verstuur webwinkel producten (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


class Command(BaseCommand):

    help = "Betaal mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__BESTEL_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

        self._instellingen_via_bond = None
        self._instellingen_verkoper_webwinkel = None
        self._instellingen_cache = dict()     # [ver_nr] = BetaalInstellingenVereniging

        self._emailadres_backoffice = Functie.objects.get(rol='MWW').bevestigde_email

        ophalen_ver = NhbVereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)
        self._adres_backoffice = (ophalen_ver.adres_regel1, ophalen_ver.adres_regel2)

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')             # for testing
        parser.add_argument('--fake-hoogste', action='store_true')      # for testing

    def _get_mandje(self, mutatie):
        account = mutatie.account
        if not account:
            self.stderr.write('[ERROR] Mutatie pk=%s met code=%s heeft geen account' % (mutatie.pk, mutatie.code))
            mandje = None
        else:
            # let op: geen prefetch_related('producten') gebruiken i.v.m. mutaties
            mandje, is_created = BestelMandje.objects.get_or_create(account=account)

        return mandje

    def _mandjes_opschonen(self):
        """ Verwijder uit de mandjes de producten die er te lang in liggen """
        self.stdout.write('[INFO] Opschonen mandjes begin')

        verval_datum = timezone.now() - datetime.timedelta(days=settings.MANDJE_VERVAL_NA_DAGEN)

        # doorloop alle producten die nog in een mandje liggen en waarvan de datum verlopen is

        mandje_pks = list()

        # wedstrijden
        for product in (BestelProduct
                        .objects
                        .annotate(mandje_count=Count('bestelmandje'))
                        .exclude(wedstrijd_inschrijving=None)
                        .select_related('wedstrijd_inschrijving',
                                        'wedstrijd_inschrijving__koper',
                                        'wedstrijd_inschrijving__sessie')
                        .filter(mandje_count=1,         # product ligt nog in een mandje
                                wedstrijd_inschrijving__wanneer__lt=verval_datum)):

            inschrijving = product.wedstrijd_inschrijving

            self.stdout.write('[INFO] Vervallen: BestelProduct pk=%s inschrijving (%s) in mandje van %s' % (
                                product.pk, inschrijving, inschrijving.koper))

            wedstrijden_plugin_verwijder_reservering(self.stdout, inschrijving)

            mandje = product.bestelmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestelProduct met pk=%s wordt verwijderd' % product.pk)
            product.delete()
        # for

        # webwinkel
        for product in (BestelProduct
                        .objects
                        .annotate(mandje_count=Count('bestelmandje'))
                        .exclude(webwinkel_keuze=None)
                        .select_related('webwinkel_keuze')
                        .filter(mandje_count=1,         # product ligt nog in een mandje
                                webwinkel_keuze__wanneer__lt=verval_datum)):

            keuze = product.webwinkel_keuze

            self.stdout.write('[INFO] Vervallen: BestelProduct pk=%s webwinkel (%s) in mandje van %s' % (
                                product.pk, keuze.product, keuze.koper))

            # geef de reservering op de producten weer vrij
            webwinkel_plugin_verwijder_reservering(self.stdout, keuze)

            mandje = product.bestelmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            # verwijder de webwinkel keuze
            self.stdout.write('[INFO] WebwinkelKeuze met pk=%s wordt verwijderd' % keuze.pk)
            keuze.product = None
            keuze.delete()

            # verwijder het bestel product
            self.stdout.write('[INFO] BestelProduct met pk=%s wordt verwijderd' % product.pk)
            product.delete()
        # for

        # mandjes bijwerken
        for mandje in BestelMandje.objects.filter(pk__in=mandje_pks):
            wedstrijden_plugin_automatische_kortingen_toepassen(self.stdout, mandje)
            webwinkel_plugin_bepaal_kortingen(self.stdout, mandje)
            webwinkel_plugin_bepaal_verzendkosten_mandje(self.stdout, mandje)
        # for

        self.stdout.write('[INFO] Opschonen mandjes klaar')

    def _clear_instellingen_cache(self):
        self._instellingen_cache = dict()

        ver_bond = NhbVereniging.objects.get(ver_nr=settings.BETAAL_VIA_BOND_VER_NR)

        self._instellingen_via_bond, _ = (BetaalInstellingenVereniging
                                          .objects
                                          .select_related('vereniging')
                                          .get_or_create(vereniging=ver_bond))

        self._instellingen_cache[settings.BETAAL_VIA_BOND_VER_NR] = self._instellingen_via_bond

        # geen foutafhandeling: deze instelling moet gewoon goed staan
        self._instellingen_verkoper_webwinkel = (BetaalInstellingenVereniging
                                                 .objects
                                                 .select_related('vereniging')
                                                 .get(vereniging__ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR))

    def _get_instellingen(self, ver):
        try:
            instellingen = self._instellingen_cache[ver.ver_nr]
        except KeyError:
            instellingen, _ = (BetaalInstellingenVereniging
                               .objects
                               .select_related('vereniging')
                               .get_or_create(vereniging=ver))

            if instellingen.akkoord_via_bond:
                instellingen = self._instellingen_via_bond

            self._instellingen_cache[ver.ver_nr] = instellingen

        return instellingen

    @staticmethod
    def _bestel_get_volgende_bestel_nr():
        """ Neem een uniek bestelnummer uit """
        with transaction.atomic():
            hoogste = (BestelHoogsteBestelNr
                       .objects
                       .select_for_update()                         # lock tegen concurrency
                       .get(pk=BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK))

            # het volgende nummer is het nieuwe unieke nummer
            hoogste.hoogste_gebruikte_bestel_nr += 1
            hoogste.save()

            nummer = hoogste.hoogste_gebruikte_bestel_nr

        return nummer

    @staticmethod
    def _mandje_bepaal_btw(mandje):
        """ bereken de btw voor de producten in het mandje """

        # nog niet ondersteund: toon voorlopig helemaal niets
        mandje.btw_percentage_cat1 = ""
        mandje.btw_euro_cat1 = Decimal(0)

        mandje.btw_percentage_cat2 = ""
        mandje.btw_euro_cat2 = Decimal(0)

        mandje.btw_percentage_cat3 = ""
        mandje.btw_euro_cat3 = Decimal(0)

        mandje.save(update_fields=['btw_percentage_cat1', 'btw_euro_cat1',
                                   'btw_percentage_cat2', 'btw_euro_cat2',
                                   'btw_percentage_cat3', 'btw_euro_cat3'])

    @staticmethod
    def _bestelling_bepaal_btw(bestelling):
        """ bereken de btw voor de producten in een bestelling """

        # nog niet ondersteund: toon voorlopig helemaal niets
        bestelling.btw_percentage_cat1 = ""
        bestelling.btw_euro_cat1 = Decimal(0)

        bestelling.btw_percentage_cat2 = ""
        bestelling.btw_euro_cat2 = Decimal(0)

        bestelling.btw_percentage_cat3 = ""
        bestelling.btw_euro_cat3 = Decimal(0)

        bestelling.save(update_fields=['btw_percentage_cat1', 'btw_euro_cat1',
                                       'btw_percentage_cat2', 'btw_euro_cat2',
                                       'btw_percentage_cat3', 'btw_euro_cat3'])

    def _verwerk_mutatie_wedstrijd_inschrijven(self, mutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            prijs_euro = wedstrijden_plugin_inschrijven(mutatie.wedstrijd_inschrijving)

            # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
            if mutatie.wedstrijd_inschrijving.status != INSCHRIJVING_STATUS_DEFINITIEF:
                # maak een product regel aan voor de bestelling
                product = BestelProduct(
                                wedstrijd_inschrijving=mutatie.wedstrijd_inschrijving,
                                prijs_euro=prijs_euro)
                product.save()

                # leg het product in het mandje
                mandje.producten.add(product)

                # kijk of er automatische kortingen zijn die toegepast kunnen worden
                wedstrijden_plugin_automatische_kortingen_toepassen(self.stdout, mandje)

                # bereken het totaal opnieuw
                self._mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_webwinkel_keuze(self, mutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            webwinkel_keuze = mutatie.webwinkel_keuze

            prijs_euro = webwinkel_plug_reserveren(webwinkel_keuze)

            # maak een product regel aan voor de bestelling
            product = BestelProduct(
                            webwinkel_keuze=webwinkel_keuze,
                            prijs_euro=prijs_euro)
            product.save()

            # leg het product in het mandje
            mandje.producten.add(product)

            webwinkel_plugin_bepaal_kortingen(self.stdout, mandje)

            transport_oud = mandje.transport

            webwinkel_plugin_bepaal_verzendkosten_mandje(self.stdout, mandje)

            # bereken het totaal opnieuw
            self._mandje_bepaal_btw(mandje)
            mandje.bepaal_totaalprijs_opnieuw()

            transport_nieuw = mandje.transport

            self.stdout.write('[INFO] Transport: %s --> %s' % (BESTEL_TRANSPORT2STR[transport_oud],
                                                               BESTEL_TRANSPORT2STR[transport_nieuw]))
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_verwijder(self, mutatie):
        """ een bestelling mag uit het mandje voordat de betaling gestart is """

        if not mutatie.product:
            # mogelijke oorzaak: een dubbele mutatie
            return

        handled = False
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            qset = mandje.producten.filter(pk=mutatie.product.pk)
            if qset.exists():                       # pragma: no branch
                # product zit nog in het mandje (anders: ignore want waarschijnlijk een dubbel verzoek)
                product = qset[0]

                if product.wedstrijd_inschrijving:
                    mandje.producten.remove(product)

                    inschrijving = product.wedstrijd_inschrijving

                    wedstrijden_plugin_verwijder_reservering(self.stdout, inschrijving)

                    mutatie.wedstrijd_inschrijving = None
                    mutatie.product = None
                    mutatie.save()

                    # verwijder het product, dan verdwijnt deze ook uit het mandje
                    product.delete()

                    # verwijder de hele inschrijving, want bewaren heeft geen waarde op dit punt
                    # inschrijving.delete()     # geeft db integratie error i.v.m. referenties die nog ergens bestaan

                    # kijk of er automatische kortingen zijn die niet meer toegepast mogen worden
                    wedstrijden_plugin_automatische_kortingen_toepassen(self.stdout, mandje)

                    handled = True

                elif product.webwinkel_keuze:

                    transport_oud = mandje.transport

                    mandje.producten.remove(product)

                    webwinkel_keuze = product.webwinkel_keuze

                    webwinkel_plugin_verwijder_reservering(self.stdout, webwinkel_keuze)

                    mutatie.webwinkel_keuze = None
                    mutatie.product = None
                    mutatie.save()

                    # verwijder het BestelProduct, dan verdwijnt deze ook uit het mandje
                    product.delete()

                    webwinkel_plugin_bepaal_kortingen(self.stdout, mandje)

                    webwinkel_plugin_bepaal_verzendkosten_mandje(self.stdout, mandje)

                    transport_nieuw = mandje.transport

                    self.stdout.write('[INFO] Transport: %s --> %s' % (BESTEL_TRANSPORT2STR[transport_oud],
                                                                       BESTEL_TRANSPORT2STR[transport_nieuw]))

                    handled = True
                else:
                    self.stderr.write('[ERROR] Verwijder product pk=%s uit mandje pk=%s: Type niet ondersteund' % (
                                        product.pk, mandje.pk))

            # bereken het totaal opnieuw
            self._mandje_bepaal_btw(mandje)
            mandje.bepaal_totaalprijs_opnieuw()

        if not handled:
            # product ligt niet meer in het mandje?!
            self.stdout.write('[WARNING] Product pk=%s niet meer in het mandje gevonden' % mutatie.product.pk)
            if mutatie.product.wedstrijd_inschrijving:
                wedstrijden_plugin_verwijder_reservering(self.stdout, mutatie.product.wedstrijd_inschrijving)

    def _verwerk_mutatie_maak_bestellingen(self, mutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            # zorg dat we verse informatie ophalen (anders duur het 1 uur voordat een update door komt)
            self._clear_instellingen_cache()

            # maak een Mollie-client instantie aan
            mollie_client = Client(api_endpoint=settings.BETAAL_API)

            # verdeel de producten in het mandje naar vereniging waar de betaling heen moet
            ontvanger2producten = dict()      # [ver_nr] = [MandjeProduct, ...]
            for product in (mandje
                            .producten
                            .select_related('wedstrijd_inschrijving',
                                            'wedstrijd_inschrijving__wedstrijd',
                                            'wedstrijd_inschrijving__wedstrijd__organiserende_vereniging',
                                            'webwinkel_keuze')
                            .order_by('wedstrijd_inschrijving__pk',
                                      'webwinkel_keuze__pk')):

                if product.wedstrijd_inschrijving:
                    # wedstrijd van de kalender
                    instellingen = self._get_instellingen(product.wedstrijd_inschrijving.wedstrijd.organiserende_vereniging)
                    ontvanger_ver_nr = instellingen.vereniging.ver_nr       # kan nu ook "via nhb" zijn
                    try:
                        ontvanger2producten[ontvanger_ver_nr].append(product)
                    except KeyError:
                        ontvanger2producten[ontvanger_ver_nr] = [product]

                elif product.webwinkel_keuze:
                    # keuze in de webwinkel
                    ontvanger_ver_nr = self._instellingen_verkoper_webwinkel.vereniging.ver_nr
                    try:
                        ontvanger2producten[ontvanger_ver_nr].append(product)
                    except KeyError:
                        ontvanger2producten[ontvanger_ver_nr] = [product]
            # for

            nieuwe_bestellingen = list()
            for ver_nr, producten in ontvanger2producten.items():

                instellingen = self._instellingen_cache[ver_nr]
                ver = instellingen.vereniging

                # neem een bestelnummer uit
                bestel_nr = self._bestel_get_volgende_bestel_nr()

                totaal_euro = Decimal('0')
                for product in producten:
                    totaal_euro += product.prijs_euro
                    totaal_euro -= product.korting_euro
                # for

                bestelling = Bestelling(
                                    bestel_nr=bestel_nr,
                                    account=mutatie.account,
                                    ontvanger=instellingen,
                                    totaal_euro=totaal_euro,
                                    verkoper_naam=ver.naam,
                                    verkoper_adres1=ver.adres_regel1,
                                    verkoper_adres2=ver.adres_regel2,
                                    verkoper_kvk=ver.kvk_nummer,
                                    verkoper_email=ver.contact_email,
                                    verkoper_telefoon=ver.telefoonnummer,
                                    verkoper_iban=ver.bank_iban,
                                    verkoper_bic=ver.bank_bic)

                instellingen.ondersteunt_mollie = False
                try:
                    mollie_client.validate_api_key(instellingen.mollie_api_key)
                except RequestSetupError:
                    # API key lijkt nergens op
                    pass
                else:
                    bestelling.verkoper_heeft_mollie = True

                bestelling.save()
                bestelling.producten.set(producten)

                webwinkel_plugin_bepaal_verzendkosten_bestelling(self.stdout, mandje.transport, bestelling)

                self._bestelling_bepaal_btw(bestelling)

                totaal_euro += bestelling.verzendkosten_euro
                totaal_euro += bestelling.btw_euro_cat1
                totaal_euro += bestelling.btw_euro_cat2
                totaal_euro += bestelling.btw_euro_cat3

                bestelling.totaal_euro = totaal_euro
                bestelling.save(update_fields=['totaal_euro'])

                totaal_euro_str = "€ %.2f" % totaal_euro
                totaal_euro_str = totaal_euro_str.replace('.', ',')     # nederlandse komma

                when_str = timezone.localtime(bestelling.aangemaakt).strftime('%Y-%m-%d om %H:%M')

                msg = "[%s] Bestelling aangemaakt met %s producten voor totaal %s" % (
                                                when_str, len(producten), totaal_euro_str)
                bestelling.log = msg
                bestelling.save(update_fields=['log'])

                nieuwe_bestellingen.append(bestelling)

                # haal deze producten uit het mandje
                mandje.producten.remove(*producten)

                # pas de status aan van wedstrijd inschrijvingen
                for product in producten:
                    if product.wedstrijd_inschrijving:
                        inschrijving = product.wedstrijd_inschrijving
                        inschrijving.status = INSCHRIJVING_STATUS_RESERVERING_BESTELD
                        inschrijving.save(update_fields=['status'])
                # for

                self.stdout.write(
                    "[INFO] %s producten voor totaal %s uit mandje van account pk=%s (%s) omgezet in bestelling pk=%s" % (
                        len(producten), totaal_euro, mutatie.account.pk, mutatie.account.volledige_naam(), bestelling.pk))
            # for

            # kijk welke bestellingen een nul-bedrag hebben en daarom meteen afgerond kunnen worden
            for bestelling in nieuwe_bestellingen:
                if bestelling.totaal_euro < Decimal('0.001'):
                    self.stdout.write('[INFO] Bestelling pk=%s wordt meteen afgerond' % bestelling.pk)
                    # TODO: ondersteuning voor gratis producten in de webwinkel
                    for product in bestelling.producten.all():
                        if product.wedstrijd_inschrijving:
                            wedstrijden_plugin_inschrijving_is_betaald(product)
                    # for

                    bestelling.status = BESTELLING_STATUS_AFGEROND
                    bestelling.save(update_fields=['status'])
                else:
                    # laat de status op BESTELLING_STATUS_NIEUW staan totdat de betaling opgestart is
                    pass

                # stuur voor elke bestelling een bevestiging naar de koper met details van de bestelling
                # en instructies voor betaling (niet nodig, handmatig, via Mollie)
                stuur_email_naar_koper_bestelling_details(bestelling)
            # for

            # zorg dat het totaal van het mandje ook weer klopt
            webwinkel_plugin_bepaal_verzendkosten_mandje(self.stdout, mandje)
            self._mandje_bepaal_btw(mandje)
            mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_wedstrijd_afmelden(self, mutatie):
        inschrijving = mutatie.wedstrijd_inschrijving
        oude_status = inschrijving.status

        # INSCHRIJVING_STATUS_AFGEMELD --> doe niets
        # INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTEL_MUTATIE_VERWIJDER
        if oude_status == INSCHRIJVING_STATUS_RESERVERING_BESTELD:
            # in een bestelling; nog niet (volledig) betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor wedstrijd' % inschrijving.pk)

            if inschrijving:
                wedstrijden_plugin_verwijder_reservering(self.stdout, inschrijving)
            # FUTURE: betaling afbreken
            # FUTURE: automatische restitutie als de betaling binnen is

        elif oude_status == INSCHRIJVING_STATUS_DEFINITIEF:
            # in een bestelling en betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor wedstrijd' % inschrijving.pk)

            if inschrijving:
                wedstrijden_plugin_afmelden(inschrijving)
            # FUTURE: automatisch een restitutie beginnen

    def _verwerk_mutatie_betaling_afgerond(self, mutatie):
        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        bestelling = mutatie.bestelling
        is_gelukt = mutatie.betaling_is_gelukt

        status = bestelling.status
        if status != BESTELLING_STATUS_WACHT_OP_BETALING:
            self.stdout.write('[WARNING] Bestelling %s (pk=%s) wacht niet op een betaling (status=%s)' % (
                                bestelling.mh_bestel_nr(), bestelling.pk, BESTELLING_STATUS2STR[bestelling.status]))
            return

        actief = bestelling.betaal_actief
        if not actief:
            self.stdout.write('[WARNING] Bestelling %s (pk=%s) heeft geen actieve transactie' % (
                                bestelling.mh_bestel_nr(), bestelling.pk))
            return

        if is_gelukt:
            self.stdout.write('[INFO] Betaling is gelukt voor bestelling %s (pk=%s)' % (
                                bestelling.mh_bestel_nr(), bestelling.pk))

            # koppel alle (nieuwe) transacties aan de bestelling
            payment_id = actief.payment_id
            bestaande_pks = list(bestelling.transacties.all().values_list('pk', flat=True))
            transacties_new = BetaalTransactie.objects.filter(payment_id=payment_id).exclude(pk__in=bestaande_pks)
            bestelling.transacties.add(*transacties_new)

            # controleer of we voldoende ontvangen hebben
            ontvangen_euro = Decimal('0')
            for transactie in bestelling.transacties.all():
                if transactie.is_restitutie:
                    ontvangen_euro -= transactie.bedrag_euro_klant
                else:
                    ontvangen_euro += transactie.bedrag_euro_klant
            # for

            ontvangen_euro_str = "€ %.2f" % ontvangen_euro
            ontvangen_euro_str = ontvangen_euro_str.replace('.', ',')  # nederlandse komma

            totaal_euro_str = "€ %.2f" % bestelling.totaal_euro
            totaal_euro_str = totaal_euro_str.replace('.', ',')  # nederlandse komma

            self.stdout.write('[INFO] Bestelling %s (pk=%s) heeft %s van de %s ontvangen' % (
                                bestelling.mh_bestel_nr(), bestelling.pk, ontvangen_euro_str, totaal_euro_str))

            msg = "\n[%s] Bestelling heeft %s van de %s euro ontvangen" % (
                        when_str, ontvangen_euro_str, totaal_euro_str)
            bestelling.log += msg
            bestelling.save(update_fields=['log'])

            if ontvangen_euro >= bestelling.totaal_euro:
                self.stdout.write('[INFO] Bestelling %s (pk=%s) is afgerond' % (
                                    bestelling.mh_bestel_nr(), bestelling.pk))
                bestelling.status = BESTELLING_STATUS_AFGEROND

                msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % when_str
                bestelling.log += msg
                bestelling.save(update_fields=['log'])

                bevat_webwinkel = False
                for product in bestelling.producten.all():
                    if product.wedstrijd_inschrijving:
                        wedstrijden_plugin_inschrijving_is_betaald(product)
                    elif product.webwinkel_keuze:
                        bevat_webwinkel = True
                # for

                # stuur een e-mail aan de koper
                stuur_email_naar_koper_betaalbevestiging(bestelling)

                # stuur een e-mail naar het backoffice
                if bevat_webwinkel:
                    stuur_email_webwinkel_backoffice(bestelling, self._emailadres_backoffice)
        else:
            self.stdout.write('[INFO] Betaling niet gelukt voor bestelling %s (pk=%s)' % (
                                bestelling.mh_bestel_nr(), bestelling.pk))

            bestelling.status = BESTELLING_STATUS_MISLUKT

            msg = "\n[%s] Betaling is niet gelukt" % when_str
            bestelling.log += msg
            bestelling.save(update_fields=['log'])

        bestelling.betaal_actief = None
        bestelling.save(update_fields=['betaal_actief', 'status'])

    def _verwerk_mutatie_overboeking_ontvangen(self, mutatie):
        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        bestelling = mutatie.bestelling
        bedrag_euro = mutatie.bedrag_euro

        self.stdout.write('[INFO] Overboeking %s euro ontvangen voor bestelling %s (pk=%s)' % (bedrag_euro,
                                                                                               bestelling.mh_bestel_nr(),
                                                                                               bestelling.pk))

        status = bestelling.status
        if status == BESTELLING_STATUS_AFGEROND:
            self.stdout.write('[WARNING] Bestelling %s (pk=%s) is al afgerond (status=%s)' % (
                                bestelling.mh_bestel_nr(), bestelling.pk, BESTELLING_STATUS2STR[bestelling.status]))
            return

        self.stdout.write('[INFO] Betaling is gelukt voor bestelling %s (pk=%s)' % (
                            bestelling.mh_bestel_nr(), bestelling.pk))

        # koppel een transactie aan de bestelling
        # bestaande_pks = list(bestelling.transacties.all().values_list('pk', flat=True))
        transactie = BetaalTransactie(
                            when=timezone.now(),
                            is_handmatig=True,
                            beschrijving='Overboeking ontvangen',
                            is_restitutie=False,
                            bedrag_euro_klant=bedrag_euro,
                            bedrag_euro_boeking=bedrag_euro,
                            payment_id='',
                            klant_naam='',
                            klant_account='')
        transactie.save()
        bestelling.transacties.add(transactie)

        msg = "\n[%s] Bestelling heeft een overboeking van %s euro ontvangen" % (
                    when_str, bedrag_euro)
        bestelling.log += msg

        # controleer of we voldoende ontvangen hebben
        ontvangen_euro = Decimal('0')
        for transactie in bestelling.transacties.all():
            if transactie.is_restitutie:
                ontvangen_euro -= transactie.bedrag_euro_klant
            else:
                ontvangen_euro += transactie.bedrag_euro_klant
        # for

        self.stdout.write('[INFO] Bestelling %s (pk=%s) heeft %s van de %s euro ontvangen' % (
                            bestelling.mh_bestel_nr(), bestelling.pk, ontvangen_euro, bestelling.totaal_euro))

        msg = "\n[%s] Bestelling heeft %s van de %s euro ontvangen" % (
                    when_str, ontvangen_euro, bestelling.totaal_euro)
        bestelling.log += msg

        bestelling.save(update_fields=['log'])

        if ontvangen_euro >= bestelling.totaal_euro:
            self.stdout.write('[INFO] Bestelling %s (pk=%s) is afgerond' % (
                                bestelling.mh_bestel_nr(), bestelling.pk))
            bestelling.status = BESTELLING_STATUS_AFGEROND

            msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % when_str
            bestelling.log += msg

            bestelling.save(update_fields=['status', 'log'])

            bevat_webwinkel = False
            for product in bestelling.producten.all():
                if product.wedstrijd_inschrijving:
                    wedstrijden_plugin_inschrijving_is_betaald(product)
                elif product.webwinkel_keuze:
                    bevat_webwinkel = True
            # for

            # stuur een e-mail naar het backoffice
            if bevat_webwinkel:
                stuur_email_webwinkel_backoffice(bestelling, self._emailadres_backoffice)

            # stuur een e-mail aan de koper
            stuur_email_naar_koper_betaalbevestiging(bestelling)

    def _verwerk_mutatie_annuleer_bestelling(self, mutatie):
        """ Annulering van een bestelling + verwijderen van de reserveringen + bevestig via e-mail """

        bestelling = mutatie.bestelling

        status = bestelling.status
        if status not in (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_WACHT_OP_BETALING):
            self.stdout.write('[WARNING] Kan bestelling %s (pk=%s) niet annuleren, want status = %s' % (
                                bestelling.mh_bestel_nr(), bestelling.pk, BESTELLING_STATUS2STR[bestelling.status]))
            return

        self.stdout.write('[INFO] Bestelling %s (pk=%s) wordt nu geannuleerd' % (bestelling.bestel_nr, bestelling.pk))

        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        bestelling.status = BESTELLING_STATUS_GEANNULEERD
        bestelling.log += '\n[%s] Bestelling is geannuleerd' % when_str
        bestelling.save(update_fields=['status', 'log'])

        # stuur een e-mail om de annulering te bevestigen
        stuur_email_naar_koper_bestelling_details(bestelling)

        # verwijder de reserveringen

        # wedstrijden
        for product in (bestelling
                        .producten
                        .exclude(wedstrijd_inschrijving=None)
                        .select_related('wedstrijd_inschrijving',
                                        'wedstrijd_inschrijving__koper',
                                        'wedstrijd_inschrijving__sessie')
                        .all()):

            inschrijving = product.wedstrijd_inschrijving

            self.stdout.write('[INFO] Annuleer: BestelProduct pk=%s inschrijving (%s) in mandje van %s' % (
                                product.pk, inschrijving, inschrijving.koper))

            wedstrijden_plugin_verwijder_reservering(self.stdout, inschrijving)
        # for

        # webwinkel
        for product in (bestelling
                        .producten
                        .exclude(webwinkel_keuze=None)
                        .select_related('webwinkel_keuze')
                        .all()):

            keuze = product.webwinkel_keuze

            self.stdout.write('[INFO] Annuleer: BestelProduct pk=%s webwinkel (%s) in mandje van %s' % (
                                product.pk, keuze.product, keuze.koper))

            webwinkel_plugin_verwijder_reservering(self.stdout, keuze)
        # for

    def _verwerk_mutatie_transport(self, mutatie):
        """ Wijzig keuze voor transport tussen ophalen en verzender; alleen voor webwinkel aankopen """

        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch

            transport_oud = mandje.transport

            mandje.transport = mutatie.transport
            mandje.save(update_fields=['transport'])

            webwinkel_plugin_bepaal_verzendkosten_mandje(self.stdout, mandje)

            # bereken het totaal opnieuw
            self._mandje_bepaal_btw(mandje)
            mandje.bepaal_totaalprijs_opnieuw()

            transport_nieuw = mandje.transport

            self.stdout.write('[INFO] Transport: %s --> %s' % (BESTEL_TRANSPORT2STR[transport_oud],
                                                               BESTEL_TRANSPORT2STR[transport_nieuw]))
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.code

        if code == BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_wedstrijd_inschrijven(mutatie)

        elif code == BESTEL_MUTATIE_WEBWINKEL_KEUZE:
            self.stdout.write('[INFO] Verwerk mutatie %s: webwinkel keuze' % mutatie.pk)
            self._verwerk_mutatie_webwinkel_keuze(mutatie)

        elif code == BESTEL_MUTATIE_VERWIJDER:
            self.stdout.write('[INFO] Verwerk mutatie %s: verwijder product uit mandje' % mutatie.pk)
            self._verwerk_mutatie_verwijder(mutatie)

        elif code == BESTEL_MUTATIE_MAAK_BESTELLINGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: mandje omzetten in bestelling(en)' % mutatie.pk)
            self._verwerk_mutatie_maak_bestellingen(mutatie)

        elif code == BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_wedstrijd_afmelden(mutatie)

        elif code == BESTEL_MUTATIE_BETALING_AFGEROND:
            self.stdout.write('[INFO] Verwerk mutatie %s: betaling afgerond' % mutatie.pk)
            self._verwerk_mutatie_betaling_afgerond(mutatie)

        elif code == BESTEL_MUTATIE_OVERBOEKING_ONTVANGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: overboeking ontvangen' % mutatie.pk)
            self._verwerk_mutatie_overboeking_ontvangen(mutatie)

        elif code == BESTEL_MUTATIE_RESTITUTIE_UITBETAALD:
            self.stdout.write('[INFO] Verwerk mutatie %s: restitutie uitbetaald' % mutatie.pk)
            self._verwerk_mutatie_restitutie_uitbetaald(mutatie)

        elif code == BESTEL_MUTATIE_ANNULEER:
            self.stdout.write('[INFO] Verwerk mutatie %s: annuleer bestelling' % mutatie.pk)
            self._verwerk_mutatie_annuleer_bestelling(mutatie)

        elif code == BESTEL_MUTATIE_TRANSPORT:
            self.stdout.write('[INFO] Verwerk mutatie %s: wijzig transport' % mutatie.pk)
            self._verwerk_mutatie_transport(mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = BestelMutatie.objects.latest('pk')     # foutafhandeling in handle()

        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste BestelMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (BestelMutatie
                    .objects
                    .exclude(is_verwerkt=True)
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (BestelMutatie
                    .objects
                    .exclude(is_verwerkt=True))             # deferred

        # sorteren zodat ze in de juiste volgorde afgehandeld worden
        mutatie_pks = qset.order_by('pk').values_list('pk', flat=True)     # deferred

        self._hoogste_mutatie_pk = mutatie_latest.pk

        did_useful_work = False
        for pk in mutatie_pks:
            # we halen de records hier 1 voor 1 op
            # zodat we verse informatie hebben inclusief de vorige mutatie
            # en zodat we 1 plek hebben voor select/prefetch
            mutatie = (BestelMutatie
                       .objects
                       .select_related('account',
                                       'wedstrijd_inschrijving',
                                       'product',
                                       'bestelling')
                       .get(pk=pk))

            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste BestelMutatie pk is %s' % self._hoogste_mutatie_pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = BestelMutatie.objects.count()
            if new_count != mutatie_count:
                mutatie_count = new_count
                self._verwerk_nieuwe_mutaties()
                now = datetime.datetime.now()

            # wacht 5 seconden voordat we opnieuw in de database kijken
            # het wachten kan onderbroken worden door een ping, als er een nieuwe mutatie toegevoegd is
            secs = (self.stop_at - now).total_seconds()
            if secs > 1:                                    # pragma: no branch
                timeout = min(5.0, secs)
                if self._sync.wait_for_ping(timeout):       # pragma: no branch
                    self._count_ping += 1                   # pragma: no cover
            else:
                # near the end
                break       # from the while                # pragma: no cover

            now = datetime.datetime.now()
        # while

    def _set_stop_time(self, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        # trek er nog eens 15 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']

        self.stop_at = (datetime.datetime.now()
                        + datetime.timedelta(minutes=duration)
                        - datetime.timedelta(seconds=15))

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

        if options['fake_hoogste']:
            self._hoogste_mutatie_pk = -1

    def handle(self, *args, **options):

        self._set_stop_time(**options)

        # vang generieke fouten af
        try:
            self._mandjes_opschonen()
            self._monitor_nieuwe_mutaties()
        except (DataError, OperationalError, IntegrityError) as exc:  # pragma: no cover
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))
        except KeyboardInterrupt:                       # pragma: no cover
            pass

        self.stdout.write('[DEBUG] Aantal pings ontvangen: %s' % self._count_ping)

        self.stdout.write('Klaar')


"""
    performance debug helper:

    from django.db import connection

        q_begin = len(connection.queries)

        # queries here

        print('queries: %s' % (len(connection.queries) - q_begin))
        for obj in connection.queries[q_begin:]:
            print('%10s %s' % (obj['time'], obj['sql'][:200]))
        # for
        sys.exit(1)

    test uitvoeren met --debug-mode anders wordt er niets bijgehouden
"""

# end of file
