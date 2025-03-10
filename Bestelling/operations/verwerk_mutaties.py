# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from Bestelling.definities import (BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN, BESTELLING_MUTATIE_WEBWINKEL_KEUZE,
                                   BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN, BESTELLING_MUTATIE_VERWIJDER,
                                   BESTELLING_MUTATIE_MAAK_BESTELLINGEN, BESTELLING_MUTATIE_BETALING_AFGEROND,
                                   BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN,
                                   BESTELLING_MUTATIE_ANNULEER, BESTELLING_MUTATIE_TRANSPORT,
                                   BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN, BESTELLING_MUTATIE_EVENEMENT_AFMELDEN,
                                   BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN, BESTELLING_MUTATIE_OPLEIDING_AFMELDEN,
                                   BESTELLING_TRANSPORT_NVT, BESTELLING_TRANSPORT_VERZEND)
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_STATUS2STR, BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK,
                                   BESTELLING_TRANSPORT_OPHALEN, BESTELLING_TRANSPORT2STR)
from Bestelling.models import (Bestelling, BestellingRegel, BestellingMandje,
                               BestellingHoogsteBestelNr, BestellingMutatie)
from Bestelling.operations.bepaal_kortingen import BepaalAutomatischeKorting
from Bestelling.plugins.alle_bestel_plugins import bestel_plugins
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE, TRANSACTIE_TYPE_HANDMATIG
from Betaal.format import format_bedrag_euro
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Betaal.operations import maak_transactie_handmatige_overboeking
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF, EVENEMENT_STATUS_TO_STR,
                                  EVENEMENT_INSCHRIJVING_STATUS_BESTELD)
from Functie.models import Functie
from Mailer.operations import mailer_queue_email, render_email_template
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                                  OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                                  OPLEIDING_STATUS_TO_STR)
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR)
from mollie.api.client import Client, RequestSetupError
from types import SimpleNamespace
from decimal import Decimal
import datetime
from Evenement.plugin_bestelling import evenement_bestel_plugin
from Opleiding.plugin_bestelling import opleiding_bestel_plugin
from Webwinkel.plugin_bestelling import webwinkel_bestel_plugin, transportkosten_bestel_plugin
from Wedstrijden.plugin_bestelling import wedstrijd_bestel_plugin

EMAIL_TEMPLATE_BACKOFFICE_VERSTUREN = 'email_bestelling/backoffice-versturen.dtl'
EMAIL_TEMPLATE_BEVESTIG_BESTELLING = 'email_bestelling/bevestig-bestelling.dtl'
EMAIL_TEMPLATE_BEVESTIG_BETALING = 'email_bestelling/bevestig-betaling.dtl'


class VerwerkBestelMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de Bestellingen applicatie.
        Wordt aangeroepen door de achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout):
        self.stdout = stdout
        for plugin in bestel_plugins.values():
            plugin.zet_stdout(stdout)
        # for

        self.bepaal_kortingen = BepaalAutomatischeKorting(stdout)

        self._instellingen_via_bond = None
        self._instellingen_cache = dict()  # [ver_nr] = BetaalInstellingenVereniging

        # geen bescherming: deze vereniging moet bestaan
        ophalen_ver = Vereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)
        self._adres_backoffice = (ophalen_ver.adres_regel1, ophalen_ver.adres_regel2)

        # geen bescherming: dit e-mailadres moet ingesteld zijn
        self._emailadres_backoffice = Functie.objects.get(rol='MWW').bevestigde_email

    def _clear_instellingen_cache(self):
        self._instellingen_cache = dict()

        ver_nr_bond = settings.BETAAL_VIA_BOND_VER_NR

        self._instellingen_via_bond, _ = (BetaalInstellingenVereniging
                                          .objects
                                          .select_related('vereniging')
                                          .get_or_create(vereniging__ver_nr=ver_nr_bond))

        self._instellingen_cache[ver_nr_bond] = self._instellingen_via_bond

    def _get_betaal_instellingen(self, ver_nr: int):
        try:
            instellingen = self._instellingen_cache[ver_nr]
        except KeyError:
            instellingen, _ = (BetaalInstellingenVereniging
                               .objects
                               .select_related('vereniging')
                               .get_or_create(vereniging__ver_nr=ver_nr))

            if instellingen.akkoord_via_bond:
                instellingen = self._instellingen_via_bond

            self._instellingen_cache[ver_nr] = instellingen

        return instellingen

    def _get_mandje(self, mutatie: BestellingMutatie):
        account = mutatie.account
        if not account:
            self.stdout.write('[ERROR] Mutatie pk=%s met code=%s heeft geen account' % (mutatie.pk, mutatie.code))
            mandje = None
        else:
            # let op: geen prefetch_related('producten') gebruiken i.v.m. mutaties
            mandje, is_created = BestellingMandje.objects.get_or_create(account=account)

        return mandje

    def mandjes_opschonen(self):
        """ Verwijder uit de mandjes de producten die er te lang in liggen """
        self.stdout.write('[INFO] Opschonen mandjes begint')

        verval_datum = timezone.now() - datetime.timedelta(days=settings.MANDJE_VERVAL_NA_DAGEN)

        # doorloop alle producten die nog in een mandje liggen en waarvan de datum verlopen is
        # hiervan wordt de reservering verwijderd
        mandje_pks = list()
        for plugin in bestel_plugins.values():
            mandje_pks.extend(
                plugin.mandje_opschonen(verval_datum)
            )
        # for

        # mandjes bijwerken
        mandje_pks = set(mandje_pks)  # remove dupes
        for mandje in BestellingMandje.objects.filter(pk__in=mandje_pks):
            _automatische_kortingen_toepassen(self.stdout, mandje)
            self._bepaal_verzendkosten_mandje(mandje)
        # for

        self.stdout.write('[INFO] Opschonen mandjes klaar')

    @staticmethod
    def _bepaal_verzendkosten_mandje(mandje):
        """ bereken de verzendkosten voor fysieke producten in het mandje """

        mandje.verzendkosten_euro = transportkosten_bestel_plugin.bereken_verzendkosten(mandje)

        if mandje.verzendkosten_euro > 0.00:
            # wel fysieke producten
            if mandje.transport == BESTELLING_TRANSPORT_NVT:
                # bij toevoegen eerste product schakelen we over op verzenden
                # gebruiker kan deze op "ophalen" zetten
                mandje.transport = BESTELLING_TRANSPORT_VERZEND

        mandje.save(update_fields=['verzendkosten_euro', 'transport'])

    @staticmethod
    def _bepaal_verzendkosten_bestelling(transport, bestelling):
        """ bereken de verzendkosten voor fysieke producten van de bestelling
            transport: de transport keuze gemaakt door de gebruiker: ophalen of verzenden
        """

        bestelling.verzendkosten_euro = transportkosten_bestel_plugin.bereken_verzendkosten(bestelling)
        bestelling.transport = transport

        if bestelling.verzendkosten_euro < Decimal(0.001):
            # geen fysieke producten, dus transport is niet van toepassing
            bestelling.transport = BESTELLING_TRANSPORT_NVT

        bestelling.save(update_fields=['verzendkosten_euro', 'transport'])

    @staticmethod
    def _bestelling_bepaal_btw(bestelling: Bestelling):
        """ bereken de btw voor de producten in een bestelling """

        # TODO: meerdere BTW percentages ondersteunen

        # begin met een schone lei
        bestelling.btw_percentage_cat1 = ""
        bestelling.btw_euro_cat1 = Decimal(0)

        bestelling.btw_percentage_cat2 = ""
        bestelling.btw_euro_cat2 = Decimal(0)

        bestelling.btw_percentage_cat3 = ""
        bestelling.btw_euro_cat3 = Decimal(0)

        # kijk hoeveel euro aan webwinkelproducten in deze bestelling zitten
        totaal_euro = Decimal(0)
        for product in bestelling.regels.all():
            totaal_euro += product.bedrag_euro
        # for

        totaal_euro += bestelling.verzendkosten_euro

        if totaal_euro > 0:
            # converteer percentage (21.1) naar string "21,1"
            btw_str = "%.2f" % settings.WEBWINKEL_BTW_PERCENTAGE
            while btw_str[-1] == '0':
                btw_str = btw_str[:-1]  # 21,10 --> 21,1 / 21,00 --> 21,
            btw_str = btw_str.replace('.', ',')  # localize
            if btw_str[-1] == ",":
                btw_str = btw_str[:-1]  # drop the trailing dot/comma
            bestelling.btw_percentage_cat1 = btw_str

            # het totaalbedrag is inclusief BTW, dus 100% + BTW% (was: 121%)
            # reken uit hoeveel daarvan de BTW is
            btw_deel = Decimal(settings.WEBWINKEL_BTW_PERCENTAGE / (100 + settings.WEBWINKEL_BTW_PERCENTAGE))
            btw = totaal_euro * btw_deel
            btw = round(btw, 2)  # afronden op 2 decimalen
            bestelling.btw_euro_cat1 = btw

        bestelling.save(update_fields=['btw_percentage_cat1', 'btw_euro_cat1',
                                       'btw_percentage_cat2', 'btw_euro_cat2',
                                       'btw_percentage_cat3', 'btw_euro_cat3'])

    def _verwerk_mutatie_wedstrijd_inschrijven(self, mutatie: BestellingMutatie):
        """ Verwerk een mutatie via de achtergrondtaak voor inschrijving op een wedstrijd
            Voeg deze toe aan het mandje van de gebruiker
        """
        mandje = self._get_mandje(mutatie)
        if mandje:  # pragma: no branch
            inschrijving = mutatie.wedstrijd_inschrijving

            # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
            if inschrijving.status != WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
                regel = wedstrijd_bestel_plugin.reserveer(
                    inschrijving,
                    mandje.account.get_account_full_name())
                mandje.regels.add(regel)

                # kijk of er automatische kortingen zijn die toegepast kunnen worden
                _automatische_kortingen_toepassen(stdout, mandje)

                # bereken het totaal opnieuw
                _mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_evenement_inschrijven(self, mutatie: BestellingMutatie):
        """ Verwerk een mutatie via de achtergrondtaak voor inschrijving op een evenement
            Voeg deze toe aan het mandje van de gebruiker
        """
        mandje = self._get_mandje(mutatie)
        if mandje:  # pragma: no branch
            inschrijving = mutatie.evenement_inschrijving

            # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
            if inschrijving.status != EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
                regel = evenement_bestel_plugin.reserveer(
                    mutatie.evenement_inschrijving,
                    mandje.account.get_account_full_name())
                mandje.regels.add(regel)

                inschrijving.nummer = inschrijving.pk
                inschrijving.save(update_fields=['nummer'])

                # bereken het totaal opnieuw
                _mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_opleiding_inschrijven(self, mutatie: BestellingMutatie):
        """ Verwerk een mutatie via de achtergrondtaak voor inschrijving op een opleiding
            Voeg deze toe aan het mandje van de gebruiker
        """
        mandje = self._get_mandje(mutatie)
        if mandje:  # pragma: no branch

            inschrijving = mutatie.opleiding_inschrijving

            # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
            if inschrijving.status != OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF:
                regel = opleiding_bestel_plugin.reserveer(
                    mutatie.opleiding_inschrijving,
                    mandje.account.get_account_full_name())
                mandje.regels.add(regel)

                inschrijving.nummer = inschrijving.pk
                inschrijving.save(update_fields=['nummer'])

                # bereken het totaal opnieuw
                _mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_webwinkel_keuze(self, mutatie: BestellingMutatie):
        """ Verwerk een mutatie via de achtergrondtaak voor selectie van een product uit de webwinkel
            Voeg deze toe aan het mandje van de gebruiker
        """
        mandje = self._get_mandje(mutatie)
        if mandje:  # pragma: no branch

            regel = webwinkel_bestel_plugin.reserveer(
                mutatie.webwinkel_keuze,
                mandje.account.get_account_full_name())
            mandje.regels.add(regel)

            transport_oud = mandje.transport

            # bereken het totaal opnieuw
            self._bepaal_verzendkosten_mandje(mandje)
            _mandje_bepaal_btw(mandje)
            mandje.bepaal_totaalprijs_opnieuw()

            transport_nieuw = mandje.transport

            if transport_oud != transport_nieuw:
                self.stdout.write('[INFO] Transport: %s --> %s' % (BESTELLING_TRANSPORT2STR[transport_oud],
                                                                   BESTELLING_TRANSPORT2STR[transport_nieuw]))
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

    def _verwerk_mutatie_verwijder_uit_mandje(self, mutatie: BestellingMutatie):
        """ een bestelling mag uit het mandje voordat de betaling gestart is """

        mandje = self._get_mandje(mutatie)
        if mandje:  # pragma: no branch
            regel = mutatie.regel
            qset = mandje.regels.filter(pk=regel.pk)
            if qset.exists():  # pragma: no branch
                # product zit nog in het mandje (anders: ignore want waarschijnlijk een dubbel verzoek)
                self.stdout.write('[INFO] Regel met pk=%s (code %s) wordt verwijderd uit het mandje van %s' % (
                                  regel.pk, regel.code, mandje.account.username))

                plugin = bestel_plugins[regel.code]
                nieuwe_regel = plugin.verwijder_reservering(regel)

                # verwijder uit het mandje
                mandje.regels.remove(regel)

                if nieuwe_regel:
                    # vervangt een inschrijving door een afmelding
                    mandje.regels.add(nieuwe_regel)

                # kijk of er automatische kortingen zijn die niet meer toegepast mogen worden
                _automatische_kortingen_toepassen(stdout, mandje)

                self._bepaal_verzendkosten_mandje(mandje)

                # bereken het totaal opnieuw
                _mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_maak_bestellingen(self, mutatie: BestellingMutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:  # pragma: no branch
            # zorg dat we verse informatie ophalen (anders duur het 1 uur voordat een update door komt)
            self._clear_instellingen_cache()

            # maak een Mollie-client instantie aan
            mollie_client = Client(api_endpoint=settings.BETAAL_API_URL)

            # verdeel de producten in het mandje naar vereniging waar de betaling heen moet
            ontvanger2regels = dict()  # [ver_nr] = [BestellingRegel, ...]
            for regel in mandje.regels.all():
                plugin = bestel_plugins[regel.code]
                ver_nr = plugin.verkopende_vereniging(regel)

                instellingen = self._get_betaal_instellingen(ver_nr)
                ontvanger_ver_nr = instellingen.vereniging.ver_nr  # kan nu ook "via KHSN" zijn

                try:
                    ontvanger2regels[ontvanger_ver_nr].append(regel)
                except KeyError:
                    ontvanger2regels[ontvanger_ver_nr] = [regel]
            # for

            nieuwe_bestellingen = list()
            for ver_nr, regels in ontvanger2regels.items():

                instellingen = self._instellingen_cache[ver_nr]
                ver = instellingen.vereniging

                # neem een bestelnummer uit
                bestel_nr = _bestel_get_volgende_bestel_nr()

                totaal_euro = Decimal('0')
                for regel in regels:
                    totaal_euro += regel.bedrag_euro
                # for

                bestelling = Bestelling(
                                bestel_nr=bestel_nr,
                                account=mutatie.account,
                                ontvanger=instellingen,
                                totaal_euro=totaal_euro,
                                verkoper_kvk=ver.kvk_nummer,
                                verkoper_bic=ver.bank_bic,
                                verkoper_iban=ver.bank_iban,
                                verkoper_naam=ver.naam,
                                verkoper_email=ver.contact_email,
                                verkoper_adres1=ver.adres_regel1,
                                verkoper_adres2=ver.adres_regel2,
                                verkoper_telefoon=ver.telefoonnummer,
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
                bestelling.regels.set(regels)

                self._bepaal_verzendkosten_bestelling(mandje.transport, bestelling)

                totaal_euro += bestelling.verzendkosten_euro

                self._bestelling_bepaal_btw(bestelling)

                # toon het BTW-nummer alleen als het relevant is
                if ver_nr == settings.WEBWINKEL_VERKOPER_VER_NR:
                    if bestelling.btw_percentage_cat1:
                        bestelling.verkoper_btw_nr = settings.WEBWINKEL_VERKOPER_BTW_NR

                bestelling.totaal_euro = totaal_euro
                bestelling.save(update_fields=['totaal_euro', 'verkoper_btw_nr'])

                when_str = timezone.localtime(bestelling.aangemaakt).strftime('%Y-%m-%d om %H:%M')
                totaal_euro_str = format_bedrag_euro(totaal_euro)

                msg = "[%s] Bestelling aangemaakt met %s producten voor totaal %s" % (
                        when_str, len(regels), totaal_euro_str)
                bestelling.log = msg
                bestelling.save(update_fields=['log'])

                nieuwe_bestellingen.append(bestelling)

                # haal deze producten uit het mandje
                mandje.regels.remove(*regels)

                # zet de status van elke regel om
                for regel in regels:
                    plugin = bestel_plugins[regel.code]
                    plugin.is_besteld(regel)
                # for

                totaal_euro_str = format_bedrag_euro(totaal_euro)

                self.stdout.write(
                    "[INFO] %s producten voor totaal %s uit mandje account %s omgezet in bestelling pk=%s" % (
                        len(regels), totaal_euro_str, mutatie.account.volledige_naam(), bestelling.pk))
            # for

            # kijk welke bestellingen een nul-bedrag hebben en daarom meteen afgerond kunnen worden
            for bestelling in nieuwe_bestellingen:
                if bestelling.totaal_euro < Decimal('0.001'):
                    self.stdout.write('[INFO] Bestelling pk=%s met bedrag €0,00 wordt meteen afgerond' % bestelling.pk)

                    for regel in bestelling.regels.all():
                        plugin = bestel_plugins[regel.code]
                        plugin.is_betaald(regel)
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
            self._bepaal_verzendkosten_mandje(mandje)
            _mandje_bepaal_btw(mandje)
            mandje.bepaal_totaalprijs_opnieuw()

    def verwerk(self, mutatie: BestellingMutatie):
        """ Verwerk een mutatie die via de database tabel ontvangen is """
        code = mutatie.code

        if code == BESTELLING_MUTATIE_WEDSTRIJD_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_wedstrijd_inschrijven(mutatie)

        elif code == BESTELLING_MUTATIE_EVENEMENT_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op evenement' % mutatie.pk)
            self._verwerk_mutatie_evenement_inschrijven(mutatie)

        elif code == BESTELLING_MUTATIE_OPLEIDING_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op opleiding' % mutatie.pk)
            self._verwerk_mutatie_opleiding_inschrijven(mutatie)

        elif code == BESTELLING_MUTATIE_WEBWINKEL_KEUZE:
            self.stdout.write('[INFO] Verwerk mutatie %s: webwinkel keuze' % mutatie.pk)
            self._verwerk_mutatie_webwinkel_keuze(mutatie)

        elif code == BESTELLING_MUTATIE_VERWIJDER:
            self.stdout.write('[INFO] Verwerk mutatie %s: verwijder regel uit mandje' % mutatie.pk)
            self._verwerk_mutatie_verwijder_uit_mandje(mutatie)

        elif code == BESTELLING_MUTATIE_MAAK_BESTELLINGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: mandje omzetten in bestelling(en)' % mutatie.pk)
            self._verwerk_mutatie_maak_bestellingen(mutatie)

        elif code == BESTELLING_MUTATIE_WEDSTRIJD_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor wedstrijd' % mutatie.pk)
            verwerk_mutatie_wedstrijd_afmelden(stdout, mutatie)

        elif code == BESTELLING_MUTATIE_EVENEMENT_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor evenement' % mutatie.pk)
            verwerk_mutatie_evenement_afmelden(stdout, mutatie)

        elif code == BESTELLING_MUTATIE_BETALING_AFGEROND:
            self.stdout.write('[INFO] Verwerk mutatie %s: betaling afgerond' % mutatie.pk)
            verwerk_mutatie_betaling_afgerond(stdout, mutatie)

        elif code == BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: overboeking ontvangen' % mutatie.pk)
            verwerk_mutatie_overboeking_ontvangen(stdout, mutatie)

        # elif code == BESTELLING_MUTATIE_RESTITUTIE_UITBETAALD:
        #     self.stdout.write('[INFO] Verwerk mutatie %s: restitutie uitbetaald' % mutatie.pk)
        #     verwerk_mutatie_restitutie_uitbetaald(stdout, mutatie)

        elif code == BESTELLING_MUTATIE_ANNULEER:
            self.stdout.write('[INFO] Verwerk mutatie %s: annuleer bestelling' % mutatie.pk)
            verwerk_mutatie_annuleer_bestelling(stdout, mutatie)

        elif code == BESTELLING_MUTATIE_TRANSPORT:
            self.stdout.write('[INFO] Verwerk mutatie %s: wijzig transport' % mutatie.pk)
            verwerk_mutatie_transport(stdout, mutatie)

        elif code == BESTELLING_MUTATIE_OPLEIDING_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor opleiding' % mutatie.pk)
            verwerk_mutatie_opleiding_afmelden(stdout, mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))


def _automatische_kortingen_toepassen(stdout, mandje):
    BepaalAutomatischeKorting(stdout).kies_kortingen_voor_mandje(mandje)


def _btw_optellen(regels: list[BestellingRegel]) -> dict:
    perc2btw = dict()       # [percentage] = Decimal()

    for regel in regels:
        if regel.btw_percentage:
            # is gezet
            try:
                perc2btw[regel.btw_percentage] += regel.btw_euro
            except KeyError:
                perc2btw[regel.btw_percentage] = regel.btw_euro
    # for

    return perc2btw


def _beschrijf_bestelling(bestelling: Bestelling):

    regel_nr = 0

    regels = list(bestelling.regels.order_by('pk'))
    for regel in regels:
        # nieuwe regel op de bestelling
        regel_nr += 1
        regel.regel_nr = regel_nr

        # product.beschrijving = beschrijf_product(product)
        # product.prijs_euro_str = format_bedrag_euro(product.prijs_euro)
        # product.korting_euro_str = format_bedrag_euro(product.korting_euro)     # positief bedrag
        #
        # if product.wedstrijd_inschrijving:
        #     korting = product.wedstrijd_inschrijving.korting
        #     if korting:
        #         product.gebruikte_korting_str, combi_redenen = beschrijf_korting(product)
        #         if korting.soort == WEDSTRIJD_KORTING_COMBI:
        #             product.combi_reden = " en ".join(combi_redenen)
    # for

    # voeg de eventuele verzendkosten toe als aparte regel op de bestelling
    if bestelling.verzendkosten_euro > 0.001:

        verzendkosten_euro_str = format_bedrag_euro(bestelling.verzendkosten_euro)

        # nieuwe regel op de bestelling
        regel_nr += 1
        regel = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=[("Verzendkosten", "")],       # TODO: specialiseren in pakket/briefpost
                        # geen btw op transport
                        prijs_euro_str=verzendkosten_euro_str)
        regels.append(regel)

    if bestelling.transport == BESTELLING_TRANSPORT_OPHALEN:

        nul_euro_str = format_bedrag_euro(Decimal(0))

        # nieuwe regel op de bestelling
        regel_nr += 1
        regel = SimpleNamespace(
                        regel_nr=regel_nr,
                        beschrijving=[("Ophalen op het bondsbureau", "")],
                        prijs_euro_str=nul_euro_str)
        regels.append(regel)

    # formatteren van de BTW bedragen
    bestelling.btw_euro_cat1_str = format_bedrag_euro(bestelling.btw_euro_cat1)
    bestelling.btw_euro_cat2_str = format_bedrag_euro(bestelling.btw_euro_cat2)
    bestelling.btw_euro_cat3_str = format_bedrag_euro(bestelling.btw_euro_cat3)

    return regels


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

    regels = _beschrijf_bestelling(bestelling)

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
        'regels': regels,
        'bestel_status': BESTELLING_STATUS2STR[bestelling.status],
        'kan_betalen': bestelling.status not in (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD),
        'heeft_afleveradres': heeft_afleveradres,
        'wil_ophalen': bestelling.transport == BESTELLING_TRANSPORT_OPHALEN,
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

    regels = _beschrijf_bestelling(bestelling)
    transacties = _beschrijf_transacties(bestelling)
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
        'regels': regels,
        'transacties': transacties,
        'heeft_afleveradres': heeft_afleveradres,
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

    regels = _beschrijf_bestelling(bestelling)
    transacties = _beschrijf_transacties(bestelling)

    totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

    context = {
        'koper_sporter': sporter,       # bevat postadres
        'naam_site': settings.NAAM_SITE,
        'bestelling': bestelling,
        'totaal_euro_str': totaal_euro_str,
        'regels': regels,
        'transacties': transacties,
        'waarschuw_test_server': settings.IS_TEST_SERVER,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BACKOFFICE_VERSTUREN)

    mailer_queue_email(email_backoffice,
                       'Verstuur webwinkel producten (%s)' % bestelling.mh_bestel_nr(),
                       mail_body)


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


def _mandje_bepaal_btw(mandje):
    """ bereken de btw voor de producten in het mandje """

    # begin met een schone lei
    mandje.btw_percentage_cat1 = ""
    mandje.btw_euro_cat1 = Decimal(0)

    mandje.btw_percentage_cat2 = ""
    mandje.btw_euro_cat2 = Decimal(0)

    mandje.btw_percentage_cat3 = ""
    mandje.btw_euro_cat3 = Decimal(0)

    # kijk hoeveel euro aan webwinkel producten in het mandje liggen
    totaal_btw_euro = Decimal(0)
    for regel in mandje.regels.all():
        totaal_btw_euro += regel.btw_euro
    # for

    # TODO: transportkosten via een BestellingRegel laten lopen
    #totaal_euro += mandje.verzendkosten_euro

    if not mandje:
        # converteer percentage (21,0) naar string "21.0%"
        btw_str = "%.2f" % settings.WEBWINKEL_BTW_PERCENTAGE
        while btw_str[-1] == '0':
            btw_str = btw_str[:-1]      # 21,10 --> 21,1 / 21,00 --> 21,
        btw_str = btw_str.replace('.', ',')       # localize
        if btw_str[-1] == ",":
            btw_str = btw_str[:-1]      # drop the trailing dot/comma
        mandje.btw_percentage_cat1 = btw_str

        # het totaalbedrag is inclusief BTW, dus 100% + BTW% (was: 121%)
        # reken uit hoeveel daarvan de BTW is (voorbeeld: 21 / 121)
        btw_deel = Decimal(settings.WEBWINKEL_BTW_PERCENTAGE / (100 + settings.WEBWINKEL_BTW_PERCENTAGE))
        btw = totaal_euro * btw_deel
        btw = round(btw, 2)             # afronden op 2 decimalen
        mandje.btw_euro_cat1 = btw

    mandje.save(update_fields=['btw_percentage_cat1', 'btw_euro_cat1',
                               'btw_percentage_cat2', 'btw_euro_cat2',
                               'btw_percentage_cat3', 'btw_euro_cat3'])







def verwerk_mutatie_wedstrijd_afmelden(stdout, mutatie: BestellingMutatie):
    inschrijving = mutatie.wedstrijd_inschrijving
    oude_status = inschrijving.status
    if not inschrijving:
        return

    # WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD --> doe niets
    # WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTELLING_MUTATIE_VERWIJDER
    if oude_status == WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD:
        # in een bestelling; nog niet (volledig) betaald
        stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor wedstrijd' % inschrijving.pk)

        wedstrijden_plugin_verwijder_reservering(stdout, inschrijving)
        # FUTURE: betaling afbreken
        # FUTURE: automatische restitutie als de betaling binnen is

    elif oude_status == WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
        # in een bestelling en betaald
        stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor wedstrijd' %
                          inschrijving.pk)

        wedstrijden_plugin_afmelden(inschrijving)
        # FUTURE: automatisch een restitutie beginnen
    else:
        stdout.write('[WARNING] Niet ondersteund: Inschrijving pk=%s met status=%s afmelden voor wedstrijd' % (
            inschrijving.pk, WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))


def verwerk_mutatie_evenement_afmelden(stdout, mutatie: BestellingMutatie):
    inschrijving = mutatie.evenement_inschrijving
    if not inschrijving:
        return

    # EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTELLING_MUTATIE_VERWIJDER
    if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_BESTELD:
        # in een bestelling; nog niet (volledig) betaald
        stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor evenement' % inschrijving.pk)

        mutatie.evenement_inschrijving = None
        mutatie.save(update_fields=['evenement_inschrijving'])

        evenement_plugin_verwijder_reservering(stdout, inschrijving)
        # FUTURE: betaling afbreken
        # FUTURE: automatische restitutie als de betaling binnen is

    elif inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
        # in een bestelling en betaald
        stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor evenement' % inschrijving.pk)

        mutatie.evenement_inschrijving = None
        mutatie.save(update_fields=['evenement_inschrijving'])

        evenement_plugin_afmelden(inschrijving)
        # FUTURE: automatisch een restitutie beginnen

    else:
        stdout.write('[WARNING] Niet ondersteund: Inschrijving pk=%s met status=%s afmelden voor evenement' % (
                     inschrijving.pk, EVENEMENT_STATUS_TO_STR[inschrijving.status]))


def verwerk_mutatie_opleiding_afmelden(stdout, mutatie: BestellingMutatie):
    inschrijving = mutatie.opleiding_inschrijving
    if not inschrijving:
        return

    # OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTELLING_MUTATIE_VERWIJDER
    if inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_BESTELD:
        # in een bestelling; nog niet (volledig) betaald
        stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor opleiding' % inschrijving.pk)

        # verwijder referentie vanuit mutatie, zodat inschrijving verwijderd kan worden
        mutatie.opleiding_inschrijving = None
        mutatie.save(update_fields=['opleiding_inschrijving'])

        opleiding_plugin_verwijder_reservering(stdout, inschrijving)
        # FUTURE: betaling afbreken
        # FUTURE: automatische restitutie als de betaling binnen is

    elif inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF:
        # in een bestelling en betaald
        stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor opleiding' % inschrijving.pk)

        # verwijder referentie vanuit mutatie, zodat inschrijving verwijderd kan worden
        mutatie.opleiding_inschrijving = None
        mutatie.save(update_fields=['opleiding_inschrijving'])

        opleiding_plugin_afmelden(inschrijving)
        # FUTURE: automatisch een restitutie beginnen

    else:
        stdout.write('[WARNING] Niet ondersteund: Inschrijving pk=%s met status=%s afmelden voor opleiding' % (
                     inschrijving.pk, OPLEIDING_STATUS_TO_STR[inschrijving.status]))


def verwerk_mutatie_betaling_afgerond(stdout, mutatie: BestellingMutatie):
    now = timezone.now()
    when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

    bestelling = mutatie.bestelling
    is_gelukt = mutatie.betaling_is_gelukt

    status = bestelling.status
    if status != BESTELLING_STATUS_BETALING_ACTIEF:
        stdout.write('[WARNING] Bestelling %s (pk=%s) wacht niet op een betaling (status=%s)' % (
                     bestelling.mh_bestel_nr(), bestelling.pk, BESTELLING_STATUS2STR[bestelling.status]))
        return

    actief = bestelling.betaal_actief
    if not actief:
        stdout.write('[WARNING] Bestelling %s (pk=%s) heeft geen actieve transactie' % (
                     bestelling.mh_bestel_nr(), bestelling.pk))
        return

    if is_gelukt:
        stdout.write('[INFO] Betaling is gelukt voor bestelling %s (pk=%s)' % (
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

        stdout.write('[INFO] Bestelling %s (pk=%s) heeft %s van de %s ontvangen' % (
                     bestelling.mh_bestel_nr(), bestelling.pk, ontvangen_euro_str, totaal_euro_str))

        msg = "\n[%s] Bestelling heeft %s van de %s euro ontvangen" % (
                    when_str, ontvangen_euro_str, totaal_euro_str)
        bestelling.log += msg
        bestelling.save(update_fields=['log'])

        if ontvangen_euro >= bestelling.totaal_euro:
            stdout.write('[INFO] Bestelling %s (pk=%s) is afgerond' % (bestelling.mh_bestel_nr(), bestelling.pk))
            bestelling.status = BESTELLING_STATUS_AFGEROND

            msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % when_str
            bestelling.log += msg
            bestelling.save(update_fields=['log'])

            bevat_webwinkel = False
            for regel in bestelling.regels.all():
                plugin = bestel_plugins[regel.code]
                plugin.is_betaald(regel)
                bevat_webwinkel |= regel.is_webwinkel()
            # for

            for product in bestelling.producten.all():
                if product.wedstrijd_inschrijving:
                    wedstrijden_plugin_inschrijving_is_betaald(stdout, product)
                elif product.evenement_inschrijving:
                    evenement_plugin_inschrijving_is_betaald(stdout, product)
                elif product.opleiding_inschrijving:
                    opleiding_plugin_inschrijving_is_betaald(stdout, product)
                elif product.webwinkel_keuze:
                    bevat_webwinkel = True
            # for

            # stuur een e-mail aan de koper
            stuur_email_naar_koper_betaalbevestiging(bestelling)

            # stuur een e-mail naar het backoffice
            if bevat_webwinkel:
                stuur_email_webwinkel_backoffice(bestelling, self._emailadres_backoffice)
    else:
        stdout.write('[INFO] Betaling niet gelukt voor bestelling %s (pk=%s)' % (
                            bestelling.mh_bestel_nr(), bestelling.pk))

        bestelling.status = BESTELLING_STATUS_MISLUKT

        msg = "\n[%s] Betaling is niet gelukt" % when_str
        bestelling.log += msg
        bestelling.save(update_fields=['log'])

    bestelling.betaal_actief = None
    bestelling.save(update_fields=['betaal_actief', 'status'])


def verwerk_mutatie_overboeking_ontvangen(stdout, mutatie: BestellingMutatie):
    now = timezone.now()
    when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

    bestelling = mutatie.bestelling
    bedrag_euro = mutatie.bedrag_euro

    stdout.write('[INFO] Overboeking %s euro ontvangen voor bestelling %s (pk=%s)' % (
                        bedrag_euro, bestelling.mh_bestel_nr(), bestelling.pk))

    status = bestelling.status
    if status == BESTELLING_STATUS_AFGEROND:
        stdout.write('[WARNING] Bestelling %s (pk=%s) is al afgerond (status=%s)' % (
                            bestelling.mh_bestel_nr(), bestelling.pk, BESTELLING_STATUS2STR[bestelling.status]))
        return

    stdout.write('[INFO] Betaling is gelukt voor bestelling %s (pk=%s)' % (
                        bestelling.mh_bestel_nr(), bestelling.pk))

    # koppel een transactie aan de bestelling
    transactie = maak_transactie_handmatige_overboeking(bestelling.mh_bestel_nr(), bedrag_euro)
    bestelling.transacties.add(transactie)

    msg = "\n[%s] Bestelling heeft een overboeking van %s euro ontvangen" % (
                when_str, bedrag_euro)
    bestelling.log += msg

    # controleer of we voldoende ontvangen hebben
    ontvangen_euro = bereken_som_betalingen(bestelling)

    stdout.write('[INFO] Bestelling %s (pk=%s) heeft %s van de %s euro ontvangen' % (
                        bestelling.mh_bestel_nr(), bestelling.pk, ontvangen_euro, bestelling.totaal_euro))

    msg = "\n[%s] Bestelling heeft %s van de %s euro ontvangen" % (
                when_str, ontvangen_euro, bestelling.totaal_euro)
    bestelling.log += msg

    bestelling.save(update_fields=['log'])

    if ontvangen_euro >= bestelling.totaal_euro:
        stdout.write('[INFO] Bestelling %s (pk=%s) is afgerond' % (
                            bestelling.mh_bestel_nr(), bestelling.pk))
        bestelling.status = BESTELLING_STATUS_AFGEROND

        msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % when_str
        bestelling.log += msg

        bestelling.save(update_fields=['status', 'log'])

        bevat_webwinkel = False
        for product in bestelling.producten.all():
            if product.wedstrijd_inschrijving:
                wedstrijden_plugin_inschrijving_is_betaald(stdout, product)
            elif product.evenement_inschrijving:
                evenement_plugin_inschrijving_is_betaald(stdout, product)
            elif product.webwinkel_keuze:
                bevat_webwinkel = True
        # for

        # stuur een e-mail naar het backoffice
        if bevat_webwinkel:
            stuur_email_webwinkel_backoffice(bestelling, _emailadres_backoffice)

        # stuur een e-mail aan de koper
        stuur_email_naar_koper_betaalbevestiging(bestelling)

    else:
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['status'])


def verwerk_mutatie_annuleer_bestelling(stdout, mutatie: BestellingMutatie):
    """ Annulering van een bestelling + verwijderen van de reserveringen + bevestig via e-mail """

    bestelling = mutatie.bestelling

    status = bestelling.status
    if status not in (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF):
        stdout.write('[WARNING] Kan bestelling %s (pk=%s) niet annuleren, want status = %s' % (
            bestelling.mh_bestel_nr(), bestelling.pk,
            BESTELLING_STATUS2STR[bestelling.status]))
        return

    stdout.write('[INFO] Bestelling %s (pk=%s) wordt nu geannuleerd' % (bestelling.bestel_nr, bestelling.pk))

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

        stdout.write('[INFO] Annuleer bestelling: BestelProduct pk=%s inschrijving (%s) besteld door %s' % (
            product.pk, inschrijving, inschrijving.koper))

        wedstrijden_plugin_verwijder_reservering(stdout, inschrijving)
    # for

    # evenement
    for product in (bestelling
                    .producten
                    .exclude(evenement_inschrijving=None)
                    .select_related('evenement_inschrijving',
                                    'evenement_inschrijving__koper')
                    .all()):

        inschrijving = product.evenement_inschrijving

        stdout.write('[INFO] Annuleer bestelling: BestelProduct pk=%s inschrijving (%s) besteld door %s' % (
                                product.pk, inschrijving, inschrijving.koper))

        afmelding = evenement_plugin_verwijder_reservering(stdout, inschrijving)

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

        stdout.write('[INFO] Annuleer: BestelProduct pk=%s webwinkel (%s) in mandje van %s' % (
            product.pk, keuze.product, keuze.koper))

        webwinkel_plugin_verwijder_reservering(stdout, keuze)
    # for

    # opleiding
    for product in (bestelling
                    .producten
                    .exclude(opleiding_inschrijving=None)
                    .select_related('opleiding_inschrijving',
                                    'opleiding_inschrijving__opleiding')
                    .all()):

        deelnemer = product.opleiding_inschrijving

        stdout.write('[INFO] Annuleer: BestelProduct pk=%s opleiding (%s) in mandje van %s' % (
                            product.pk, deelnemer.opleiding, deelnemer.koper))

        afmelding = opleiding_plugin_verwijder_reservering(stdout, deelnemer)

        product.opleiding_inschrijving = None
        product.opleiding_afgemeld = afmelding
        product.save(update_fields=['opleiding_inschrijving', 'opleiding_afgemeld'])
    # for


def verwerk_mutatie_transport(stdout, mutatie: BestellingMutatie):
    """ Wijzig keuze voor transport tussen ophalen en verzender; alleen voor webwinkel aankopen """

    # TODO: hoe is deze code anders dan in verwerk_mutatie_webwinkel_keuze()
    mandje = _get_mandje(stdout, mutatie)
    if mandje:                                  # pragma: no branch

        transport_oud = mandje.transport

        mandje.transport = mutatie.transport
        mandje.save(update_fields=['transport'])

        webwinkel_plugin_bepaal_verzendkosten_mandje(stdout, mandje)

        # bereken het totaal opnieuw
        _mandje_bepaal_btw(mandje)
        mandje.bepaal_totaalprijs_opnieuw()

        transport_nieuw = mandje.transport

        if transport_oud != transport_nieuw:
            stdout.write('[INFO] Transport: %s --> %s' % (BESTELLING_TRANSPORT2STR[transport_oud],
                                                          BESTELLING_TRANSPORT2STR[transport_nieuw]))
    else:
        stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)




# end of file
