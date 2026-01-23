# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om CompetitieMutatie records te verwerken, zodat concurrency voorkomen kan worden. """

from django.db import connection
from django.conf import settings
from django.db.utils import DataError, OperationalError, IntegrityError, DEFAULT_DB_ALIAS
from django.core.management.base import BaseCommand
from Competitie.models import CompetitieMutatie, CompetitieTaken
from Competitie.operations import competitie_hanteer_overstap_sporter
from CompLaagRegio.operations.verwerk_mutaties import VerwerkCompLaagRegioMutaties
from CompKampioenschap.operations import VerwerkCompKampMutaties
from CompBeheer.operations.verwerk_mutaties import VerwerkCompBeheerMutaties
from Mailer.operations import mailer_notify_internal_error
from Site.core.background_sync import BackgroundSync
import traceback
import datetime
import logging
import sys

my_logger = logging.getLogger('MH.competitie_mutaties')


class Command(BaseCommand):
    help = "Verwerk competitie mutaties"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        # stdout is hier niet beschikbaar in test omgeving
        # (komt binnen via cmdline optie)
        self.verwerk_mutaties = list()      # VerwerkCompLaag[Regio|Rayon|Bond]Mutaties(self.stdout)

        self.stop_at = datetime.datetime.now()

        self.taken = CompetitieTaken.objects.first()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__COMPETITIE_MUTATIES)
        self._count_ping = 0

    def _out_error(self, msg):
        self.stdout.write('[ERROR] {competitie_mutaties} %s' % msg)

    def _out_debug(self, msg):
        self.stdout.write('[DEBUG] {competitie_mutaties} %s' % msg)

    def _out_info(self, msg):
        self.stdout.write('[INFO] {competitie_mutaties} %s' % msg)

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices=(1, 2, 5, 7, 10, 15, 20, 30, 45, 60),
                            help="Maximum aantal minuten actief blijven")
        parser.add_argument('--stop_exactly', type=int, default=None, choices=range(60),
                            help="Stop op deze minuut")
        parser.add_argument('--quick', action='store_true')                 # for testing
        parser.add_argument('--use-test-database', action='store_true')     # for testing

    def _verwerk_in_achtergrond(self):
        # vraag elk van de verwerkers om een stukje werk in de achtergrond te doen
        for plugin in self.verwerk_mutaties:
            plugin.verwerk_in_achtergrond()
        # for

    def _verwerk_mutatie(self, mutatie):
        # vraag elk van de mutatie verwerkers om de mutatie af te handelen
        done = False
        for plugin in self.verwerk_mutaties:
            if not done:
                done = plugin.verwerk(mutatie)
        # for

        if not done:
            self._out_error('Onbekende mutatie code %s in pk=%s' % (mutatie.mutatie, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = CompetitieMutatie.objects.latest('pk')
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self.taken.hoogste_mutatie:
            # gebruik deze informatie om te filteren
            self._out_info('vorige hoogste CompetitieMutatie pk is %s' % self.taken.hoogste_mutatie.pk)
            qset = (CompetitieMutatie
                    .objects
                    .filter(pk__gt=self.taken.hoogste_mutatie.pk))
        else:
            qset = (CompetitieMutatie
                    .objects
                    .all())

        qset = qset.filter(is_verwerkt=False)
        mutatie_pks = qset.values_list('pk', flat=True)

        self.taken.hoogste_mutatie = mutatie_latest
        self.taken.save(update_fields=['hoogste_mutatie'])

        did_useful_work = False
        for pk in mutatie_pks:
            # LET OP: we halen de records hier 1 voor 1 op
            #         zodat we verse informatie hebben inclusief de vorige mutatie
            mutatie = (CompetitieMutatie
                       .objects
                       .select_related('competitie',
                                       'regiocompetitie',
                                       'regiocompetitie__competitie',
                                       'kampioenschap',
                                       'kampioenschap__competitie',
                                       'indiv_klasse',
                                       'team_klasse',
                                       'deelnemer',
                                       'deelnemer__kampioenschap',
                                       'deelnemer__sporterboog__sporter',
                                       'deelnemer__indiv_klasse')
                       .get(pk=pk))
            if not mutatie.is_verwerkt:     # pragma: no branch
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self._out_info('nieuwe hoogste CompetitieMutatie pk is %s' % self.taken.hoogste_mutatie.pk)

            klaar = datetime.datetime.now()
            self._out_info('Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self._out_debug('tick')
            new_count = CompetitieMutatie.objects.count()
            if new_count != mutatie_count:
                mutatie_count = new_count
                self._verwerk_nieuwe_mutaties()
                now = datetime.datetime.now()
            else:
                self._verwerk_in_achtergrond()

            # wacht 3 seconden voordat we opnieuw in de database kijken
            # het wachten kan onderbroken worden door een ping, als er een nieuwe mutatie toegevoegd is
            secs = (self.stop_at - now).total_seconds()
            if secs > 1:                                    # pragma: no branch
                timeout = min(3.0, secs)
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
                self._out_info('Calculated stop at is %s' % stop_at_exact)
                if stop_at_exact < self.stop_at:
                    # run duration passes the requested stop minute
                    self.stop_at = stop_at_exact

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self._out_info('Taak loopt tot %s' % self.stop_at.strftime('%Y-%m-%d %H:%M:%S'))

    def handle(self, *args, **options):

        if options['use_test_database']:                    # pragma: no cover
            # voor gebruik tijdens browser tests
            connection.close()
            test_database_name = "test_" + settings.DATABASES[DEFAULT_DB_ALIAS]["NAME"]
            settings.DATABASES[DEFAULT_DB_ALIAS]["NAME"] = test_database_name
            connection.settings_dict["NAME"] = test_database_name

        self.verwerk_mutaties = [
            VerwerkCompBeheerMutaties(self.stdout, my_logger),
            VerwerkCompLaagRegioMutaties(self.stdout, my_logger),
            VerwerkCompKampMutaties(self.stdout, my_logger),
            # VerwerkCompLaagRayonMutaties(self.stdout, my_logger),
            # VerwerkCompLaagBondMutaties(self.stdout, my_logger),
        ]

        self._set_stop_time(**options)

        # bij opstarten van de taak, doorloop alle mutaties die nog niet verwerkt zijn
        self.taken.hoogste_mutatie = None

        competitie_hanteer_overstap_sporter(self.stdout)

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_mutaties()
        except (DataError, OperationalError, IntegrityError) as exc:  # pragma: no cover
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

            tb_msg_start = 'Onverwachte fout tijdens competitie_mutaties\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self._out_error('Onverwachte fout (%s): %s' % (type(exc), str(exc)))
            self.stdout.write('Traceback:')
            self.stdout.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            mailer_notify_internal_error(tb_msg)

        self._out_debug('Aantal pings ontvangen: %s' % self._count_ping)

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
