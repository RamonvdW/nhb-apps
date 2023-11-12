# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.conf import settings
from django.core.management.base import BaseCommand
from Locatie.models import Locatie
import googlemaps

MAX_REQUESTS = 100


class Command(BaseCommand):

    help = "Reistijd tabel bijwerken"

    def __init__(self):
        super().__init__()

        self._gmaps = None

    def _connect_gmaps(self):
        # TODO: error handling
        self._gmaps = googlemaps.Client(key=settings.MAPS_API_KEY)

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
                    self.stderr.write(
                        '[WARNING] No lat/lon for locatie pk=%s met adres %s' % (locatie.pk, repr(locatie.adres)))

                    # voorkom dat we keer op keer blijven proberen
                    locatie.adres_lat = '?'
                    locatie.adres_lon = '?'

                locatie.save(update_fields=['adres_lat', 'adres_lon'])
        # for

    def handle(self, *args, **options):

        self._connect_gmaps()

        self._update_locaties_uit_crm()
        self._update_locaties_overig()
        #self._update_reistijd()


# end of file
