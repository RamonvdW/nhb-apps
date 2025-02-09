# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BestellingMutatie
"""

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError, IntegrityError
from django.db.models import Count
from django.db import transaction
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_STATUS2STR, BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK,
                                   BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN, BESTELLING_MUTATIE_WEBWINKEL_KEUZE,
                                   BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN, BESTELLING_MUTATIE_VERWIJDER,
                                   BESTELLING_MUTATIE_MAAK_BESTELLINGEN, BESTELLING_MUTATIE_BETALING_AFGEROND,
                                   BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN, BESTELLING_MUTATIE_RESTITUTIE_UITBETAALD,
                                   BESTELLING_MUTATIE_ANNULEER, BESTELLING_MUTATIE_TRANSPORT,
                                   BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN, BESTELLING_MUTATIE_EVENEMENT_AFMELDEN,
                                   BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN, BESTELLING_MUTATIE_OPLEIDING_AFMELDEN,
                                   BESTELLING_TRANSPORT_OPHALEN, BESTELLING_TRANSPORT2STR)
from Bestelling.models import (BestellingProduct, BestellingMandje, Bestelling, BestellingHoogsteBestelNr, 
                               BestellingMutatie)
from Bestelling.plugins.evenement import (evenement_plugin_inschrijven, evenement_plugin_verwijder_reservering,
                                          evenement_plugin_inschrijving_is_betaald, evenement_plugin_afmelden)
from Bestelling.plugins.opleiding import (opleiding_plugin_inschrijven, opleiding_plugin_inschrijving_is_betaald,
                                          opleiding_plugin_verwijder_reservering, opleiding_plugin_afmelden)
from Bestelling.plugins.product_info import beschrijf_product, beschrijf_korting
from Bestelling.plugins.wedstrijden import (wedstrijden_plugin_automatische_kortingen_toepassen,
                                            wedstrijden_plugin_inschrijven, wedstrijden_plugin_verwijder_reservering,
                                            wedstrijden_plugin_afmelden, wedstrijden_plugin_inschrijving_is_betaald)
from Bestelling.plugins.webwinkel import (webwinkel_plugin_reserveren, webwinkel_plugin_verwijder_reservering,
                                          webwinkel_plugin_bepaal_kortingen,
                                          webwinkel_plugin_bepaal_verzendkosten_mandje,
                                          webwinkel_plugin_bepaal_verzendkosten_bestelling)
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE, TRANSACTIE_TYPE_HANDMATIG
from Betaal.format import format_bedrag_euro
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Betaal.operations import maak_transactie_handmatige_overboeking
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF, EVENEMENT_STATUS_TO_STR,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_BESTELD)
from Functie.models import Functie
from Mailer.operations import mailer_queue_email, render_email_template, mailer_notify_internal_error
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_BESTELD,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  OPLEIDING_STATUS_TO_STR, OPLEIDING_INSCHRIJVING_STATUS_TO_STR)
from Overig.background_sync import BackgroundSync
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_KORTING_COMBI, WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR)
from mollie.api.client import Client, RequestSetupError
from types import SimpleNamespace
from decimal import Decimal
import traceback
import datetime
import sys

EMAIL_TEMPLATE_BACKOFFICE_VERSTUREN = 'email_bestelling/backoffice-versturen.dtl'
EMAIL_TEMPLATE_BEVESTIG_BESTELLING = 'email_bestelling/bevestig-bestelling.dtl'
EMAIL_TEMPLATE_BEVESTIG_BETALING = 'email_bestelling/bevestig-betaling.dtl'


def _beschrijf_bestelling(bestelling: Bestelling):
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
        product.prijs_euro_str = format_bedrag_euro(product.prijs_euro)
        product.korting_euro_str = format_bedrag_euro(product.korting_euro)     # positief bedrag

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

        verzendkosten_euro_str = format_bedrag_euro(bestelling.verzendkosten_euro)

        product = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=[("Verzendkosten", "")],       # TODO: specialiseren in pakket/briefpost
                        prijs_euro=verzendkosten_euro_str)
        producten.append(product)

    if bestelling.transport == BESTELLING_TRANSPORT_OPHALEN:

        # nieuwe regel op de bestelling
        regel_nr += 1

        verzendkosten_euro_str = format_bedrag_euro(Decimal(0))

        product = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=[("Ophalen op het bondsbureau", "")],
                        prijs_euro=verzendkosten_euro_str)
        producten.append(product)

    return producten


def bereken_som_betalingen(bestelling: Bestelling) -> Decimal:
    # TODO: dit gaat helemaal mis als een transactie meerdere keer in de database staat!!
    ontvangen_euro = Decimal('0')
    for transactie in bestelling.transacties.exclude(transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE):
        if transactie.transactie_type == TRANSACTIE_TYPE_HANDMATIG:
            ontvangen_euro += transactie.bedrag_handmatig
        else:
            ontvangen_euro += transactie.bedrag_beschikbaar     # restant na aftrek restitutie en terug geclaimd
    # for
    return ontvangen_euro


def _beschrijf_transacties(bestelling: Bestelling):
    transacties = (bestelling
                   .transacties
                   .all()
                   .order_by('when'))  # chronologisch

    for transactie in transacties:
        transactie.when_str = timezone.localtime(transactie.when).strftime('%Y-%m-%d om %H:%M')
        transactie.is_restitutie = (transactie.transactie_type == TRANSACTIE_TYPE_MOLLIE_RESTITUTIE)
    # for

    return transacties


def stuur_email_naar_koper_bestelling_details(bestelling: Bestelling):
    """ Stuur een e-mail naar de koper met details van de bestelling en betaalinstructies """

    account = bestelling.account

    producten = _beschrijf_bestelling(bestelling)

    totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

    heeft_afleveradres = False
    for nr in (1, 2, 3, 4, 5):
        regel = getattr(bestelling, 'afleveradres_regel_%s' % nr)
        if regel:
            heeft_afleveradres = True
    # for

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'producten': producten,
        'bestel_status': BESTELLING_STATUS2STR[bestelling.status],
        'kan_betalen': bestelling.status not in (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD),
        'heeft_afleveradres': heeft_afleveradres,
    }

    if bestelling.status == BESTELLING_STATUS_NIEUW:
        context['bestel_status'] = 'Te betalen'

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BESTELLING)

    mailer_queue_email(account.bevestigde_email,
                       'Bestelling op MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


def stuur_email_naar_koper_betaalbevestiging(bestelling: Bestelling):
    """ Stuur een e-mail om de betaalde bestelling te bevestigen """

    account = bestelling.account

    producten = _beschrijf_bestelling(bestelling)
    transacties = _beschrijf_transacties(bestelling)
    totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

    context = {
        'voornaam': account.get_first_name(),
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'producten': producten,
        'transacties': transacties,
        'wil_ophalen': bestelling.transport == BESTELLING_TRANSPORT_OPHALEN,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_BETALING)

    mailer_queue_email(account.bevestigde_email,
                       'Bevestiging aankoop via MijnHandboogsport (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


def stuur_email_webwinkel_backoffice(bestelling: Bestelling, email_backoffice):
    """ Stuur een e-mail om de betaalde bestelling te bevestigen """

    account = bestelling.account
    sporter = account.sporter_set.first()

    producten = _beschrijf_bestelling(bestelling)
    transacties = _beschrijf_transacties(bestelling)

    totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)
    bestelling.btw_euro_cat1_str = format_bedrag_euro(bestelling.btw_euro_cat1)
    bestelling.btw_euro_cat2_str = format_bedrag_euro(bestelling.btw_euro_cat2)
    bestelling.btw_euro_cat3_str = format_bedrag_euro(bestelling.btw_euro_cat3)

    context = {
        'koper_sporter': sporter,       # bevat postadres
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'producten': producten,
        'transacties': transacties,
        'waarschuw_test_server': settings.IS_TEST_SERVER,
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

        ophalen_ver = Vereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)
        self._adres_backoffice = (ophalen_ver.adres_regel1, ophalen_ver.adres_regel2)

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices=(1, 2, 5, 7, 10, 15, 20, 30, 45, 60),
                            help="Maximum aantal minuten actief blijven")
        parser.add_argument('--stop_exactly', type=int, default=None, choices=range(60),
                            help="Stop op deze minuut")
        parser.add_argument('--quick', action='store_true')             # for testing

    def _get_mandje(self, mutatie):
        account = mutatie.account
        if not account:
            self.stderr.write('[ERROR] Mutatie pk=%s met code=%s heeft geen account' % (mutatie.pk, mutatie.code))
            mandje = None
        else:
            # let op: geen prefetch_related('producten') gebruiken i.v.m. mutaties
            mandje, is_created = BestellingMandje.objects.get_or_create(account=account)

        return mandje

    def _mandjes_opschonen(self):
        """ Verwijder uit de mandjes de producten die er te lang in liggen """
        self.stdout.write('[INFO] Opschonen mandjes begin')

        verval_datum = timezone.now() - datetime.timedelta(days=settings.MANDJE_VERVAL_NA_DAGEN)

        # doorloop alle producten die nog in een mandje liggen en waarvan de datum verlopen is

        mandje_pks = list()

        # wedstrijden
        for product in (BestellingProduct
                        .objects
                        .annotate(mandje_count=Count('bestellingmandje'))
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

            mandje = product.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestelProduct met pk=%s wordt verwijderd' % product.pk)
            product.delete()
        # for

        # evenementen
        for product in (BestellingProduct
                        .objects
                        .annotate(mandje_count=Count('bestellingmandje'))
                        .exclude(evenement_inschrijving=None)
                        .select_related('evenement_inschrijving',
                                        'evenement_inschrijving__koper')
                        .filter(mandje_count=1,         # product ligt nog in een mandje
                                evenement_inschrijving__wanneer__lt=verval_datum)):

            inschrijving = product.evenement_inschrijving

            self.stdout.write('[INFO] Vervallen: BestelProduct pk=%s inschrijving (%s) in mandje van %s' % (
                                product.pk, inschrijving, inschrijving.koper))

            evenement_plugin_verwijder_reservering(self.stdout, inschrijving)

            mandje = product.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestelProduct met pk=%s wordt verwijderd' % product.pk)
            product.delete()
        # for

        # webwinkel
        for product in (BestellingProduct
                        .objects
                        .annotate(mandje_count=Count('bestellingmandje'))
                        .exclude(webwinkel_keuze=None)
                        .select_related('webwinkel_keuze')
                        .filter(mandje_count=1,         # product ligt nog in een mandje
                                webwinkel_keuze__wanneer__lt=verval_datum)):

            keuze = product.webwinkel_keuze

            self.stdout.write('[INFO] Vervallen: BestelProduct pk=%s webwinkel (%s) in mandje van %s' % (
                                product.pk, keuze.product, keuze.koper))

            # geef de reservering op de producten weer vrij
            webwinkel_plugin_verwijder_reservering(self.stdout, keuze)

            mandje = product.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:         # pragma: no branch
                mandje_pks.append(mandje.pk)

            # verwijder de webwinkel keuze
            self.stdout.write('[INFO] WebwinkelKeuze met pk=%s wordt verwijderd' % keuze.pk)
            keuze.product = None
            keuze.delete()

            # verwijder het bestel product
            self.stdout.write('[INFO] BestelProduct met pk=%s wordt verwijderd' % product.pk)
            product.delete()
        # for

        # opleidingen
        for product in (BestellingProduct
                        .objects
                        .annotate(mandje_count=Count('bestellingmandje'))
                        .exclude(opleiding_inschrijving=None)
                        .select_related('opleiding_inschrijving')
                        .filter(mandje_count=1,         # product ligt nog in een mandje
                                opleiding_inschrijving__wanneer_aangemeld__lt=verval_datum)):

            inschrijving = product.opleiding_inschrijving

            # laat mutatie verwerken
            # deze verwijdert ook het OpleidingInschrijving record
            opleiding_plugin_verwijder_reservering(self.stdout, inschrijving)

            mandje = product.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:             # pragma: no branch
                mandje_pks.append(mandje.pk)

            # verwijder het bestel product
            self.stdout.write('[INFO] BestelProduct met pk=%s wordt verwijderd' % product.pk)
            product.delete()
        # for

        # mandjes bijwerken
        for mandje in BestellingMandje.objects.filter(pk__in=mandje_pks):
            wedstrijden_plugin_automatische_kortingen_toepassen(self.stdout, mandje)
            webwinkel_plugin_bepaal_kortingen(self.stdout, mandje)
            webwinkel_plugin_bepaal_verzendkosten_mandje(self.stdout, mandje)
        # for

        self.stdout.write('[INFO] Opschonen mandjes klaar')

    def _clear_instellingen_cache(self):
        self._instellingen_cache = dict()

        ver_bond = Vereniging.objects.get(ver_nr=settings.BETAAL_VIA_BOND_VER_NR)

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
            hoogste = (BestellingHoogsteBestelNr
                       .objects
                       .select_for_update()                         # lock tegen concurrency
                       .get(pk=BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK))

            # het volgende nummer is het nieuwe unieke nummer
            hoogste.hoogste_gebruikte_bestel_nr += 1
            hoogste.save()

            nummer = hoogste.hoogste_gebruikte_bestel_nr

        return nummer

    @staticmethod
    def _mandje_bepaal_btw(mandje):
        """ bereken de btw voor de producten in het mandje """

        # begin met een schone lei
        mandje.btw_percentage_cat1 = ""
        mandje.btw_euro_cat1 = Decimal(0)

        mandje.btw_percentage_cat2 = ""
        mandje.btw_euro_cat2 = Decimal(0)

        mandje.btw_percentage_cat3 = ""
        mandje.btw_euro_cat3 = Decimal(0)

        # kijk hoeveel euro aan webwinkelproducten in het mandje liggen
        totaal_euro = Decimal(0)
        for product in mandje.producten.exclude(webwinkel_keuze=None):
            totaal_euro += product.prijs_euro
            totaal_euro -= product.korting_euro
        # for

        totaal_euro += mandje.verzendkosten_euro

        if totaal_euro > 0:
            # converteer percentage (21,0) naar string "21.0%"
            btw_str = "%.2f" % settings.WEBWINKEL_BTW_PERCENTAGE
            while btw_str[-1] == '0':
                btw_str = btw_str[:-1]      # 21,10 --> 21,1 / 21,00 --> 21,
            btw_str = btw_str.replace('.', ',')       # localize
            if btw_str[-1] == ",":
                btw_str = btw_str[:-1]      # drop the trailing dot/comma
            mandje.btw_percentage_cat1 = btw_str

            # het totaalbedrag is inclusief BTW, dus 100% + BTW% (was: 121%)
            # reken uit hoeveel daarvan de BTW is
            btw_deel = Decimal(settings.WEBWINKEL_BTW_PERCENTAGE / (100 + settings.WEBWINKEL_BTW_PERCENTAGE))
            btw = totaal_euro * btw_deel
            btw = round(btw, 2)             # afronden op 2 decimalen
            mandje.btw_euro_cat1 = btw

        mandje.save(update_fields=['btw_percentage_cat1', 'btw_euro_cat1',
                                   'btw_percentage_cat2', 'btw_euro_cat2',
                                   'btw_percentage_cat3', 'btw_euro_cat3'])

    @staticmethod
    def _bestelling_bepaal_btw(bestelling: Bestelling):
        """ bereken de btw voor de producten in een bestelling """

        # begin met een schone lei
        bestelling.btw_percentage_cat1 = ""
        bestelling.btw_euro_cat1 = Decimal(0)

        bestelling.btw_percentage_cat2 = ""
        bestelling.btw_euro_cat2 = Decimal(0)

        bestelling.btw_percentage_cat3 = ""
        bestelling.btw_euro_cat3 = Decimal(0)

        # kijk hoeveel euro aan webwinkelproducten in deze bestelling zitten
        totaal_euro = Decimal(0)
        for product in bestelling.producten.exclude(webwinkel_keuze=None):
            totaal_euro += product.prijs_euro
            totaal_euro -= product.korting_euro
        # for

        totaal_euro += bestelling.verzendkosten_euro

        if totaal_euro > 0:
            # converteer percentage (21.1) naar string "21,1"
            btw_str = "%.2f" % settings.WEBWINKEL_BTW_PERCENTAGE
            while btw_str[-1] == '0':
                btw_str = btw_str[:-1]      # 21,10 --> 21,1 / 21,00 --> 21,
            btw_str = btw_str.replace('.', ',')       # localize
            if btw_str[-1] == ",":
                btw_str = btw_str[:-1]      # drop the trailing dot/comma
            bestelling.btw_percentage_cat1 = btw_str

            # het totaalbedrag is inclusief BTW, dus 100% + BTW% (was: 121%)
            # reken uit hoeveel daarvan de BTW is
            btw_deel = Decimal(settings.WEBWINKEL_BTW_PERCENTAGE / (100 + settings.WEBWINKEL_BTW_PERCENTAGE))
            btw = totaal_euro * btw_deel
            btw = round(btw, 2)             # afronden op 2 decimalen
            bestelling.btw_euro_cat1 = btw

        bestelling.save(update_fields=['btw_percentage_cat1', 'btw_euro_cat1',
                                       'btw_percentage_cat2', 'btw_euro_cat2',
                                       'btw_percentage_cat3', 'btw_euro_cat3'])

    def _verwerk_mutatie_wedstrijd_inschrijven(self, mutatie: BestellingMutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            prijs_euro = wedstrijden_plugin_inschrijven(mutatie.wedstrijd_inschrijving)

            # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
            if mutatie.wedstrijd_inschrijving.status != WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
                # maak een product regel aan voor de bestelling
                product = BestellingProduct(
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

    def _verwerk_mutatie_evenement_inschrijven(self, mutatie: BestellingMutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            inschrijving = mutatie.evenement_inschrijving
            inschrijving.nummer = inschrijving.pk
            inschrijving.save(update_fields=['nummer'])

            prijs_euro = evenement_plugin_inschrijven(mutatie.evenement_inschrijving)

            # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
            if mutatie.evenement_inschrijving.status != EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
                # maak een product regel aan voor de bestelling
                product = BestellingProduct(
                                evenement_inschrijving=mutatie.evenement_inschrijving,
                                prijs_euro=prijs_euro)
                product.save()

                # leg het product in het mandje
                mandje.producten.add(product)

                # bereken het totaal opnieuw
                self._mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_webwinkel_keuze(self, mutatie: BestellingMutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            webwinkel_keuze = mutatie.webwinkel_keuze

            prijs_euro = webwinkel_plugin_reserveren(webwinkel_keuze)

            # maak een product regel aan voor de bestelling
            product = BestellingProduct(
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

            self.stdout.write('[INFO] Transport: %s --> %s' % (BESTELLING_TRANSPORT2STR[transport_oud],
                                                               BESTELLING_TRANSPORT2STR[transport_nieuw]))
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_opleiding_inschrijven(self, mutatie: BestellingMutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            inschrijving = mutatie.opleiding_inschrijving

            inschrijving.nummer = inschrijving.pk
            inschrijving.save(update_fields=['nummer'])

            prijs_euro = opleiding_plugin_inschrijven(inschrijving)

            self.stdout.write('[DEBUG] Opleiding inschrijving status = %s (%s)' % (
                                inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))

            # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
            if inschrijving.status != OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF:
                # maak een product regel aan voor de bestelling
                product = BestellingProduct(
                                opleiding_inschrijving=inschrijving,
                                prijs_euro=prijs_euro)
                product.save()

                # leg het product in het mandje
                mandje.producten.add(product)

                stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
                msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, mandje.account.get_account_full_name())
                inschrijving.log += msg
                inschrijving.status = OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE
                inschrijving.save(update_fields=['log', 'status'])

                # bereken het totaal opnieuw
                self._mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_verwijder_uit_mandje(self, mutatie: BestellingMutatie):
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

                elif product.evenement_inschrijving:
                    mandje.producten.remove(product)

                    inschrijving = product.evenement_inschrijving

                    mutatie.evenement_inschrijving = None
                    mutatie.product = None
                    mutatie.save()

                    evenement_plugin_verwijder_reservering(self.stdout, inschrijving)

                    # verwijder het product, dan verdwijnt deze ook uit het mandje
                    product.delete()

                    handled = True

                elif product.opleiding_inschrijving:
                    mandje.producten.remove(product)
                    inschrijving = product.opleiding_inschrijving

                    mutatie.opleiding_inschrijving = None
                    mutatie.product = None
                    mutatie.save()

                    opleiding_plugin_verwijder_reservering(self.stdout, inschrijving)

                    # verwijder het product, dan verdwijnt deze ook uit het mandje
                    product.delete()

                    handled = True

                elif product.webwinkel_keuze:

                    transport_oud = mandje.transport

                    mandje.producten.remove(product)

                    webwinkel_keuze = product.webwinkel_keuze

                    webwinkel_plugin_verwijder_reservering(self.stdout, webwinkel_keuze)

                    mutatie.webwinkel_keuze = None
                    mutatie.product = None
                    mutatie.save()

                    # verwijder het product, dan verdwijnt deze ook uit het mandje
                    product.delete()

                    webwinkel_plugin_bepaal_kortingen(self.stdout, mandje)

                    webwinkel_plugin_bepaal_verzendkosten_mandje(self.stdout, mandje)

                    transport_nieuw = mandje.transport

                    self.stdout.write('[INFO] Transport: %s --> %s' % (BESTELLING_TRANSPORT2STR[transport_oud],
                                                                       BESTELLING_TRANSPORT2STR[transport_nieuw]))

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

    def _verwerk_mutatie_maak_bestellingen(self, mutatie: BestellingMutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            # zorg dat we verse informatie ophalen (anders duur het 1 uur voordat een update door komt)
            self._clear_instellingen_cache()

            # maak een Mollie-client instantie aan
            mollie_client = Client(api_endpoint=settings.BETAAL_API_URL)

            # verdeel de producten in het mandje naar vereniging waar de betaling heen moet
            ontvanger2producten = dict()      # [ver_nr] = [MandjeProduct, ...]
            for product in (mandje
                            .producten
                            .select_related('wedstrijd_inschrijving',
                                            'wedstrijd_inschrijving__wedstrijd',
                                            'wedstrijd_inschrijving__wedstrijd__organiserende_vereniging',
                                            'evenement_inschrijving',
                                            'evenement_inschrijving__evenement',
                                            'evenement_inschrijving__evenement__organiserende_vereniging',
                                            'opleiding_inschrijving',
                                            'opleiding_inschrijving__opleiding',
                                            'opleiding_inschrijving__sporter',
                                            'webwinkel_keuze')
                            .order_by('wedstrijd_inschrijving__pk',
                                      'webwinkel_keuze__pk')):

                if product.wedstrijd_inschrijving:
                    # wedstrijd van de kalender
                    instellingen = self._get_instellingen(product
                                                          .wedstrijd_inschrijving
                                                          .wedstrijd
                                                          .organiserende_vereniging)
                    ontvanger_ver_nr = instellingen.vereniging.ver_nr       # kan nu ook "via KHSN" zijn
                    try:
                        ontvanger2producten[ontvanger_ver_nr].append(product)
                    except KeyError:
                        ontvanger2producten[ontvanger_ver_nr] = [product]

                elif product.evenement_inschrijving:
                    # evenement van de kalender
                    instellingen = self._get_instellingen(product
                                                          .evenement_inschrijving
                                                          .evenement
                                                          .organiserende_vereniging)
                    ontvanger_ver_nr = instellingen.vereniging.ver_nr       # kan nu ook "via KHSN" zijn
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

                elif product.opleiding_inschrijving:
                    # opleiding
                    # TODO: organiserende_vereniging toevoegen aan elke opleiding
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
                                    verkoper_bic=ver.bank_bic,
                                    afleveradres_regel_1=mandje.afleveradres_regel_1,
                                    afleveradres_regel_2=mandje.afleveradres_regel_2,
                                    afleveradres_regel_3=mandje.afleveradres_regel_3,
                                    afleveradres_regel_4=mandje.afleveradres_regel_4,
                                    afleveradres_regel_5=mandje.afleveradres_regel_5)

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

                totaal_euro += bestelling.verzendkosten_euro

                self._bestelling_bepaal_btw(bestelling)

                # toon het BTW-nummer alleen als het relevant is
                if ver_nr == settings.WEBWINKEL_VERKOPER_VER_NR:
                    if (bestelling.btw_percentage_cat1
                            or bestelling.btw_percentage_cat2
                            or bestelling.btw_percentage_cat3):
                        bestelling.verkoper_btw_nr = settings.WEBWINKEL_VERKOPER_BTW_NR

                bestelling.totaal_euro = totaal_euro
                bestelling.save(update_fields=['totaal_euro', 'verkoper_btw_nr'])

                totaal_euro_str = format_bedrag_euro(totaal_euro)

                when_str = timezone.localtime(bestelling.aangemaakt).strftime('%Y-%m-%d om %H:%M')

                msg = "[%s] Bestelling aangemaakt met %s producten voor totaal %s" % (
                                                when_str, len(producten), totaal_euro_str)
                bestelling.log = msg
                bestelling.save(update_fields=['log'])

                nieuwe_bestellingen.append(bestelling)

                # haal deze producten uit het mandje
                mandje.producten.remove(*producten)

                # pas de status aan van inschrijvingen voor wedstrijden en evenementen
                for product in producten:
                    if product.wedstrijd_inschrijving:
                        inschrijving = product.wedstrijd_inschrijving
                        inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD
                        inschrijving.save(update_fields=['status'])
                    if product.evenement_inschrijving:
                        inschrijving = product.evenement_inschrijving
                        inschrijving.status = EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_BESTELD
                        inschrijving.save(update_fields=['status'])
                    if product.opleiding_inschrijving:
                        inschrijving = product.opleiding_inschrijving
                        inschrijving.status = OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_BESTELD
                        inschrijving.save(update_fields=['status'])
                # for

                totaal_euro_str = format_bedrag_euro(totaal_euro)

                self.stdout.write(
                    "[INFO] %s producten voor totaal %s uit mandje account pk=%s (%s) omgezet in bestelling pk=%s" % (
                        len(producten), totaal_euro_str, mutatie.account.pk, mutatie.account.volledige_naam(),
                        bestelling.pk))
            # for

            # kijk welke bestellingen een nul-bedrag hebben en daarom meteen afgerond kunnen worden
            for bestelling in nieuwe_bestellingen:
                if bestelling.totaal_euro < Decimal('0.001'):
                    self.stdout.write('[INFO] Bestelling pk=%s wordt meteen afgerond' % bestelling.pk)
                    # TODO: ondersteuning voor gratis producten in de webwinkel
                    for product in bestelling.producten.all():
                        if product.wedstrijd_inschrijving:
                            wedstrijden_plugin_inschrijving_is_betaald(self.stdout, product)
                        elif product.evenement_inschrijving:
                            evenement_plugin_inschrijving_is_betaald(self.stdout, product)
                        elif product.opleiding_inschrijving:
                            opleiding_plugin_inschrijving_is_betaald(self.stdout, product)
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

    def _verwerk_mutatie_wedstrijd_afmelden(self, mutatie: BestellingMutatie):
        inschrijving = mutatie.wedstrijd_inschrijving
        oude_status = inschrijving.status
        if not inschrijving:
            return

        # WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD --> doe niets
        # WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTELLING_MUTATIE_VERWIJDER
        if oude_status == WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD:
            # in een bestelling; nog niet (volledig) betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor wedstrijd' %
                              inschrijving.pk)

            wedstrijden_plugin_verwijder_reservering(self.stdout, inschrijving)
            # FUTURE: betaling afbreken
            # FUTURE: automatische restitutie als de betaling binnen is

        elif oude_status == WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
            # in een bestelling en betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor wedstrijd' %
                              inschrijving.pk)

            wedstrijden_plugin_afmelden(inschrijving)
            # FUTURE: automatisch een restitutie beginnen
        else:
            self.stdout.write('[WARNING] Niet ondersteund: Inschrijving pk=%s met status=%s afmelden voor wedstrijd' % (
                inschrijving.pk, WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))

    def _verwerk_mutatie_evenement_afmelden(self, mutatie):
        inschrijving = mutatie.evenement_inschrijving
        if not inschrijving:
            return

        # EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTELLING_MUTATIE_VERWIJDER
        if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_BESTELD:
            # in een bestelling; nog niet (volledig) betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor evenement' %
                              inschrijving.pk)

            mutatie.evenement_inschrijving = None
            mutatie.save(update_fields=['evenement_inschrijving'])

            evenement_plugin_verwijder_reservering(self.stdout, inschrijving)
            # FUTURE: betaling afbreken
            # FUTURE: automatische restitutie als de betaling binnen is

        elif inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
            # in een bestelling en betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor evenement' %
                              inschrijving.pk)

            mutatie.evenement_inschrijving = None
            mutatie.save(update_fields=['evenement_inschrijving'])

            evenement_plugin_afmelden(inschrijving)
            # FUTURE: automatisch een restitutie beginnen

        else:
            self.stdout.write('[WARNING] Niet ondersteund: Inschrijving pk=%s met status=%s afmelden voor evenement' % (
                        inschrijving.pk, EVENEMENT_STATUS_TO_STR[inschrijving.status]))

    def _verwerk_mutatie_opleiding_afmelden(self, mutatie):
        inschrijving = mutatie.opleiding_inschrijving
        if not inschrijving:
            return

        # OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTELLING_MUTATIE_VERWIJDER
        if inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_BESTELD:
            # in een bestelling; nog niet (volledig) betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor opleiding' %
                              inschrijving.pk)

            # verwijder referentie vanuit mutatie, zodat inschrijving verwijderd kan worden
            mutatie.opleiding_inschrijving = None
            mutatie.save(update_fields=['opleiding_inschrijving'])

            opleiding_plugin_verwijder_reservering(self.stdout, inschrijving)
            # FUTURE: betaling afbreken
            # FUTURE: automatische restitutie als de betaling binnen is

        elif inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF:
            # in een bestelling en betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor opleiding' %
                              inschrijving.pk)

            # verwijder referentie vanuit mutatie, zodat inschrijving verwijderd kan worden
            mutatie.opleiding_inschrijving = None
            mutatie.save(update_fields=['opleiding_inschrijving'])

            opleiding_plugin_afmelden(inschrijving)
            # FUTURE: automatisch een restitutie beginnen

        else:
            self.stdout.write('[WARNING] Niet ondersteund: Inschrijving pk=%s met status=%s afmelden voor opleiding' % (
                        inschrijving.pk, OPLEIDING_STATUS_TO_STR[inschrijving.status]))

    def _verwerk_mutatie_betaling_afgerond(self, mutatie: BestellingMutatie):
        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        bestelling = mutatie.bestelling
        is_gelukt = mutatie.betaling_is_gelukt

        status = bestelling.status
        if status != BESTELLING_STATUS_BETALING_ACTIEF:
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
            ontvangen_euro = bereken_som_betalingen(bestelling)

            ontvangen_euro_str = format_bedrag_euro(ontvangen_euro)
            totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

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
                        wedstrijden_plugin_inschrijving_is_betaald(self.stdout, product)
                    elif product.evenement_inschrijving:
                        evenement_plugin_inschrijving_is_betaald(self.stdout, product)
                    elif product.opleiding_inschrijving:
                        opleiding_plugin_inschrijving_is_betaald(self.stdout, product)
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

    def _verwerk_mutatie_overboeking_ontvangen(self, mutatie: BestellingMutatie):
        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        bestelling = mutatie.bestelling
        bedrag_euro = mutatie.bedrag_euro

        self.stdout.write('[INFO] Overboeking %s euro ontvangen voor bestelling %s (pk=%s)' % (
                            bedrag_euro, bestelling.mh_bestel_nr(), bestelling.pk))

        status = bestelling.status
        if status == BESTELLING_STATUS_AFGEROND:
            self.stdout.write('[WARNING] Bestelling %s (pk=%s) is al afgerond (status=%s)' % (
                                bestelling.mh_bestel_nr(), bestelling.pk, BESTELLING_STATUS2STR[bestelling.status]))
            return

        self.stdout.write('[INFO] Betaling is gelukt voor bestelling %s (pk=%s)' % (
                            bestelling.mh_bestel_nr(), bestelling.pk))

        # koppel een transactie aan de bestelling
        transactie = maak_transactie_handmatige_overboeking(bestelling.mh_bestel_nr(), bedrag_euro)
        bestelling.transacties.add(transactie)

        msg = "\n[%s] Bestelling heeft een overboeking van %s euro ontvangen" % (
                    when_str, bedrag_euro)
        bestelling.log += msg

        # controleer of we voldoende ontvangen hebben
        ontvangen_euro = bereken_som_betalingen(bestelling)

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
                    wedstrijden_plugin_inschrijving_is_betaald(self.stdout, product)
                elif product.evenement_inschrijving:
                    evenement_plugin_inschrijving_is_betaald(self.stdout, product)
                elif product.webwinkel_keuze:
                    bevat_webwinkel = True
            # for

            # stuur een e-mail naar het backoffice
            if bevat_webwinkel:
                stuur_email_webwinkel_backoffice(bestelling, self._emailadres_backoffice)

            # stuur een e-mail aan de koper
            stuur_email_naar_koper_betaalbevestiging(bestelling)

        else:
            bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
            bestelling.save(update_fields=['status'])

    def _verwerk_mutatie_annuleer_bestelling(self, mutatie: BestellingMutatie):
        """ Annulering van een bestelling + verwijderen van de reserveringen + bevestig via e-mail """

        bestelling = mutatie.bestelling

        status = bestelling.status
        if status not in (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF):
            self.stdout.write('[WARNING] Kan bestelling %s (pk=%s) niet annuleren, want status = %s' % (
                bestelling.mh_bestel_nr(), bestelling.pk,
                BESTELLING_STATUS2STR[bestelling.status]))
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

            self.stdout.write('[INFO] Annuleer bestelling: BestelProduct pk=%s inschrijving (%s) besteld door %s' % (
                product.pk, inschrijving, inschrijving.koper))

            wedstrijden_plugin_verwijder_reservering(self.stdout, inschrijving)
        # for

        # evenement
        for product in (bestelling
                        .producten
                        .exclude(evenement_inschrijving=None)
                        .select_related('evenement_inschrijving',
                                        'evenement_inschrijving__koper')
                        .all()):

            inschrijving = product.evenement_inschrijving

            self.stdout.write('[INFO] Annuleer bestelling: BestelProduct pk=%s inschrijving (%s) besteld door %s' % (
                                    product.pk, inschrijving, inschrijving.koper))

            afmelding = evenement_plugin_verwijder_reservering(self.stdout, inschrijving)

            product.evenement_inschrijving = None
            product.evenement_afgemeld = afmelding
            product.save(update_fields=['evenement_inschrijving', 'evenement_afgemeld'])
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

        # opleiding
        for product in (bestelling
                        .producten
                        .exclude(opleiding_inschrijving=None)
                        .select_related('opleiding_inschrijving',
                                        'opleiding_inschrijving__opleiding')
                        .all()):

            deelnemer = product.opleiding_inschrijving

            self.stdout.write('[INFO] Annuleer: BestelProduct pk=%s opleiding (%s) in mandje van %s' % (
                                product.pk, deelnemer.opleiding, deelnemer.koper))

            afmelding = opleiding_plugin_verwijder_reservering(self.stdout, deelnemer)

            product.opleiding_inschrijving = None
            product.opleiding_afgemeld = afmelding
            product.save(update_fields=['opleiding_inschrijving', 'opleiding_afgemeld'])
        # for

    def _verwerk_mutatie_transport(self, mutatie: BestellingMutatie):
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

            self.stdout.write('[INFO] Transport: %s --> %s' % (BESTELLING_TRANSPORT2STR[transport_oud],
                                                               BESTELLING_TRANSPORT2STR[transport_nieuw]))
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.code

        if code == BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_wedstrijd_inschrijven(mutatie)

        elif code == BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op evenement' % mutatie.pk)
            self._verwerk_mutatie_evenement_inschrijven(mutatie)

        elif code == BESTELLING_MUTATIE_WEBWINKEL_KEUZE:
            self.stdout.write('[INFO] Verwerk mutatie %s: webwinkel keuze' % mutatie.pk)
            self._verwerk_mutatie_webwinkel_keuze(mutatie)

        elif code == BESTELLING_MUTATIE_VERWIJDER:
            self.stdout.write('[INFO] Verwerk mutatie %s: verwijder product uit mandje' % mutatie.pk)
            self._verwerk_mutatie_verwijder_uit_mandje(mutatie)

        elif code == BESTELLING_MUTATIE_MAAK_BESTELLINGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: mandje omzetten in bestelling(en)' % mutatie.pk)
            self._verwerk_mutatie_maak_bestellingen(mutatie)

        elif code == BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_wedstrijd_afmelden(mutatie)

        elif code == BESTELLING_MUTATIE_EVENEMENT_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor evenement' % mutatie.pk)
            self._verwerk_mutatie_evenement_afmelden(mutatie)

        elif code == BESTELLING_MUTATIE_BETALING_AFGEROND:
            self.stdout.write('[INFO] Verwerk mutatie %s: betaling afgerond' % mutatie.pk)
            self._verwerk_mutatie_betaling_afgerond(mutatie)

        elif code == BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: overboeking ontvangen' % mutatie.pk)
            self._verwerk_mutatie_overboeking_ontvangen(mutatie)

        elif code == BESTELLING_MUTATIE_RESTITUTIE_UITBETAALD:
            self.stdout.write('[INFO] Verwerk mutatie %s: restitutie uitbetaald' % mutatie.pk)
            self._verwerk_mutatie_restitutie_uitbetaald(mutatie)

        elif code == BESTELLING_MUTATIE_ANNULEER:
            self.stdout.write('[INFO] Verwerk mutatie %s: annuleer bestelling' % mutatie.pk)
            self._verwerk_mutatie_annuleer_bestelling(mutatie)

        elif code == BESTELLING_MUTATIE_TRANSPORT:
            self.stdout.write('[INFO] Verwerk mutatie %s: wijzig transport' % mutatie.pk)
            self._verwerk_mutatie_transport(mutatie)

        elif code == BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op opleiding' % mutatie.pk)
            self._verwerk_mutatie_opleiding_inschrijven(mutatie)

        elif code == BESTELLING_MUTATIE_OPLEIDING_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor opleiding' % mutatie.pk)
            self._verwerk_mutatie_opleiding_afmelden(mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = BestellingMutatie.objects.latest('pk')     # foutafhandeling in handle()

        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk is not None:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste BestellingMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (BestellingMutatie
                    .objects
                    .exclude(is_verwerkt=True)
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (BestellingMutatie
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
            mutatie = (BestellingMutatie
                       .objects
                       .select_related('account',
                                       'wedstrijd_inschrijving',
                                       'evenement_inschrijving',
                                       'webwinkel_keuze',
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
            self.stdout.write('[INFO] nieuwe hoogste BestellingMutatie pk is %s' % self._hoogste_mutatie_pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = BestellingMutatie.objects.count()
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
        duration = options['duration']
        stop_minute = options['stop_exactly']

        now = datetime.datetime.now()
        self.stop_at = now + datetime.timedelta(minutes=duration)

        if isinstance(stop_minute, int):
            delta = stop_minute - now.minute
            if delta < 0:
                delta += 60
            if delta != 0:    # avoid stopping in start minute
                stop_at_exact = now + datetime.timedelta(minutes=delta)
                stop_at_exact -= datetime.timedelta(seconds=self.stop_at.second,
                                                    microseconds=self.stop_at.microsecond)
                self.stdout.write('[INFO] Calculated stop at is %s' % stop_at_exact)
                if stop_at_exact < self.stop_at:
                    # run duration passes the requested stop minute
                    self.stop_at = stop_at_exact

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            if options['duration'] == 60:
                # speciale testcase
                self._hoogste_mutatie_pk = 0
                duration = 2

            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

    def handle(self, *args, **options):

        self._set_stop_time(**options)

        # vang generieke fouten af
        try:
            self._mandjes_opschonen()
            self._monitor_nieuwe_mutaties()
        except (OperationalError, IntegrityError) as exc:  # pragma: no cover
            # OperationalError treed op bij system shutdown, als database gesloten wordt
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

        except KeyboardInterrupt:                       # pragma: no cover
            pass

        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Onverwachte fout tijdens bestel_mutaties\n'
            tb_msg_start += '\n'

            self.stderr.write('[ERROR] Onverwachte fout tijdens bestel_mutaties: ' + str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            mailer_notify_internal_error(tb_msg)

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

    test uitvoeren met DEBUG=True via --settings=Site.settings_dev anders wordt er niets bijgehouden
"""

# end of file
