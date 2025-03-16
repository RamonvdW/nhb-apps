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
                                   BESTELLING_TRANSPORT_NVT, BESTELLING_TRANSPORT_VERZEND,
                                   BESTELLING_REGEL_CODE_WEBWINKEL)
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_STATUS2STR, BESTELLING_HOOGSTE_BESTEL_NR_FIXED_PK,
                                   BESTELLING_TRANSPORT2STR)
from Bestelling.models import (Bestelling, BestellingRegel, BestellingMandje,
                               BestellingHoogsteBestelNr, BestellingMutatie)
from Bestelling.operations.bepaal_kortingen import BepaalAutomatischeKorting
from Bestelling.operations.email_backoffice import stuur_email_webwinkel_backoffice
from Bestelling.operations.email_koper import (stuur_email_naar_koper_bestelling_details,
                                               stuur_email_naar_koper_betaalbevestiging)
from Bestelling.plugins.alle_bestel_plugins import bestel_plugins
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE, TRANSACTIE_TYPE_HANDMATIG
from Betaal.format import format_bedrag_euro
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Betaal.operations import maak_transactie_handmatige_overboeking
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF, EVENEMENT_STATUS_TO_STR,
                                  EVENEMENT_INSCHRIJVING_STATUS_BESTELD)
from Evenement.plugin_bestelling import evenement_bestel_plugin
from Functie.models import Functie
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                                  OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                                  OPLEIDING_STATUS_TO_STR)
from Opleiding.plugin_bestelling import opleiding_bestel_plugin
from Vereniging.models import Vereniging
from Webwinkel.plugin_bestelling import webwinkel_bestel_plugin, verzendkosten_bestel_plugin
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR)
from Wedstrijden.plugin_bestelling import wedstrijd_bestel_plugin
from mollie.api.client import Client, RequestSetupError
from decimal import Decimal
import datetime


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

        ver_bond = Vereniging.objects.get(ver_nr=settings.BETAAL_VIA_BOND_VER_NR)

        self._instellingen_via_bond, _ = (BetaalInstellingenVereniging
                                          .objects
                                          .select_related('vereniging')
                                          .get_or_create(vereniging=ver_bond))

        self._instellingen_cache[ver_bond.ver_nr] = self._instellingen_via_bond

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

    def _automatische_kortingen_toepassen(self, mandje: BestellingMandje):
        BepaalAutomatischeKorting(self.stdout).kies_kortingen_voor_mandje(mandje)

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
            self._automatische_kortingen_toepassen(mandje)
            self._bepaal_verzendkosten_mandje(mandje)
        # for

        self.stdout.write('[INFO] Opschonen mandjes klaar')

    @staticmethod
    def _bepaal_verzendkosten_mandje(mandje):
        """ bereken de verzendkosten voor fysieke producten in het mandje """

        mandje.verzendkosten_euro = verzendkosten_bestel_plugin.bereken_verzendkosten(mandje)

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

        bestelling.verzendkosten_euro = verzendkosten_bestel_plugin.bereken_verzendkosten(bestelling)
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
                self._automatische_kortingen_toepassen(mandje)

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
                plugin.annuleer(regel)

                # verwijder uit het mandje
                mandje.regels.remove(regel)

                # kijk of er automatische kortingen zijn die niet meer toegepast mogen worden
                self._automatische_kortingen_toepassen(mandje)

                self._bepaal_verzendkosten_mandje(mandje)

                # bereken het totaal opnieuw
                _mandje_bepaal_btw(mandje)
                mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_maak_bestellingen(self, mutatie: BestellingMutatie):

        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        mandje = self._get_mandje(mutatie)
        if not mandje:  # pragma: no branch
            return

        # zorg dat we verse informatie ophalen (anders duurt het 1 uur voordat een update door komt)
        self._clear_instellingen_cache()

        # maak een Mollie-client instantie aan
        mollie_client = Client(api_endpoint=settings.BETAAL_API_URL)

        # verdeel de producten in het mandje naar vereniging waar de betaling heen moet
        ontvanger2regels = dict()  # [ver_nr] = [BestellingRegel, ...]
        for regel in mandje.regels.all():
            plugin = bestel_plugins[regel.code]
            ver_nr = plugin.get_verkoper_ver_nr(regel)
            if ver_nr <= 0:
                # niet van toepassing
                continue

            instellingen = self._get_betaal_instellingen(ver_nr)
            ontvanger_ver_nr = instellingen.vereniging.ver_nr  # kan nu ook "via KHSN" zijn

            try:
                ontvanger2regels[ontvanger_ver_nr].append(regel)
            except KeyError:
                ontvanger2regels[ontvanger_ver_nr] = [regel]
        # for

        # maak per partij waarmee afgerekend moet worden een aparte bestelling
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
                    plugin.is_betaald(regel, Decimal(0.0))
                # for

                msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % when_str
                bestelling.log += msg
                bestelling.status = BESTELLING_STATUS_AFGEROND
                bestelling.save(update_fields=['status', 'log'])
            else:
                # laat de status op BESTELLING_STATUS_NIEUW staan totdat de betaling opgestart is
                pass

            # stuur voor elke bestelling een bevestiging naar de koper met details van de bestelling
            # en instructies voor betaling (niet nodig / handmatig / via Mollie)
            stuur_email_naar_koper_bestelling_details(bestelling)
        # for

        # zorg dat het totaal van het mandje ook weer klopt
        self._bepaal_verzendkosten_mandje(mandje)
        _mandje_bepaal_btw(mandje)
        mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_wedstrijd_afmelden(self, mutatie: BestellingMutatie):
        """ serialisatie van verzoek tot afmelden voor een wedstrijd, ingediend door de HWL
            product ligt niet meer in een mandje
            het kan een handmatige inschrijving zijn, zonder bestelling
        """
        wedstrijd_bestel_plugin.afmelden(mutatie.wedstrijd_inschrijving)

    def _verwerk_mutatie_evenement_afmelden(self, mutatie: BestellingMutatie):
        """ serialisatie van verzoek tot afmelden voor een wedstrijd, ingediend door de HWL
            product ligt niet meer in een mandje
            het kan een handmatige inschrijving zijn, zonder bestelling
        """
        evenement_bestel_plugin.afmelden(mutatie.evenement_inschrijving)

    def _verwerk_mutatie_opleiding_afmelden(self, mutatie: BestellingMutatie):
        """ serialisatie van verzoek tot afmelden voor een wedstrijd, ingediend door de HWL
            product ligt niet meer in een mandje
            het kan een handmatige inschrijving zijn, zonder bestelling
        """
        opleiding_bestel_plugin.afmelden(mutatie.opleiding_inschrijving)

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

            msg = "\n[%s] Bestelling heeft %s van de %s euro ontvangen" % (
                when_str, ontvangen_euro_str, totaal_euro_str)
            bestelling.log += msg
            bestelling.save(update_fields=['log'])

            self.stdout.write('[INFO] Bestelling %s (pk=%s) heeft %s van de %s ontvangen' % (
                                bestelling.mh_bestel_nr(), bestelling.pk, ontvangen_euro_str, totaal_euro_str))

            if ontvangen_euro >= bestelling.totaal_euro:
                self.stdout.write('[INFO] Bestelling %s (pk=%s) is afgerond' % (bestelling.mh_bestel_nr(),
                                                                                bestelling.pk))

                msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % when_str
                bestelling.log += msg
                bestelling.status = BESTELLING_STATUS_AFGEROND
                bestelling.save(update_fields=['status', 'log'])

                bevat_webwinkel = False
                for regel in bestelling.regels.all():
                    plugin = bestel_plugins[regel.code]
                    plugin.is_betaald(regel, regel.bedrag_euro)

                    bevat_webwinkel |= regel.code == BESTELLING_REGEL_CODE_WEBWINKEL
                # for

                # stuur een e-mail aan de koper
                stuur_email_naar_koper_betaalbevestiging(bestelling)

                # stuur een e-mail naar het backoffice
                if bevat_webwinkel:
                    stuur_email_webwinkel_backoffice(bestelling)
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

        msg = "\n[%s] Bestelling heeft %s van de %s euro ontvangen" % (when_str, ontvangen_euro, bestelling.totaal_euro)
        bestelling.log += msg
        bestelling.save(update_fields=['log'])

        self.stdout.write('[INFO] Bestelling %s (pk=%s) heeft %s van de %s euro ontvangen' % (
                            bestelling.mh_bestel_nr(), bestelling.pk, ontvangen_euro, bestelling.totaal_euro))

        if ontvangen_euro >= bestelling.totaal_euro:
            self.stdout.write('[INFO] Bestelling %s (pk=%s) is afgerond' % (bestelling.mh_bestel_nr(), bestelling.pk))

            msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % when_str
            bestelling.log += msg
            bestelling.status = BESTELLING_STATUS_AFGEROND
            bestelling.save(update_fields=['status', 'log'])

            bevat_webwinkel = False
            for regel in bestelling.regels.all():
                plugin = bestel_plugins[regel.code]
                plugin.is_betaald(regel, regel.bedrag_euro)

                bevat_webwinkel |= regel.code == BESTELLING_REGEL_CODE_WEBWINKEL
            # for

            # stuur een e-mail naar het backoffice
            if bevat_webwinkel:
                stuur_email_webwinkel_backoffice(bestelling)

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
        bestelling.log += '\n[%s] Bestelling is geannuleerd' % when_str

        bestelling.status = BESTELLING_STATUS_GEANNULEERD
        bestelling.save(update_fields=['status', 'log'])

        # stuur een e-mail om de annulering te bevestigen
        stuur_email_naar_koper_bestelling_details(bestelling)

        # verwijder de reserveringen
        for regel in bestelling.regels.all():
            plugin = bestel_plugins[regel.code]
            plugin.annuleer(regel)
        # for

    def _verwerk_mutatie_transport(self, mutatie: BestellingMutatie):
        """ Wijzig keuze voor transport tussen ophalen en verzender; alleen voor webwinkel aankopen """

        # TODO: hoe is deze code anders dan in verwerk_mutatie_webwinkel_keuze()
        mandje = self._get_mandje(mutatie)
        if mandje:  # pragma: no branch

            transport_oud = mandje.transport

            mandje.transport = mutatie.transport
            mandje.save(update_fields=['transport'])

            verzendkosten_bestel_plugin.bereken_verzendkosten(mandje)

            # bereken het totaal opnieuw
            _mandje_bepaal_btw(mandje)
            mandje.bepaal_totaalprijs_opnieuw()

            transport_nieuw = mandje.transport

            if transport_oud != transport_nieuw:
                self.stdout.write('[INFO] Transport: %s --> %s' % (BESTELLING_TRANSPORT2STR[transport_oud],
                                                                   BESTELLING_TRANSPORT2STR[transport_nieuw]))
        else:
            self.stdout.write('[WARNING] Kan mandje niet vinden voor mutatie pk=%s' % mutatie.pk)

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
            self._verwerk_mutatie_wedstrijd_afmelden(mutatie)

        elif code == BESTELLING_MUTATIE_EVENEMENT_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor evenement' % mutatie.pk)
            self._verwerk_mutatie_evenement_afmelden(mutatie)

        elif code == BESTELLING_MUTATIE_OPLEIDING_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor opleiding' % mutatie.pk)
            self._verwerk_mutatie_opleiding_afmelden(mutatie)

        elif code == BESTELLING_MUTATIE_BETALING_AFGEROND:
            self.stdout.write('[INFO] Verwerk mutatie %s: betaling afgerond' % mutatie.pk)
            self._verwerk_mutatie_betaling_afgerond(mutatie)

        elif code == BESTELLING_MUTATIE_OVERBOEKING_ONTVANGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: overboeking ontvangen' % mutatie.pk)
            self._verwerk_mutatie_overboeking_ontvangen(mutatie)

        # elif code == BESTELLING_MUTATIE_RESTITUTIE_UITBETAALD:
        #     self.stdout.write('[INFO] Verwerk mutatie %s: restitutie uitbetaald' % mutatie.pk)
        #     verwerk_mutatie_restitutie_uitbetaald(stdout, mutatie)

        elif code == BESTELLING_MUTATIE_ANNULEER:
            self.stdout.write('[INFO] Verwerk mutatie %s: annuleer bestelling' % mutatie.pk)
            self._verwerk_mutatie_annuleer_bestelling(mutatie)

        elif code == BESTELLING_MUTATIE_TRANSPORT:
            self.stdout.write('[INFO] Verwerk mutatie %s: wijzig transport' % mutatie.pk)
            self._verwerk_mutatie_transport(mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))




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

# end of file
