# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from BasisTypen.definities import SCHEIDS_NIET
from Locatie.models import Locatie, Reistijd
from Sporter.models import Sporter
import googlemaps
import datetime
import pprint


class Command(BaseCommand):

    help = "Reistijd tabel bijwerken"

    def __init__(self):
        super().__init__()

        self._gmaps = None

        # aankomst op de wedstrijdlocatie zetten we standaard op een zaterdag in de toekomst om 08:00
        date = timezone.localtime(timezone.now())
        date += datetime.timedelta(days=60)
        while date.weekday() != 5:      # 5 = zaterdag
            date += datetime.timedelta(days=1)
        # while
        self._future_saturday_0800 = date

    def _connect_gmaps(self):
        # TODO: error handling
        if settings.GMAPS_API:
            self.stdout.write('[INFO] Using server URL %s' % repr(settings.GMAPS_API))
            self._gmaps = googlemaps.Client(key=settings.GMAPS_KEY, base_url=settings.GMAPS_API)
        else:
            self._gmaps = googlemaps.Client(key=settings.GMAPS_KEY)

    def _get_adres_lat_lon(self, adres):

        # TODO: error handling
        results = self._gmaps.geocode(adres, region='nl')

        # geocode return a list of results
        if len(results) < 1:
            self.stderr.write('[WARNING] No results from geocode for adres=%s' % repr(adres))
            return None, None

        try:
            result = results[0]

            geometry = result['geometry']

            location = geometry['location']
            # self.stdout.write('location: %s' % repr(location))

            lat = location['lat']
            lon = location['lng']

        except (KeyError, IndexError) as exc:
            self.stderr.write('[WARNING] Could not extract lat/lng from geocode results %s' % repr(results))
            return None, None

        return lat, lon

    def _reistijd_met_auto(self, vanaf_lat_lon, naar_lat_lon):
        # self.stdout.write('[DEBUG] vanaf_lat_lon=%s' % repr(vanaf_lat_lon))
        # self.stdout.write('[DEBUG] naar_lat_lon=%s' % repr(naar_lat_lon))
        try:
            results = self._gmaps.directions(
                                origin=vanaf_lat_lon,
                                destination=naar_lat_lon,
                                mode="driving",
                                units="metric",
                                alternatives=False,
                                arrival_time=self._future_saturday_0800)
        except googlemaps.exceptions.ApiError as exc:
            self.stdout.write('[ERROR] Failed to get directions from %s to %s: error %s' % (
                                repr(vanaf_lat_lon), repr(naar_lat_lon), str(exc)))
            return 16 * 60      # geef een gek getal terug wat om aandacht vraagt

        try:
            # pp = pprint.PrettyPrinter()
            # pp.pprint(results)
            result = results[0]      # maximaal 1 resultaat omdat alternatives = False
            leg = result['legs'][0]
            # del leg['steps']
            # pp = pprint.PrettyPrinter()
            # pp.pprint(leg)
            duration = leg['duration']
            secs = duration['value']
        except (KeyError, IndexError):
            self.stdout.write('[ERROR] Failed to extract minutes from %s' % repr(results))
            mins = 17 * 60      # geef een gek getal terug wat om aandacht vraagt
        else:
            mins = int(round(secs / 60, 0))
            self.stdout.write('[INFO] Duration %s is %s seconds is %s minutes' % (repr(duration['text']), secs, mins))

        return mins

    def _update_locaties_uit_crm(self):
        # adressen uit het CRM aanvullen met lat/lon
        for locatie in (Locatie
                        .objects
                        .filter(adres_uit_crm=True,
                                adres_lat='')
                        .exclude(zichtbaar=False)):

            adres_lat, adres_lon = self._get_adres_lat_lon(locatie.adres)

            if adres_lat and adres_lon:
                # afkappen voor storage
                # 5 decimalen geeft ongeveer 1 meter nauwkeurigheid
                locatie.adres_lat = "%2.6f" % adres_lat
                locatie.adres_lon = "%2.6f" % adres_lon
            else:
                self.stderr.write('[WARNING] No lat/lon for locatie pk=%s' % locatie.pk)

                # voorkom dat we keer op keer blijven proberen
                locatie.adres_lat = '?'
                locatie.adres_lon = '?'

            locatie.save(update_fields=['adres_lat', 'adres_lon'])
        # for

    def _update_locaties_overig(self):
        # adressen van overige locaties aanvullen met lat/lon
        for locatie in (Locatie
                        .objects
                        .filter(adres_uit_crm=False,
                                adres_lat='')
                        .exclude(zichtbaar=False)):

            if locatie.adres.strip() not in ('', '(diverse)'):

                adres_lat, adres_lon = self._get_adres_lat_lon(locatie.adres)

                if adres_lat and adres_lon:
                    # afkappen voor storage
                    # 5 decimalen geeft ongeveer 1 meter nauwkeurigheid
                    locatie.adres_lat = "%2.6f" % adres_lat
                    locatie.adres_lon = "%2.6f" % adres_lon
                else:
                    self.stderr.write('[WARNING] Geen lat/lon for locatie pk=%s met adres %s' % (
                                        locatie.pk, repr(locatie.adres)))

                    # voorkom dat we keer op keer blijven proberen
                    locatie.adres_lat = '?'
                    locatie.adres_lon = '?'

                locatie.save(update_fields=['adres_lat', 'adres_lon'])
        # for

    def _update_scheids(self):
        # zet voor alle scheidsrechters het postadres om in een lat/lon
        # bij wijziging adres worden lat/lon leeggemaakt.
        for sporter in (Sporter
                        .objects
                        .exclude(scheids=SCHEIDS_NIET)
                        .filter(adres_lat='')):

            adres = sporter.postadres_1
            if sporter.postadres_2:
                adres += ", "
                adres += sporter.postadres_2
            if sporter.postadres_3:
                adres += ", "
                adres += sporter.postadres_3

            adres_lat, adres_lon = self._get_adres_lat_lon(adres)

            if adres_lat and adres_lon:
                # afkappen voor storage
                # 5 decimalen geeft ongeveer 1 meter nauwkeurigheid
                sporter.adres_lat = "%2.6f" % adres_lat
                sporter.adres_lon = "%2.6f" % adres_lon
            else:
                self.stderr.write('[WARNING] Geen lat/lon for sporter %s met adres %s' % (
                                    sporter.lid_nr, repr(adres)))

                # voorkom dat we keer op keer blijven proberen
                sporter.adres_lat = '?'
                sporter.adres_lon = '?'

            sporter.save(update_fields=['adres_lat', 'adres_lon'])
        # for

    def _update_reistijd(self):

        today = timezone.localtime(timezone.now()).date()

        for reistijd in Reistijd.objects.filter(reistijd_min=0):

            vanaf_lat_lon = "%s, %s" % (reistijd.vanaf_lat, reistijd.vanaf_lon)
            naar_lat_lon = "%s, %s" % (reistijd.naar_lat, reistijd.naar_lon)

            mins = self._reistijd_met_auto(vanaf_lat_lon, naar_lat_lon)

            reistijd.reistijd_min = mins
            reistijd.op_datum = today

            reistijd.save(update_fields=['reistijd_min', 'op_datum'])
        # for

    def handle(self, *args, **options):

        self._connect_gmaps()

        self._update_scheids()
        self._update_locaties_uit_crm()
        self._update_locaties_overig()
        self._update_reistijd()


# end of file
