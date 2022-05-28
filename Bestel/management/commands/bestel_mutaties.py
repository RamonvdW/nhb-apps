# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BestelMutatie
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import DataError, OperationalError, IntegrityError
from django.db import transaction
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Bestel.models import (BestelProduct, BestelMandje, Bestelling,
                           BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_WACHT_OP_BETALING,
                           BestelHoogsteBestelNr, BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK, BESTELLING_STATUS2STR,
                           BestelMutatie, BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN, BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN,
                           BESTEL_MUTATIE_VERWIJDER, BESTEL_MUTATIE_KORTINGSCODE, BESTEL_MUTATIE_MAAK_BESTELLING,
                           BESTEL_MUTATIE_BETALING_AFGEROND, BESTEL_MUTATIE_RESTITUTIE_UITBETAALD)
from Bestel.plugins.kalender import (kalender_plugin_automatische_kortingscodes_toepassen, kalender_plugin_inschrijven,
                                     kalender_plugin_verwijder_reservering, kalender_plugin_kortingscode_toepassen,
                                     kalender_plugin_afmelden, kalender_plugin_inschrijving_is_betaald)
from Kalender.models import (INSCHRIJVING_STATUS_RESERVERING_BESTELD, INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                             INSCHRIJVING_STATUS_AFGEMELD, INSCHRIJVING_STATUS_DEFINITIEF,
                             INSCHRIJVING_STATUS_TO_STR)
from Overig.background_sync import BackgroundSync
from decimal import Decimal
import traceback
import datetime
import sys


class Command(BaseCommand):

    help = "Betaal mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__BESTEL_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

        self._instellingen_nhb = None
        self._instellingen_cache = dict()     # [ver_nr] = BetaalInstellingenVereniging

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
            # let op: geen prefetch_related('producten') gebruiken ivm mutaties
            mandje, is_created = BestelMandje.objects.get_or_create(account=account)

        return mandje

    def _clear_instellingen_cache(self):
        self._instellingen_cache = dict()

        try:
            self._instellingen_nhb = (BetaalInstellingenVereniging
                                      .objects
                                      .select_related('vereniging')
                                      .get(vereniging__ver_nr=settings.BETAAL_VIA_NHB_VER_NR))
        except BetaalInstellingenVereniging.DoesNotExist:
            # nog niet aangemaakt
            self._instellingen_nhb = None

    def _get_instellingen(self, ver_nr):
        try:
            instellingen = self._instellingen_cache[ver_nr]
        except KeyError:
            try:
                instellingen = (BetaalInstellingenVereniging
                                .objects
                                .select_related('vereniging')
                                .get(vereniging__ver_nr=ver_nr))
            except BetaalInstellingenVereniging.DoesNotExist:
                instellingen = None
            else:
                if instellingen.akkoord_via_nhb:
                    instellingen = self._instellingen_nhb

                self._instellingen_cache[ver_nr] = instellingen

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

    def _verwerk_mutatie_wedstrijd_inschrijven(self, mutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            prijs_euro = kalender_plugin_inschrijven(mutatie.inschrijving)

            # maak een product regel aan voor de bestelling
            product = BestelProduct(
                            inschrijving=mutatie.inschrijving,
                            prijs_euro=prijs_euro)
            product.save()

            # leg het product in het mandje
            mandje.producten.add(product)

            # kijk of er automatische kortingscodes zijn die toegepast kunnen worden
            kalender_plugin_automatische_kortingscodes_toepassen(self.stdout, mandje)

            # bereken het totaal opnieuw
            mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_verwijder(self, mutatie):
        """ een bestelling mag uit het mandje voordat de betaling gestart is """

        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            qset = mandje.producten.filter(pk=mutatie.product.pk)
            if qset.exists():                       # pragma: no branch
                # product zit nog in het mandje (anders: ignore want waarschijnlijk een dubbel verzoek)
                product = qset[0]

                if product.inschrijving:
                    mandje.producten.remove(product)

                    inschrijving = product.inschrijving

                    kalender_plugin_verwijder_reservering(self.stdout, inschrijving)

                    mutatie.inschrijving = None
                    mutatie.product = None
                    mutatie.save()

                    # verwijder het product, dan verdwijnt deze ook uit het mandje
                    product.delete()

                    # verwijder de hele inschrijving, want bewaren heeft geen waarde op dit punt
                    # inschrijving.delete()     # geeft db integratie error ivm referenties die nog ergens bestaan
                else:
                    self.stderr.write('[ERROR] Verwijder product pk=%s uit mandje pk=%s: Type niet ondersteund' % (
                                        product.pk, mandje.pk))

            # kijk of er automatische kortingscodes zijn die niet meer toegepast mogen worden
            kalender_plugin_automatische_kortingscodes_toepassen(self.stdout, mandje)

            # bereken het totaal opnieuw
            mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_kortingscode(self, mutatie):
        """ Deze functie controleert of een kortingscode toegepast mag worden op de producten die in het mandje
            van het account staan.
        """
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            kortingscode_str = mutatie.kortingscode
            producten = mandje.producten.exclude(inschrijving=None)

            kalender_plugin_kortingscode_toepassen(self.stdout, kortingscode_str, producten)
            # FUTURE: opleiding_plugin_kortingscode_toepassen()

            # bereken het totaal opnieuw
            mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_maak_bestelling(self, mutatie):
        mandje = self._get_mandje(mutatie)
        if mandje:                                  # pragma: no branch
            # zorg dat we verse informatie ophalen (anders 1 uur geblokkeerd)
            self._clear_instellingen_cache()

            # verdeel de producten in het mandje naar vereniging waar de betaling heen moet
            ontvanger2producten = dict()      # [ver_nr] = [MandjeProduct, ...]
            for product in (mandje
                            .producten
                            .select_related('inschrijving')
                            .order_by('inschrijving__pk')):

                if product.inschrijving:
                    # wedstrijd van de kalender
                    ver_nr = product.inschrijving.wedstrijd.organiserende_vereniging.ver_nr
                    instellingen = self._get_instellingen(ver_nr)
                    if instellingen:
                        ontvanger_ver_nr = instellingen.vereniging.ver_nr
                        try:
                            ontvanger2producten[ontvanger_ver_nr].append(product)
                        except KeyError:
                            ontvanger2producten[ontvanger_ver_nr] = [product]
            # for

            nieuwe_bestellingen = list()
            for ver_nr, producten in ontvanger2producten.items():

                instellingen = self._get_instellingen(ver_nr)

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
                                    totaal_euro=totaal_euro)
                bestelling.save()
                bestelling.producten.set(producten)

                msg = "[%s] Bestelling aangemaakt met %s producten voor totaal euro=%s" % (
                                                bestelling.aangemaakt, len(producten), totaal_euro)
                bestelling.log = msg
                bestelling.save(update_fields=['log'])

                nieuwe_bestellingen.append(bestelling)

                # haal deze producten uit het mandje
                mandje.producten.remove(*producten)

                # pas de status aan van wedstrijd inschrijvingen
                for product in producten:
                    if product.inschrijving:
                        inschrijving = product.inschrijving
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
                    for product in bestelling.producten.all():
                        if product.inschrijving:
                            kalender_plugin_inschrijving_is_betaald(product)
                    # for

                    bestelling.status = BESTELLING_STATUS_AFGEROND
                    bestelling.save(update_fields=['status'])
                else:
                    # wijzig de status in 'wacht op betaling'
                    bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
                    bestelling.save(update_fields=['status'])
            # for

            # zorg dat het totaal van het mandje ook weer klopt
            mandje.bepaal_totaalprijs_opnieuw()

    def _verwerk_mutatie_wedstrijd_afmelden(self, mutatie):
        inschrijving = mutatie.inschrijving
        oude_status = inschrijving.status

        # INSCHRIJVING_STATUS_AFGEMELD --> doe niets
        # INSCHRIJVING_STATUS_RESERVERING_MANDJE gaat via BESTEL_MUTATIE_VERWIJDER

        if oude_status == INSCHRIJVING_STATUS_RESERVERING_BESTELD:
            # in een bestelling; nog niet (volledig) betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="besteld" afmelden voor wedstrijd' % inschrijving.pk)

            kalender_plugin_verwijder_reservering(self.stdout, inschrijving)
            # FUTURE: betaling afbreken
            # FUTURE: automatische restitutie als de betaling binnen is

        elif oude_status == INSCHRIJVING_STATUS_DEFINITIEF:
            # in een bestelling en betaald
            self.stdout.write('[INFO] Inschrijving pk=%s met status="definitief" afmelden voor wedstrijd' % inschrijving.pk)

            kalender_plugin_afmelden(inschrijving)
            # FUTURE: automatisch een restitutie beginnen

    def _verwerk_mutatie_betaling_afgerond(self, mutatie):
        bestelling = mutatie.bestelling
        is_gelukt = mutatie.betaling_is_gelukt

        status = bestelling.status
        if status != BESTELLING_STATUS_WACHT_OP_BETALING:
            self.stdout.write('[WARNING] Bestelling %s (pk=%s) wacht niet op een betaling (status=%s)' % (
                                bestelling.bestel_nr, bestelling.pk, BESTELLING_STATUS2STR[bestelling.status]))
            return

        actief = bestelling.betaal_actief
        if not actief:
            self.stdout.write('[WARNING] Bestelling %s (pk=%s) heeft geen actieve transactie' % (
                                bestelling.bestel_nr, bestelling.pk))
            return

        if is_gelukt:
            self.stdout.write('[INFO] Betaling is gelukt voor bestelling %s (pk=%s)' % (
                                bestelling.bestel_nr, bestelling.pk))

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

            self.stdout.write('[INFO] Bestelling %s (pk=%s) heeft %s van de %s euro ontvangen' % (
                                bestelling.bestel_nr, bestelling.pk, ontvangen_euro, bestelling.totaal_euro))

            msg = "\n[%s] Bestelling heeft %s van de %s euro ontvangen" % (
                mutatie.when, ontvangen_euro, bestelling.totaal_euro)
            bestelling.log += msg
            bestelling.save(update_fields=['log'])

            if ontvangen_euro >= bestelling.totaal_euro:
                self.stdout.write('[INFO] Bestelling %s (pk=%s) is afgerond' % (
                                    bestelling.bestel_nr, bestelling.pk))
                bestelling.status = BESTELLING_STATUS_AFGEROND

                msg = "\n[%s] Bestelling is afgerond (volledig betaald)" % mutatie.when
                bestelling.log += msg
                bestelling.save(update_fields=['log'])

                for product in bestelling.producten.all():
                    if product.inschrijving:
                        kalender_plugin_inschrijving_is_betaald(product)
                # for
        else:
            self.stdout.write('[INFO] Betaling niet gelukt voor bestelling %s (pk=%s)' % (
                                bestelling.bestel_nr, bestelling.pk))
            # laat status staan op "wacht op betaling"

        bestelling.betaal_actief = None
        bestelling.save(update_fields=['betaal_actief', 'status'])

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.code

        if code == BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: inschrijven op wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_wedstrijd_inschrijven(mutatie)

        elif code == BESTEL_MUTATIE_VERWIJDER:
            self.stdout.write('[INFO] Verwerk mutatie %s: verwijder product uit mandje' % mutatie.pk)
            self._verwerk_mutatie_verwijder(mutatie)

        elif code == BESTEL_MUTATIE_KORTINGSCODE:
            self.stdout.write('[INFO] Verwerk mutatie %s: kortingscode toepassen' % mutatie.pk)
            self._verwerk_mutatie_kortingscode(mutatie)

        elif code == BESTEL_MUTATIE_MAAK_BESTELLING:
            self.stdout.write('[INFO] Verwerk mutatie %s: mandje omzetten in bestelling(en)' % mutatie.pk)
            self._verwerk_mutatie_maak_bestelling(mutatie)

        elif code == BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden voor wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_wedstrijd_afmelden(mutatie)

        elif code == BESTEL_MUTATIE_BETALING_AFGEROND:
            self.stdout.write('[INFO] Verwerk mutatie %s: betaling afgerond' % mutatie.pk)
            self._verwerk_mutatie_betaling_afgerond(mutatie)

        elif code == BESTEL_MUTATIE_RESTITUTIE_UITBETAALD:
            self.stdout.write('[INFO] Verwerk mutatie %s: restitutie uitbetaald' % mutatie.pk)
            self._verwerk_mutatie_restitutie_uitbetaald(mutatie)

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

        mutatie_pks = qset.values_list('pk', flat=True)     # deferred

        self._hoogste_mutatie_pk = mutatie_latest.pk

        did_useful_work = False
        for pk in mutatie_pks:
            # we halen de records hier 1 voor 1 op
            # zodat we verse informatie hebben inclusief de vorige mutatie
            # en zodat we 1 plek hebben voor select/prefetch
            mutatie = (BestelMutatie
                       .objects
                       .select_related('account',
                                       'inschrijving',
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
