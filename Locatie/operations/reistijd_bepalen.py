# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.conf import settings
from django.utils import timezone
from BasisTypen.definities import SCHEIDS_NIET
from Locatie.models import WedstrijdLocatie, Reistijd
from Sporter.models import Sporter
from google.auth.api_key import Credentials
from google.maps.routing_v2 import RoutesClient, RouteTravelMode, Units, RoutingPreference
import googlemaps
import datetime

TEST_TRIGGER = '##TEST##'


class ReistijdBepaler(object):

    """ Bereken de reistijd tussen twee locaties met Google Maps Routing v2 """

    def __init__(self, stdout, stderr, verzoeken_grens):
        self.stdout = stdout
        self.stderr = stderr

        self._client: RoutesClient | None = None
        self._gmaps: googlemaps.Client | None = None
        self.verzoeken_teller = 0
        self.verzoeken_grens = verzoeken_grens

    def _connect_gmaps(self):
        """ Init de google maps library
            Return: True  = success
                    False = failure
        """

        if not self._gmaps:
            options = {'key': settings.GOOGLEMAPS_API_KEY}

            if settings.GOOGLEMAPS_API_URL:      # pragma: no branch
                self.stdout.write('[INFO] Server URL %s' % repr(settings.GOOGLEMAPS_API_URL))
                options['base_url'] = settings.GOOGLEMAPS_API_URL

            try:
                self._gmaps = googlemaps.Client(**options)
            except Exception as exc:
                self.stderr.write('[ERROR] Fout tijdens gmaps init: %s' % str(exc))
                return False

        if not self._client:
            creds = None
            options = {}
            transport = None

            if settings.GOOGLEMAPS_API_URL:  # pragma: no branch
                # verification environment
                # redirect (URL) does not work, so we provide a RoutesTransport implementation
                from Locatie.test_tools.websim_routes import get_routes_transport
                transport = get_routes_transport()
            else:
                creds = Credentials(settings.GOOGLEMAPS_API_KEY)

            try:
                self._client = RoutesClient(credentials=creds, client_options=options, transport=transport)
            except Exception as exc:
                self.stderr.write('[ERROR] Fout tijdens RoutesClient init: %s' % str(exc))
                return False

        return True

    def _get_adres_lat_lon(self, adres):
        # vervang newlines
        adres = adres.replace('\r\n', '; ')
        adres = adres.replace('\n', '; ')

        try:
            results = self._gmaps.geocode(adres, region='nl')
        except (googlemaps.exceptions.ApiError, googlemaps.exceptions.HTTPError) as exc:
            self.stderr.write('[ERROR] Fout van gmaps geocode: %s' % str(exc))
            raise ResourceWarning()

        # geocode returns a list of results
        if len(results) < 1:
            self.stderr.write('[WARNING] Geen geocode resultaten voor adres=%s' % repr(adres))
            return None, None

        try:
            result = results[0]

            geometry = result['geometry']

            location = geometry['location']
            # self.stdout.write('location: %s' % repr(location))

            lat = location['lat']
            lon = location['lng']

        except (KeyError, IndexError):
            self.stderr.write('[WARNING] Kan geen lat/lng halen uit geocode results %s' % repr(results))
            raise ResourceWarning()

        return lat, lon

    @staticmethod
    def _lat_lon_to_api(lat, lon) -> dict:
        if lat == lon == TEST_TRIGGER:
            raise SystemError('test')

        d = {
            "location": {
                "lat_lng": {
                    "latitude": float(lat),
                    "longitude": float(lon),
                }
            }
        }
        return d

    def _reistijd_met_auto(self, vanaf_lat_lon, naar_lat_lon):
        request = {
            "origin": vanaf_lat_lon,
            "destination": naar_lat_lon,
            "travel_mode": RouteTravelMode.DRIVE,
            "units": Units.METRIC,
            # "arrival_time": self._future_saturday_0800.isoformat(),       # includes date
            "compute_alternative_routes": False,
            "routing_preference": RoutingPreference.TRAFFIC_AWARE_OPTIMAL,  # anders geen veerboot!
            # "language_code": "NL",
            "route_modifiers": {
                "avoid_ferries": False,
                "avoid_highways": False,
                "avoid_tolls": False,
            }
        }

        try:
            metadata = [
                ('x-goog-fieldmask', 'routes.static_duration'),
            ]
            # self.stdout.write('[DEBUG] compute routes request: %s' % repr(request))
            self.verzoeken_teller += 1
            response = self._client.compute_routes(request, metadata=metadata)
        except Exception as exc:
            self.stderr.write('[ERROR] Fout van routing_v2 (%s)' % str(exc))
            self.stdout.write('[DEBUG] compute routes request was: %s' % repr(request))
            mins = 16 * 60      # geef een gek getal (16 uur) terug wat om aandacht vraagt
        else:
            # self.stdout.write('[DEBUG] response=%s' % repr(response))

            try:
                secs = response.routes[0].static_duration.seconds
            except (KeyError, IndexError):
                self.stderr.write('[ERROR] Onvolledig routes antwoord: %s' % repr(response))
                self.stdout.write('[DEBUG] compute routes request was: %s' % repr(request))
                mins = 17 * 60      # geef een gek getal (17 uur) terug wat om aandacht vraagt
            else:
                mins = int(round(secs / 60, 0))
                # self.stdout.write('[DEBUG] Reistijd %s seconden wordt %s minuten' % (secs, mins))

        return mins

    def _update_locaties(self):
        # adressen van de locaties aanvullen met lat/lon
        for locatie in (WedstrijdLocatie
                        .objects
                        .filter(adres_lat='')
                        .exclude(zichtbaar=False)):

            if locatie.adres.strip() not in ('', '(diverse)'):
                try:
                    adres_lat, adres_lon = self._get_adres_lat_lon(locatie.adres)
                except ResourceWarning:
                    # silently ignore
                    pass
                else:
                    if adres_lat and adres_lon:
                        # afkappen voor storage
                        # 5 decimalen geeft ongeveer 1 meter nauwkeurigheid
                        locatie.adres_lat = "%2.6f" % adres_lat
                        locatie.adres_lon = "%2.6f" % adres_lon
                    else:
                        self.stderr.write('[WARNING] Geen lat/lon voor locatie pk=%s met adres %s' % (
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
                        .filter(adres_lat='',
                                is_actief_lid=True)):

            adres = sporter.postadres_1
            if sporter.postadres_2:
                adres += ", "
                adres += sporter.postadres_2
            if sporter.postadres_3:
                adres += ", "
                adres += sporter.postadres_3

            try:
                adres_lat, adres_lon = self._get_adres_lat_lon(adres)
            except ResourceWarning:
                # silently ignore
                pass
            else:
                if adres_lat and adres_lon:
                    # afkappen voor storage
                    # 5 decimalen geeft ongeveer 1 meter nauwkeurigheid
                    sporter.adres_lat = "%2.6f" % adres_lat
                    sporter.adres_lon = "%2.6f" % adres_lon
                else:
                    self.stderr.write('[WARNING] Geen lat/lon voor sporter %s met adres %s' % (
                                        sporter.lid_nr, repr(adres)))

                    # voorkom dat we keer op keer blijven proberen
                    sporter.adres_lat = '?'
                    sporter.adres_lon = '?'

                sporter.save(update_fields=['adres_lat', 'adres_lon'])
        # for

    def _update_locaties_fallback(self):
        # kijk of er een handmatige fallback is
        for locatie in (WedstrijdLocatie
                        .objects
                        .filter(adres_lat='?')
                        .exclude(zichtbaar=False)):

            adres = locatie.adres.upper()
            adres = adres.replace('\r\n', ' ')
            adres = adres.replace('\n', ' ')
            adres = adres.replace('  ', ' ')

            try:
                adres_lat, adres_lon = settings.GEOCODE_FALLBACK[adres]
            except KeyError:
                adres_lat, adres_lon = None, None

            if isinstance(adres_lat, float) and isinstance(adres_lon, float):
                # afkappen voor storage
                # 5 decimalen geeft ongeveer 1 meter nauwkeurigheid
                locatie.adres_lat = "%2.6f" % adres_lat
                locatie.adres_lon = "%2.6f" % adres_lon
                locatie.save(update_fields=['adres_lat', 'adres_lon'])
            else:
                self.stdout.write('[WARNING] Geen fallback voor locatie pk=%s met adres %s' % (locatie.pk, repr(adres)))
        # for

    def _update_reistijd(self):

        today = timezone.localtime(timezone.now()).date()

        for reistijd in Reistijd.objects.filter(reistijd_min=0):

            if not reistijd.is_compleet():
                self.stdout.write('[WARNING] Reistijd met pk=%s is niet compleet; skipping' % reistijd.pk)
                continue

            try:
                vanaf_lat_lon = self._lat_lon_to_api(reistijd.vanaf_lat, reistijd.vanaf_lon)
                naar_lat_lon = self._lat_lon_to_api(reistijd.naar_lat, reistijd.naar_lon)
            except ValueError:
                self.stdout.write('[WARNING] Fout in lat/lon (geen float?) voor reistijd pk=%s' % reistijd.pk)
            else:
                mins = self._reistijd_met_auto(vanaf_lat_lon, naar_lat_lon)

                reistijd.reistijd_min = mins
                reistijd.op_datum = today

                reistijd.save(update_fields=['reistijd_min', 'op_datum'])

            # begrens het aantal verzoeken per keer
            if self.verzoeken_teller >= self.verzoeken_grens:
                self.stdout.write('[WARNING] Limit van %s verzoeken per keer bereikt' % self.verzoeken_grens)
                break
        # for

    def _refresh_reistijd(self):
        # na 6 maanden verversen we de reistijd

        today = timezone.localtime(timezone.now()).date()
        oud = today - datetime.timedelta(days=183)

        for reistijd in Reistijd.objects.filter(op_datum__lt=oud):

            if not reistijd.is_compleet():
                self.stdout.write('[WARNING] Reistijd met pk=%s is niet compleet; skipping' % reistijd.pk)
                continue

            try:
                vanaf_lat_lon = self._lat_lon_to_api(reistijd.vanaf_lat, reistijd.vanaf_lon)
                naar_lat_lon = self._lat_lon_to_api(reistijd.naar_lat, reistijd.naar_lon)
            except ValueError:
                self.stdout.write('[WARNING] Fout in lat/lon (geen float?) voor reistijd pk=%s' % reistijd.pk)
            else:
                mins = self._reistijd_met_auto(vanaf_lat_lon, naar_lat_lon)

                if mins > 5 * 60:
                    self.stdout.write('[WARNING] Rare reistijd (%s minuten) wordt niet opgeslagen' % mins)
                else:
                    if mins != reistijd.reistijd_min:
                        self.stdout.write('[INFO] Reistijd pk=%s is aangepast van %s naar %s minuten' % (reistijd.pk,
                                                                                                         reistijd.reistijd_min,
                                                                                                         mins))
                        reistijd.reistijd_min = mins
                    else:
                        self.stdout.write('[INFO] Reistijd pk=%s is niet gewijzigd' % reistijd.pk)

                    reistijd.op_datum = today
                    reistijd.save(update_fields=['reistijd_min', 'op_datum'])

            # begrens het aantal verzoeken per keer
            if self.verzoeken_teller >= self.verzoeken_grens:
                self.stdout.write('[WARNING] Limit van %s verzoeken per keer bereikt' % self.verzoeken_grens)
                break
        # for

    def run(self):

        if self._connect_gmaps():
            # connection success
            self._update_scheids()
            self._update_locaties()
            self._update_locaties_fallback()
            self._update_reistijd()
            self._refresh_reistijd()

        self.stdout.write('[INFO] Aantal verzoeken naar Routes API: %s' % self.verzoeken_teller)


# end of file
