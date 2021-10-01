# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# download op verzoek een bondspas
# bij elke opstart wordt de cache opgeschoond

from django.conf import settings
from django.db.models import F
from django.core.management.base import BaseCommand
from Bondspas.models import (Bondspas, BONDSPAS_STATUS_OPHALEN,  BONDSPAS_STATUS_BEZIG,
                             BONDSPAS_STATUS_FAIL, BONDSPAS_STATUS_AANWEZIG, BONDSPAS_STATUS_VERWIJDERD)
from Overig.background_sync import BackgroundSync
import django.db.utils
import datetime
import requests
import os


class Command(BaseCommand):
    help = "Competitie mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._stop_at = datetime.datetime.now()
        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)
        self._count_ping = 0

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _scrub_bondspas_cache(self):
        """ Als de bondspas cache bijna vol zit (meer dan 90% in gebruik),
            verwijder dan de oudste passen.
        """
        self.stderr.write('[TODO] Implement bondspas cache scrubbing')

    def _bondspas_ophalen(self, bondspas):
        """ Haal een bondspas op """

        self.stdout.write('[INFO] Bondspas ophalen voor lid %s' % bondspas.lid_nr)

        # zet de status om aan te geven dat we bezig gaan
        bondspas.status = BONDSPAS_STATUS_BEZIG
        # bepaal de filename
        bondspas.filename = 'bondspas_%s.pdf' % bondspas.lid_nr
        bondspas.save(update_fields=['filename', 'status'])

        if len(bondspas.log) > 0 and bondspas.log[-1] != '\n':
            bondspas.log += '\n'

        headers = {'User-Agent': 'NHBApps-bondspas-downloader'}
        url = settings.BONDSPAS_DOWNLOAD_URL % bondspas.lid_nr
        try:
            with requests.get(url, headers=headers, stream=True) as req:        # with = automatisch vrij geven
                # header zijn nu ontvangen
                self.stdout.write('[DEBUG] Headers: %s' % req.headers)

                # controleer de lengte
                try:
                    pdf_len = int(req.headers['Content-length'])
                except (KeyError, ValueError):
                    self.stderr.write('[ERROR] Missing header: Content-length')
                    now = datetime.datetime.now()
                    bondspas.status = BONDSPAS_STATUS_FAIL
                    bondspas.opnieuw_proberen_na = now + datetime.timedelta(minutes=settings.BONDSPAS_RETRY_MINUTES)
                    bondspas.log += '[%s] Fout tijdens ophalen  (geen content-length)\n' % now
                    bondspas.save(update_fields=['status', 'log', 'opnieuw_proberen_na'])
                else:
                    if pdf_len > (settings.BONDSPAS_MAX_SIZE_PDF_KB * 1024):
                        now = datetime.datetime.now()
                        bondspas.status = BONDSPAS_STATUS_FAIL
                        bondspas.opnieuw_proberen_na = now + datetime.timedelta(minutes=settings.BONDSPAS_RETRY_MINUTES)
                        bondspas.log += '[%s] Fout tijdens ophalen: pas is te groot (%s bytes)\n' % (now, pdf_len)
                        bondspas.save(update_fields=['status', 'log', 'opnieuw_proberen_na'])
                    else:
                        # maak het bestand aan en ontvang deze
                        fpath = os.path.join(settings.BONDSPAS_CACHE_PATH, bondspas.filename)
                        try:
                            with open(fpath, 'wb') as dest:                     # with = automatisch sluiten
                                # in 1x ophalen en opslaan
                                dest.write(req.content)
                            # with
                        except IOError as exc:
                            self.stderr.write('[ERROR] Can bestand niet opslaan: %s' % str(exc))
                            now = datetime.datetime.now()
                            bondspas.status = BONDSPAS_STATUS_FAIL
                            bondspas.opnieuw_proberen_na = now + datetime.timedelta(minutes=settings.BONDSPAS_RETRY_MINUTES)
                            bondspas.log += '[%s] Fout tijdens ophalen (zie logfile)\n' % now
                            bondspas.save(update_fields=['status', 'log', 'opnieuw_proberen_na'])
                        else:
                            # ophalen is gelukt
                            bondspas.status = BONDSPAS_STATUS_AANWEZIG
                            bondspas.log += '[%s] Ophalen is gelukt\n' % datetime.datetime.now()
                            bondspas.aantal_keer_opgehaald += 1
                            bondspas.save(update_fields=['status', 'log', 'aantal_keer_opgehaald'])
            # with
        except requests.exceptions.RequestException as exc:
            self.stderr.write('[ERROR] Onverwachte fout: %s' % str(exc))
            now = datetime.datetime.now()
            bondspas.status = BONDSPAS_STATUS_FAIL
            bondspas.opnieuw_proberen_na = now + datetime.timedelta(minutes=settings.BONDSPAS_RETRY_MINUTES)
            bondspas.log += '[%s] Onverwachte fout (zie logfile)\n' % now
            bondspas.save(update_fields=['status', 'log', 'opnieuw_proberen_na'])

    def _monitor_ophaal_verzoeken(self):
        """ Wacht op een verzoek om een bondspas op te halen en voer deze uit, totdat de tijd op is
        """
        # monitor voor nieuwe verzoeken
        now = datetime.datetime.now()
        while now < self._stop_at:                   # pragma: no branch
            self.stdout.write('tick')

            for bondspas in Bondspas.objects.filter(status=BONDSPAS_STATUS_OPHALEN):
                if bondspas.opnieuw_proberen_na is None or now > bondspas.opnieuw_proberen_na:
                    self._bondspas_ophalen(bondspas)

                now = datetime.datetime.now()
            # for

            # wacht 5 seconden voordat we opnieuw in de database kijken
            # het wachten kan onderbroken worden door een ping, als er een nieuwe mutatie toegevoegd is
            secs = (self._stop_at - now).total_seconds()
            if secs > 1:                                    # pragma: no branch
                timeout = min(5.0, secs)
                if self._sync.wait_for_ping(timeout):       # pragma: no branch
                    self._count_ping += 1                   # pragma: no cover
            else:
                # near the end
                break       # from the while

            now = datetime.datetime.now()
        # while

    def _set_stop_time(self, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        # trek er nog eens 15 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']

        self._stop_at = (datetime.datetime.now()
                         + datetime.timedelta(minutes=duration)
                         - datetime.timedelta(seconds=15))

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self._stop_at = (datetime.datetime.now()
                             + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self._stop_at))

    def handle(self, *args, **options):

        if not os.path.isdir(settings.BONDSPAS_CACHE_PATH):
            self.stderr.write('[ERROR] Bondspas cache directory bestaat niet: %s' % settings.BONDSPAS_CACHE_PATH)
            return

        self._set_stop_time(**options)

        self._scrub_bondspas_cache()

        # vang generieke fouten af
        try:
            self._monitor_ophaal_verzoeken()
        except django.db.utils.DataError as exc:        # pragma: no coverage
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
        except KeyboardInterrupt:                       # pragma: no coverage
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
