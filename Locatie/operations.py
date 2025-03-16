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
import googlemaps
import datetime


class ReistijdBepalen(object):

    """ Bereken de reistijd tussen twee locaties met Google Maps """

    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

        self._gmaps = None
        self.verzoeken_teller = 0

        # aankomst op de wedstrijdlocatie zetten we standaard op een zaterdag in de toekomst om 08:00
        date = timezone.localtime(timezone.now())
        date += datetime.timedelta(days=60)
        while date.weekday() != 5:      # 5 = zaterdag
            date += datetime.timedelta(days=1)
        # while
        self._future_saturday_0800 = date

    def _connect_gmaps(self):
        """ Init de google maps library
            Return: True  = success
                    False = failure
        """
        if not self._gmaps:
            options = {'key': settings.GMAPS_KEY}

            if settings.GMAPS_API_URL:      # pragma: no branch
                self.stdout.write('[INFO] Server URL %s' % repr(settings.GMAPS_API_URL))
                options['base_url'] = settings.GMAPS_API_URL

            try:
                self._gmaps = googlemaps.Client(**options)
            except Exception as exc:
                self.stderr.write('[ERROR] Fout tijdens gmaps init: %s' % str(exc))
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
        except (googlemaps.exceptions.ApiError, googlemaps.exceptions.HTTPError) as exc:
            self.stderr.write('[ERROR] Fout van gmaps directions route van %s naar %s: error %s' % (
                                repr(vanaf_lat_lon), repr(naar_lat_lon), str(exc)))
            return 16 * 60      # geef een gek getal terug wat om aandacht vraagt
        else:
            self.verzoeken_teller += 1

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
            self.stderr.write('[ERROR] Onvolledig directions antwoord: %s' % repr(results))
            mins = 17 * 60      # geef een gek getal terug wat om aandacht vraagt
        else:
            mins = int(round(secs / 60, 0))
            self.stdout.write('[INFO] Reistijd %s is %s seconden; is %s minuten' % (repr(duration['text']), secs, mins))

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

            vanaf_lat_lon = "%s, %s" % (reistijd.vanaf_lat, reistijd.vanaf_lon)
            naar_lat_lon = "%s, %s" % (reistijd.naar_lat, reistijd.naar_lon)

            mins = self._reistijd_met_auto(vanaf_lat_lon, naar_lat_lon)

            reistijd.reistijd_min = mins
            reistijd.op_datum = today

            reistijd.save(update_fields=['reistijd_min', 'op_datum'])
        # for

    def _refresh_reistijd(self):
        # na 6 maanden verversen we de reistijd

        today = timezone.localtime(timezone.now()).date()
        oud = today - datetime.timedelta(days=183)

        for reistijd in Reistijd.objects.filter(op_datum__lt=oud):

            self.stdout.write('[INFO] Reistijd met pk=%s wordt vernieuwd' % reistijd.pk)

            vanaf_lat_lon = "%s, %s" % (reistijd.vanaf_lat, reistijd.vanaf_lon)
            naar_lat_lon = "%s, %s" % (reistijd.naar_lat, reistijd.naar_lon)

            mins = self._reistijd_met_auto(vanaf_lat_lon, naar_lat_lon)

            if mins != reistijd.reistijd_min:
                self.stdout.write('[INFO] Reistijd pk=%s is aangepast van %s naar %s minuten' % (reistijd.pk,
                                                                                                 reistijd.reistijd_min,
                                                                                                 mins))
                reistijd.reistijd_min = mins
            else:
                self.stdout.write('[INFO] Reistijd pk=%s is niet gewijzigd')

            reistijd.op_datum = today
            reistijd.save(update_fields=['reistijd_min', 'op_datum'])
        # for

    def run(self):

        if self._connect_gmaps():
            # connection success
            self._update_scheids()
            self._update_locaties()
            self._update_locaties_fallback()
            self._update_reistijd()
            self._refresh_reistijd()

        self.stdout.write('[INFO] Aantal verzoeken naar gmaps api: %s' % self.verzoeken_teller)


# end of file
