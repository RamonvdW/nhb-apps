# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from ImportCRM.import_base import ImportCrmBase
from Spelden.models import Speld, SpeldToegekend
import datetime


class ImportCrmSpelden(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self._import_sporters = None

        self._cache_speld = dict()              # [pas_code] = Speld
        self._cache_toegekend = dict()          # [lid_nr] = [SpeldToegekend, ...]
        self._vul_cache()

        self.count_toegekende_spelden = SpeldToegekend.objects.count()

    def zet_refs(self, import_sporters):
        self._import_sporters = import_sporters

    def _vul_cache(self):
        for speld in Speld.objects.all():
            self._cache_speld[speld.pas_code] = speld
        # for

        for toegekend in SpeldToegekend.objects.select_related('speld', 'sporter').all():
            try:
                self._cache_toegekend[toegekend.sporter.lid_nr].append(toegekend)
            except KeyError:
                self._cache_toegekend[toegekend.sporter.lid_nr] = [toegekend]
        # for

    def _importeer_voor_sporter(self, sporter, data):

        huidige_lijst = self._cache_toegekend.get(sporter.lid_nr, [])
        nieuwe_lijst = list()

        for was_toegekend in data:
            """
                'skill_level': [
                    {
                        "date": "1990-01-01",
                        "skill_level_code": "R1000",            # pas code
                        "skill_level_name": "Recurve 1000",
                        "discipline_code": "REC",
                        "discipline_name": "Recurve",
                        "category_name": "Senior"
                    },
                    ...
                ]
            """
            datum_raw = was_toegekend['date']
            pas_code = was_toegekend['skill_level_code']

            # vertaal de oude pas_code naar de nieuwe pas_code
            pas_code = settings.CRM_IMPORT_SPELDEN_VERTAAL_PAS_CODE.get(pas_code, pas_code)

            # vind de speld
            speld = self._cache_speld.get(pas_code, None)
            if not speld:
                self.out_error('Lid %s heeft toegekende speld met onbekende pas_code %s' % (sporter.lid_nr,
                                                                                            repr(pas_code)))
                continue

            # check en converteer de datum
            try:
                datum = datetime.datetime.strptime(datum_raw, "%Y-%m-%d").date()  # YYYY-MM-DD
            except (ValueError, TypeError):
                self.out_error('Lid %s heeft toegekende speld %s met slechte datum: %s' % (sporter.lid_nr,
                                                                                           repr(pas_code),
                                                                                           repr(datum_raw)))
                continue

            # kijk of deze al geimporteerd was
            gevonden = False
            for al_toegekend in huidige_lijst:
                if al_toegekend.speld.pas_code == pas_code:
                    # bestaat al
                    # verwijderen uit de lijst zodat niet meer toegekende spelden kunnen vinden en verwijderen
                    huidige_lijst.remove(al_toegekend)
                    gevonden = True
                    break
            # for

            if not gevonden:
                # toevoegen
                self.out_info('Nieuwe speld toegekend aan lid %s: %s, %s' % (sporter.lid_nr, datum, repr(pas_code)))
                toegekend = SpeldToegekend(
                                    speld=speld,
                                    sporter=sporter,
                                    datum=datum)
                nieuwe_lijst.append(toegekend)
                self.count_toevoegingen += 1
        # for

        if len(nieuwe_lijst):
            SpeldToegekend.objects.bulk_create(nieuwe_lijst)

        # verwijder niet meer toegekende spelden
        if len(huidige_lijst):
            for was_toegekend in huidige_lijst:
                self.out_info('Toegekend speld is vervallen: lid=%s: %s' % (sporter.lid_nr, was_toegekend.speld.pas_code))
                self.count_verwijderingen += 1
                was_toegekend.delete()
            # for

    def importeer(self, data: list):
        """ Importeert data van alle leden

            data:
                [
                    {
                        'member_number': int,
                        'skill_level': [
                            {
                                "date": "1990-01-01",
                                "skill_level_code": "R1000",            # pas code
                                "skill_level_name": "Recurve 1000",
                                "discipline_code": "REC",
                                "discipline_name": "Recurve",
                                "category_name": "Senior"
                            },
                            ...
                        ]
                    },
                    ...
                ]
        """

        for member_data in data:
            lid_nr = member_data['member_number']

            sporter = self._import_sporters.vind_sporter(lid_nr)
            if not sporter:
                continue

            skill_levels_data = member_data.get('skill_levels', [])
            self._importeer_voor_sporter(sporter, skill_levels_data)

        # for sporter

        self.count_toegekende_spelden = SpeldToegekend.objects.all().count()

# end of file
