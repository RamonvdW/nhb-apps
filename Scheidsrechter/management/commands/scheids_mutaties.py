# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via ScheidsMutatie
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import DataError, OperationalError, IntegrityError
from BasisTypen.definities import SCHEIDS_NIET, SCHEIDS_VERENIGING
from Locatie.models import Reistijd
from Overig.background_sync import BackgroundSync
from Scheidsrechter.definities import SCHEIDS_MUTATIE_BESCHIKBAARHEID_OPVRAGEN
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsMutatie
from Sporter.models import Sporter
import traceback
import datetime
import sys


class Command(BaseCommand):
    help = "Scheidsrechter mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__SCHEIDS_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _reistijd_opvragen(self, locatie, sporter):
        """ vraag de reistijd op tussen de postcode van de sporter/scheidsrechter en de locatie """

        # nieuwe verzoeken worden door het management commando "reistijd berekenen" verwerkt
        if sporter.adres_lat and sporter.adres_lon:
            Reistijd.objects.get_or_create(
                                vanaf_lat=sporter.adres_lat,
                                vanaf_lon=sporter.adres_lon,
                                naar_lat=locatie.adres_lat,
                                naar_lon=locatie.adres_lon)
        else:
            self.stdout.write('[WARNING] Nog geen lat/lon voor sporter %s' % sporter.lid_nr)

    def _verwerk_mutatie_beschikbaarheid_opvragen(self, mutatie):
        wedstrijd = mutatie.wedstrijd
        self.stdout.write('[INFO] Beschikbaarheid %s SR opvragen voor wedstrijd %s' % (wedstrijd.aantal_scheids,
                                                                                       wedstrijd))

        vraag = list()
        aantal_dagen = (wedstrijd.datum_einde - wedstrijd.datum_begin).days + 1
        for dag_nr in range(aantal_dagen):
            _, is_new = (WedstrijdDagScheidsrechters
                         .objects
                         .get_or_create(wedstrijd=wedstrijd,
                                        dag_offset=dag_nr))

            if is_new:
                # voor deze dag een verzoek versturen
                datum = wedstrijd.datum_begin + datetime.timedelta(days=dag_nr)
                vraag.append(datum)
        # for

        # doorloop alle scheidsrechters
        qset = Sporter.objects.exclude(scheids=SCHEIDS_NIET)

        # alleen een hoofdscheidsrechter nodig? --> dan niet SR3 vragen
        if wedstrijd.aantal_scheids <= 1:
            qset = qset.exclude(scheids=SCHEIDS_VERENIGING)

        for sporter in qset:

            # reisafstand laten berekenen voor deze SR
            self._reistijd_opvragen(wedstrijd.locatie, sporter)

            # TODO: stuur e-mail naar SR
        # for

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.mutatie

        if code == SCHEIDS_MUTATIE_BESCHIKBAARHEID_OPVRAGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Beschikbaarheid opvragen' % mutatie.pk)
            self._verwerk_mutatie_beschikbaarheid_opvragen(mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        try:
            mutatie_latest = ScheidsMutatie.objects.latest('pk')
        except ScheidsMutatie.DoesNotExist:
            # alle mutatie records zijn verwijderd
            return
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste BetaalMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (ScheidsMutatie
                    .objects
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (ScheidsMutatie
                    .objects
                    .all())         # deferred

        mutatie_pks = qset.order_by('pk').values_list('pk', flat=True)     # deferred

        self._hoogste_mutatie_pk = mutatie_latest.pk

        did_useful_work = False
        for pk in mutatie_pks:
            # we halen de records hier 1 voor 1 op
            # zodat we verse informatie hebben inclusief de vorige mutatie
            # en zodat we 1 plek hebben voor select/prefetch
            mutatie = (ScheidsMutatie
                       .objects
                       .select_related('wedstrijd',
                                       'wedstrijd__locatie')
                       .get(pk=pk))

            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste ScheidsMutatie pk is %s' % self._hoogste_mutatie_pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = ScheidsMutatie.objects.count()
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
