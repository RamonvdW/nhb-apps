# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from ImportCRM.import_base import ImportCrmBase
from Geo.models import Rayon, Regio

EXPECTED_RAYON_KEYS = ('rayon_number', 'name')
EXPECTED_REGIO_KEYS = ('rayon_number', 'region_number', 'name')


class ImportCrmGeo(ImportCrmBase):
    """ Importeer regio's en rayon's uit de CRM

        Deze zijn allemaal al aangemaakt in Geo/migrations/m00*_squashed.py
        Hier kunnen we de namen aanpassen
    """

    def __init__(self, *args):
        super().__init__(*args)

        self.count_rayons = 0
        self.count_regios = 0

        self._cache_rayon = dict()  # [rayon_nr] = Rayon()
        self._cache_regio = dict()  # [regio_nr] = Regio()
        self._vul_cache()

    def _vul_cache(self):
        for rayon in Rayon.objects.all():
            self._cache_rayon[rayon.rayon_nr] = rayon
        # for

        for regio in Regio.objects.all():
            self._cache_regio[regio.regio_nr] = regio
        # for

    def vind_rayon(self, rayon_nr: str | int) -> None | Rayon:
        try:
            rayon_nr = int(rayon_nr)
        except ValueError:
            self.out_error('Foutief rayon nummer: %s (geen getal)' % repr(rayon_nr))
            return None

        return self._cache_rayon.get(rayon_nr, None)

    def vind_regio(self, regio_nr: str | int) -> None | Regio:
        try:
            regio_nr = int(regio_nr)
        except ValueError:
            self.out_error('Foutief regio nummer: %s (geen getal)' % repr(regio_nr))
            return None

        return self._cache_regio.get(regio_nr, None)

    def importeer_rayons(self, data: list):
        """ Importeert data van alle rayons """

        if self.check_keys(data[0].keys(), EXPECTED_RAYON_KEYS, (), "rayon"):
            return

        # FUTURE: controleer dat alle rayons genoemd worden

        # rayons zijn statisch gedefinieerd, met een extra beschrijving
        # controleer alleen of er een wijziging is die we over moeten nemen
        for rayon in data:
            self.count_rayons += 1
            rayon_nr = rayon['rayon_number']
            rayon_naam = rayon['name']

            # zoek het rayon op
            obj = self.vind_rayon(rayon_nr)
            if not obj:
                # toevoegen van een rayon ondersteunen we niet
                self.out_error('Onbekend rayon %s' % repr(rayon))
                continue

            if obj.naam != rayon_naam:
                self.out_info('Wijziging naam rayon %s: %s --> %s' % (rayon_nr, repr(obj.naam), repr(rayon_naam)))
                self.count_wijzigingen += 1
                obj.naam = rayon_naam
                if not self.dryrun:
                    obj.save(update_fields=['naam'])
        # for
        # verwijderen van een rayon ondersteunen we niet

    def importeer_regios(self, data: list):
        """ Importeert data van alle regios """

        if self.check_keys(data[0].keys(), EXPECTED_REGIO_KEYS, (), "regio"):
            return

        # FUTURE: controleer dat alle regios genoemd worden

        # regios zijn statisch gedefinieerd
        # naam alleen de naam over
        for regio in data:
            self.count_regios += 1
            # rayon_nr = regio['rayon_number']
            regio_nr = regio['region_number']
            regio_naam = regio['name']

            # zoek de regio op
            obj = self.vind_regio(regio_nr)
            if not obj:
                # toevoegen van een regio ondersteunen we niet
                self.out_error('Onbekende regio %s' % repr(regio))
                continue

            if obj.naam != regio_naam:
                self.out_info('Wijziging naam regio %s: %s --> %s' % (regio_nr, repr(obj.naam), repr(regio_naam)))
                self.count_wijzigingen += 1
                obj.naam = regio_naam
                if not self.dryrun:
                    obj.save(update_fields=['naam'])
        # for
        # verwijderen van een regio ondersteunen we niet

# end of file
