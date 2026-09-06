# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from DataApi.import_base import ImportCrmBase
from DataApi.models import DataApiVereniging


EXPECTED_CLUB_KEYS = ('club_number', 'prefix', 'name', 'address', 'postal_code', 'location_name', 'iso_abbr',
                      'latitude', 'longitude')
OPTIONAL_CLUB_KEYS = ('region_number', 'smoke_free_status', 'has_disabled_facilities', 'phone_business',
                      'phone_private', 'phone_mobile', 'secretaris', 'member_admins', 'prefix', 'iban', 'bic',
                      'email', 'website',
                      'coc_number')     # was vroeger niet aanwezig


class ImportHistCrmVerenigingen(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self.count_actief = 0
        self.count_gestopt = 0

        self._cache_ver = dict()    # [ver_nr] = DataApiVereniging()
        self._vul_cache()

    def vind_vereniging(self, ver_nr: int) -> DataApiVereniging | None:
        return self._cache_ver.get(ver_nr, None)

    def _vul_cache(self):
        for ver in DataApiVereniging.objects.all():
            self._cache_ver[ver.ver_nr] = ver

            if ver.afmeld_datum != '':
                self.count_gestopt += 1
            else:
                self.count_actief += 1
        # for

    def _get_ver_nrs(self):
        return list(self._cache_ver.keys())

    def _store_vereniging(self, ver_nr: int, naam: str, kvk: str, straatnaam: str, huis_nr: int, postcode: str, plaats: str, lat: str, lon: str):
        ver = self.vind_vereniging(ver_nr)
        if not ver:
            # nieuw record
            ver = DataApiVereniging(
                    ver_nr=ver_nr,
                    naam=naam,
                    aanmeld_datum=self.aanmelddatum_ver,
                    kvk_nummer=kvk,
                    straatnaam=straatnaam,
                    huisnummer=huis_nr,
                    postcode=postcode,
                    plaats=plaats,
                    lat=lat,
                    lon=lon)

            self._cache_ver[ver_nr] = ver
            # self.out_info('Vereniging %s aangemaakt: %s' % (ver_nr, repr(ver.naam)))
            self.count_toevoegingen += 1

            if not self.dryrun:
                ver.save()
        else:
            # delta's opmerken en rapporteren
            updated = list()
            if naam != ver.naam:
                self.out_info('Vereniging %s wijziging naam: %s --> %s' %
                                (ver_nr, repr(ver.naam), repr(naam)))
                ver.naam = naam
                updated.append('naam')

            if kvk and kvk != ver.kvk_nummer:
                # self.out_info('Vereniging %s wijziging kvk_nummer: %s --> %s' %
                #                 (ver_nr, repr(ver.kvk_nummer), repr(kvk)))
                ver.kvk_nummer = kvk
                updated.append('kvk_nummer')

            if straatnaam and straatnaam != ver.straatnaam:
                self.out_info('Vereniging %s wijziging straatnaam: %s --> %s' %
                                (ver_nr, repr(ver.straatnaam), repr(straatnaam)))
                ver.straatnaam = straatnaam
                updated.append('straatnaam')

            if huis_nr != ver.huisnummer:
                self.out_info('Vereniging %s wijziging huisnummer: %s --> %s' %
                                (ver_nr, repr(ver.huisnummer), repr(huis_nr)))
                ver.huisnummer = huis_nr
                updated.append('huisnummer')

            if postcode and postcode != ver.postcode:
                self.out_info('Vereniging %s wijziging postcode: %s --> %s' %
                                (ver_nr, repr(ver.postcode), repr(postcode)))
                ver.postcode = postcode
                updated.append('postcode')

            if plaats and plaats != ver.plaats:
                self.out_info('Vereniging %s wijziging plaats: %s --> %s' %
                                (ver_nr, repr(ver.plaats), repr(plaats)))
                ver.plaats = plaats
                updated.append('plaats')

            if lat != ver.lat:
                self.out_info('Vereniging %s wijziging lat: %s --> %s' %
                                (ver_nr, repr(ver.lat), repr(lat)))
                ver.lat = lat
                updated.append('lat')

            if lon != ver.lon:
                self.out_info('Vereniging %s wijziging lon: %s --> %s' %
                                (ver_nr, repr(ver.lon), repr(lon)))
                ver.lon = lon
                updated.append('lon')

            if len(updated) > 0 and not self.dryrun:
                ver.save(update_fields=updated)

        return

    def importeer(self, data: list):
        """ Importeert alle verenigingen + gegevens over de primaire sportlocatie """

        if self.check_keys(data[0].keys(), EXPECTED_CLUB_KEYS, OPTIONAL_CLUB_KEYS, "club{vereniging}"):
            return

        # houd bij welke verenigingsnummers in de database zitten
        # als deze niet meer voorkomen, dan zijn ze verwijderd
        ver_nrs = self._get_ver_nrs()

        """ JSON velden (string, except):
                'club_number':             int
                'prefix',                  voorzetsel van de naam, zoals "De" en "HBSV"
                'name',
                'address':                 string with newlines
                'postal_code',
                'location_name',
                'coc_number',              KvK nummer
                'iso_abbr': 'NL',          
                'latitude',
                'longitude',
        }
        """

        for club in data:
            ver_nr = club['club_number']
            try:
                ver_nr = int(ver_nr)
            except ValueError:
                if self.dryrun and ver_nr == 'crash':
                    raise Exception('crash test')

                self.out_error('Geen valide verenigingsnummer: %s (geen getal)' % repr(ver_nr))
                continue

            ver_naam = club['name']

            if club['prefix']:
                ver_naam = club['prefix'] + ' ' + ver_naam

            ver_plaats = club['location_name']
            if not ver_plaats:
                # een vereniging zonder doel heeft een lege location_name - geen waarschuwing geven
                ver_plaats = ""     # voorkom None
            else:
                ver_plaats = ver_plaats.strip()

            ver_kvk = club.get('coc_number', None)
            if ver_kvk is None:
                ver_kvk = ''
            else:
                ver_kvk = ver_kvk.strip()
                if len(ver_kvk) != 8 or not ver_kvk.isdecimal():
                    self.out_warning('Vereniging %s KvK nummer %s moet 8 cijfers bevatten' % (ver_nr, repr(ver_kvk)))

            ver_straatnaam = ''
            ver_huisnummer = 0
            adres = club['address']
            # adres = "Straat 9\n1234 AB  Plaats\n"
            if adres:  # handles None and ''
                adres_spl = adres.strip().split('\n')
                if len(adres_spl) != 2:
                    self.out_error('Vereniging %s adres bestaat niet uit 2 regels: %s' % (ver_nr,
                                                                                          repr(club['address'])))
                if len(adres_spl) >= 2:
                    straat_huisnr = adres_spl[0]
                    ver_huisnummer = self.extract_huisnummer(straat_huisnr)

                    pos = straat_huisnr.find(str(ver_huisnummer))
                    if pos > 0:
                        if straat_huisnr.count(str(ver_huisnummer)) != 1:
                            self.out_debug('Uitdaging: meerdere matches huisnr %s in %s' % (ver_huisnummer, straat_huisnr))
                        ver_straatnaam = straat_huisnr[:pos].strip()

                    else:
                        self.out_error('Kan huisnummer %s niet vinden in adres %s' % (ver_huisnummer,
                                                                                      repr(straat_huisnr)))

                # self.out_debug('%s adres %s --> %s, %s' % (ver_nr, repr(adres), repr(ver_straatnaam), ver_huisnummer))

            # we verwachten dat alle clubs in Nederland zitten, dus NL postcode hebben
            postcode = club['postal_code']
            ver_postcode = ''
            if postcode:
                ver_postcode = postcode.upper().replace(' ', '')

            ver_lat = club['latitude']
            ver_lon = club['longitude']

            self._store_vereniging(ver_nr, ver_naam, ver_kvk, ver_straatnaam, ver_huisnummer, ver_postcode, ver_plaats, ver_lat, ver_lon)

            if ver_nr in ver_nrs:
                ver_nrs.remove(ver_nr)

        # for club

        # kijk of er verenigingen verwijderd moeten worden
        self._verwijder_verenigingen(ver_nrs)

    def _verwijder_verenigingen(self, ver_nrs):
        while len(ver_nrs) > 0:
            ver_nr = ver_nrs.pop(0)
            ver = self.vind_vereniging(ver_nr)
            if ver:
                if ver.afmeld_datum == '':
                    if ver.aanmeld_datum == '' or ver.aanmeld_datum < self.afmelddatum:
                        self.stdout.write('[INFO] Verwijder vereniging %s' % ver)
                        if not self.dryrun:
                            ver.afmeld_datum = self.afmelddatum
                            ver.save(update_fields=['afmeld_datum'])
        # while

# end of file
