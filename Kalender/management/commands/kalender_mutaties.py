# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via KalenderMutatie
"""

from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from Kalender.models import (KalenderMutatie, KalenderWedstrijdKortingscode,
                             KALENDER_MUTATIE_INSCHRIJVEN, KALENDER_MUTATIE_AFMELDEN, KALENDER_MUTATIE_KORTING,
                             INSCHRIJVING_STATUS_RESERVERING, INSCHRIJVING_STATUS_DEFINITIEF,
                             INSCHRIJVING_STATUS_AFGEMELD, INSCHRIJVING_STATUS_TO_STR)
from Mandje.models import MandjeProduct, MandjeBestelling, MANDJE_NOG_GEEN_BESTELLING
from Overig.background_sync import BackgroundSync
from decimal import Decimal
import django.db.utils
import traceback
import datetime
import sys


class Command(BaseCommand):
    help = "Kalender mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__KALENDER_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _verwerk_mutatie_inschrijven(self, mutatie):
        # voeg deze inschrijving toe aan het mandje van de koper
        inschrijving = mutatie.inschrijving
        if inschrijving is None:
            self.stderr.write('[WARNING] Inschrijf mutatie heeft geen inschrijving (meer) - skipping')
            return

        sessie = inschrijving.sessie

        if True or sessie.prijs_euro > 0.0:

            # zoek het mandje van de koper erbij
            bestelling, is_created = MandjeBestelling.objects.get_or_create(
                                                                account=inschrijving.koper,
                                                                boekingsnummer=MANDJE_NOG_GEEN_BESTELLING)
            if is_created:
                bestelling.totaal_euro = Decimal(0.0)       # anders problemen met optellen
                bestelling.save()

            # leg deze bestelling in het mandje zodat er afgerekend kan worden
            product = MandjeProduct(
                            account=inschrijving.koper,
                            inschrijving=inschrijving,
                            prijs_euro=sessie.prijs_euro)
            product.save()

            # leg het product in het mandje
            bestelling.producten.add(product)

            # verhoog de totale prijs
            with transaction.atomic():
                bestelling = MandjeBestelling.objects.select_for_update().get(pk=bestelling.pk)
                bestelling.totaal_euro += product.prijs_euro
                bestelling.save()

        # else:
        #     # gratis deelname loopt niet via het mandje
        #     inschrijving.betaling_voldaan = True
        #     inschrijving.save(update_fields=['betaling_voldaan'])

        # verhoog het aantal inschrijvingen op deze sessie
        sessie.aantal_inschrijvingen += 1
        sessie.save(update_fields=['aantal_inschrijvingen'])

    def _verwerk_mutatie_afmelden(self, mutatie):
        """ een sporter heeft zich afgemeld voor de wedstrijd """

        # voorkom dubbele mutaties
        inschrijving = mutatie.inschrijving
        if inschrijving is None:
            self.stderr.write('[WARNING] Afmeld mutatie heeft geen inschrijving (meer) - skipping')
            return

        # zet de inschrijving om in status=afgemeld
        # dit heeft de voorkeur over het verwijderen van inschrijvingen,
        # want als er wel een betaling volgt dan kunnen we die nergens aan koppelen
        oude_status = inschrijving.status
        inschrijving.status = INSCHRIJVING_STATUS_AFGEMELD
        inschrijving.save(update_fields=['status'])

        # schrijf de sporter uit bij de sessie
        sessie = inschrijving.sessie
        if sessie.aantal_inschrijvingen > 0:            # voorkom ongelukken: kan negatief niet opslaan
            sessie.aantal_inschrijvingen -= 1
            sessie.save(update_fields=['aantal_inschrijvingen'])

        mutatie.inschrijving = None
        mutatie.save(update_fields=['inschrijving'])

        self.stdout.write('[INFO] Inschrijving pk=%s status %s --> Afgemeld' % (
                        inschrijving.pk, INSCHRIJVING_STATUS_TO_STR[oude_status]))

        # zoek uit of deze inschrijving al betaald was
        producten = inschrijving.mandjeproduct_set.all()
        if producten.count() > 0:
            # is binnengekomen via een mandje
            product = producten[0]

            # zoek de bestelling waar deze bij hoort
            bestellingen = product.mandjebestelling_set.all()
            if bestellingen.count() > 0:
                bestelling = bestellingen[0]

                if bestelling.boekingsnummer == MANDJE_NOG_GEEN_BESTELLING:
                    # dit is het mandje, dus nog niet besteld en nog volledige wijzigbaar
                    # haal het product uit het mandje
                    bestelling.producten.remove(product)

                    self.stdout.write('[INFO] Product pk=%s verwijderd uit het mandje van account %s' % (
                                        product.pk, product.account.pk))

                    # verwijder de regel echt uit het mandje
                    product.delete()
                else:
                    # dit is een bestelling en die mogen we niet meer wijzigen
                    self.stderr.write('[DEBUG] Afmelding voor een bestelling (die niet meer gewijzigd mag worden)')
                    #if oude_status == INSCHRIJVING_STATUS_RESERVERING:
                    #elif oude_status == INSCHRIJVING_STATUS_DEFINITIEF:
            else:
                self.stderr.write('[ERROR] MandjeProduct pk=%s is niet gekoppeld aan een bestelling!' % product.pk)
        else:
            # inschrijving is handmatig aangemaakt
            pass

    def _verwerk_mutatie_korting(self, mutatie):
        """ Deze functie controleert of een kortingscode toegepast mag worden op de inschrijvingen
            die in het mandje van het account staan.
        """
        korting = mutatie.korting
        account = mutatie.korting_voor_account

        # controleer de geldigheidsdatum
        if korting.geldig_tot_en_met < timezone.now().date():
            self.stdout.write('[WARNING] Kortingscode pk=%s is niet meer geldig' % korting.pk)
            return

        # haal het mandje op
        try:
            bestelling = (MandjeBestelling
                          .objects
                          .get(account=account,
                               boekingsnummer=MANDJE_NOG_GEEN_BESTELLING))
        except MandjeBestelling.DoesNotExist:
            self.stdout.write('[WARNING] Geen mandje voor account pk=%s om kortingscode pk=%s op toe te passen' %
                              (account.pk, korting.pk))
            return

        # zoek regels in het mandje en kijk of de code toegepast kan worden
        nieuwe_totaal = Decimal(0.0)
        for product in (bestelling
                        .producten
                        .filter(account=account)
                        .select_related('inschrijving')):

            if product.inschrijving:
                toepassen = False

                if korting.voor_sporter:
                    self.stdout.write('[DEBUG] Korting: voor_sporter=%s' % korting.voor_sporter)
                    # code voor een specifiek sporter
                    if korting.voor_sporter == product.inschrijving.sporterboog.sporter:
                        toepassen = True
                        self.stdout.write('[DEBUG] Korting: juiste voor_sporter lid_nr=%s' % korting.voor_sporter.lid_nr)

                if korting.voor_vereniging:
                    self.stdout.write('[DEBUG] Korting: voor_vereniging=%s' % korting.voor_vereniging)
                    # alle sporters van deze vereniging mogen deze code gebruiken
                    # (bijvoorbeeld de organiserende vereniging)
                    if korting.voor_vereniging == product.inschrijving.sporterboog.sporter.bij_vereniging:
                        toepassen = True
                        self.stdout.write('[DEBUG] Korting: juiste voor_vereniging %s' % korting.voor_vereniging.ver_nr)

                if korting.voor_wedstrijden.all().count() > 0:
                    # korting is begrensd tot 1 wedstrijd of een serie wedstrijden
                    if korting.voor_wedstrijden.filter(id=product.inschrijving.wedstrijd.id).exists():
                        # code voor een specifieke wedstrijd
                        toepassen = True
                        self.stdout.write('[DEBUG] Korting: juiste wedstrijd pk=%s' % product.inschrijving.wedstrijd.pk)
                    else:
                        # leuke code, maar niet bedoeld voor deze wedstrijd
                        toepassen = False
                        self.stdout.write('[DEBUG] Korting: verkeerde wedstrijd')

                if toepassen:
                    vervang = True
                    if product.inschrijving.gebruikte_code:
                        try:
                            huidige_code = product.inschrijving.gebruikte_code
                        except KalenderWedstrijdKortingscode.DoesNotExist:
                            # huidige code is niet valide --> vervang
                            pass
                        else:
                            # ga er vanuit dat de code nog geldig is omdat het mandje een korte levensduur heeft
                            # controleer welke de hoogste korting geeft
                            if huidige_code.percentage > korting.percentage:
                                vervang = False

                    if vervang:
                        # pas de code toe op deze inschrijving
                        inschrijving = product.inschrijving
                        inschrijving.gebruikte_code = korting
                        inschrijving.save(update_fields=['gebruikte_code'])

                        self.stdout.write('[INFO] Korting pk=%s toepassen op inschrijving pk=%s in mandje inhoud pk=%s' % (
                                                korting.pk, inschrijving.pk, product.pk))

                        # bereken de korting voor het mandje
                        procent = korting.percentage / Decimal(100.0)
                        product.korting_euro = product.prijs_euro * procent
                        product.korting_euro = min(product.korting_euro, product.prijs_euro)  # voorkom korting > prijs
                        product.save(update_fields=['korting_euro'])

            nieuwe_totaal += product.prijs_euro
            nieuwe_totaal -= product.korting_euro
        # for

        if bestelling.totaal_euro != nieuwe_totaal:
            bestelling.totaal_euro = nieuwe_totaal
            bestelling.save(update_fields=['totaal_euro'])

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.code

        if code == KALENDER_MUTATIE_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Inschrijven' % mutatie.pk)
            self._verwerk_mutatie_inschrijven(mutatie)

        elif code == KALENDER_MUTATIE_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Afmelden' % mutatie.pk)
            self._verwerk_mutatie_afmelden(mutatie)

        elif code == KALENDER_MUTATIE_KORTING:
            self.stdout.write('[INFO] Verwerk mutatie %s: Korting' % mutatie.pk)
            self._verwerk_mutatie_korting(mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = KalenderMutatie.objects.latest('pk')
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste KalenderMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (KalenderMutatie
                    .objects
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (KalenderMutatie
                    .objects
                    .all())

        mutatie_pks = qset.values_list('pk', flat=True)

        self._hoogste_mutatie_pk = mutatie_latest.pk

        did_useful_work = False
        for pk in mutatie_pks:
            # LET OP: we halen de records hier 1 voor 1 op
            #         zodat we verse informatie hebben inclusief de vorige mutatie
            #         en zodat we 1 plek hebben voor select/prefetch
            mutatie = (KalenderMutatie
                       .objects
                       .select_related('inschrijving',
                                       'inschrijving__wedstrijd',
                                       'inschrijving__sessie',
                                       'inschrijving__sporterboog',
                                       'inschrijving__sporterboog__sporter',
                                       'inschrijving__koper')
                       .get(pk=pk))

            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste KalenderMutatie pk is %s' % self._hoogste_mutatie_pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = KalenderMutatie.objects.count()
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

    def handle(self, *args, **options):

        self._set_stop_time(**options)

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_mutaties()
        except django.db.utils.DataError as exc:        # pragma: no cover
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
