# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via KalenderMutatie
"""

from django.conf import settings
from django.utils import timezone
from django.db.models import F
from django.core.management.base import BaseCommand
from Kalender.models import KalenderMutatie
from Overig.background_sync import BackgroundSync
from Taken.taken import maak_taak
import django.db.utils
import traceback
import datetime
import sys

VOLGORDE_PARKEER = 22222        # hoog en past in PositiveSmallIntegerField


class Command(BaseCommand):
    help = "Kalender mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.code

        if code == MUTATIE_COMPETITIE_OPSTARTEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Competitie opstarten' % mutatie.pk)
            self._verwerk_mutatie_competitie_opstarten()

        elif code == MUTATIE_AG_VASTSTELLEN_18M:
            self.stdout.write('[INFO] Verwerk mutatie %s: AG vaststellen 18m' % mutatie.pk)
            aanvangsgemiddelden_vaststellen_voor_afstand(18)

        elif code == MUTATIE_AG_VASTSTELLEN_25M:
            self.stdout.write('[INFO] Verwerk mutatie %s: AG vaststellen 25m' % mutatie.pk)
            aanvangsgemiddelden_vaststellen_voor_afstand(25)

        elif code == MUTATIE_INITIEEL:
            self.stdout.write('[INFO] Verwerk mutatie %s: initieel' % mutatie.pk)
            self._verwerk_mutatie_initieel(mutatie.deelcompetitie.competitie, mutatie.deelcompetitie.laag)

        elif code == MUTATIE_CUT:
            self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste limiet (cut)' % mutatie.pk)
            if mutatie.indiv_klasse:
                self._verwerk_mutatie_cut_indiv(mutatie.deelcompetitie, mutatie.indiv_klasse,
                                                mutatie.cut_oud, mutatie.cut_nieuw)
            else:
                self._verwerk_mutatie_cut_team(mutatie.deelcompetitie, mutatie.team_klasse,
                                               mutatie.cut_oud, mutatie.cut_nieuw)

        elif code == MUTATIE_AANMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden' % mutatie.pk)
            self._verwerk_mutatie_aanmelden(mutatie.deelnemer)

        elif code == MUTATIE_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden' % mutatie.pk)
            self._verwerk_mutatie_afmelden_indiv(mutatie.deelnemer)

        elif code == MUTATIE_TEAM_RONDE:
            self.stdout.write('[INFO] Verwerk mutatie %s: team ronde' % mutatie.pk)
            self._verwerk_mutatie_team_ronde(mutatie.deelcompetitie)

        elif code == MUTATIE_AFSLUITEN_REGIOCOMP:
            self.stdout.write('[INFO] Verwerk mutatie %s: afsluiten regiocompetitie' % mutatie.pk)
            self._verwerk_mutatie_afsluiten_regiocomp(mutatie.competitie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s door %s (pk=%s)' % (code, mutatie.door, mutatie.pk))

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
            mutatie = (KalenderMutatie
                       .objects
                       .select_related('competitie',
                                       'deelcompetitie',
                                       'indiv_klasse',
                                       'team_klasse',
                                       'deelnemer',
                                       'deelnemer__deelcompetitie',
                                       'deelnemer__sporterboog__sporter',
                                       'deelnemer__indiv_klasse')
                       .get(pk=pk))
            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste KampioenschapMutatie pk is %s' % self._hoogste_mutatie_pk)

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
