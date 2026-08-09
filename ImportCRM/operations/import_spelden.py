# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from ImportCRM.import_base import ImportCrmBase
from Sporter.models import Speelsterkte
import datetime


class ImportCrmSpelden(ImportCrmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self._import_sporters = None

        self._cache_sterk = dict()              # [lid_nr] = [SpeelSterkte(), ...]
        self._speelsterkte2volgorde = dict()    # [(discipline, beschrijving)] = volgorde

        self._vul_cache()

        self.count_sterkte = Speelsterkte.objects.count()

    def zet_refs(self, import_sporters):
        self._import_sporters = import_sporters

    def _vul_cache(self):
        for sterkte in Speelsterkte.objects.select_related('sporter').all():
            try:
                self._cache_sterk[sterkte.sporter.lid_nr].append(sterkte)
            except KeyError:
                self._cache_sterk[sterkte.sporter.lid_nr] = [sterkte]
        # for

        for disc, beschr, volgorde in settings.SPEELSTERKTE_VOLGORDE:
            # discipline, beschrijving, volgorde
            self._speelsterkte2volgorde[(disc, beschr)] = volgorde
        # for


    def importeer(self, data: list):
        """ Importeert data van alle leden """

        """ data:
            [
                {
                    'member_number': int,
                    'skill_level': [
                        {
                            "date": "1990-01-01",
                            "skill_level_code": "R1000",
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

        for member in data:
            lid_nr = member['member_number']

            obj = self._import_sporters.vind_sporter(lid_nr)
            if not obj:
                continue

            huidige_lijst = self._cache_sterk.get(lid_nr, [])

            if obj.is_actief_lid:
                nieuwe_lijst = list()

                for sterk in member.get('skill_levels', []):
                    cat = sterk['category_name']
                    disc = sterk['discipline_name']
                    datum_raw = sterk['date']
                    beschr = sterk['skill_level_name']
                    code = sterk['skill_level_code']        # voor op de bondspas

                    try:
                        datum = datetime.datetime.strptime(datum_raw, "%Y-%m-%d").date()  # YYYY-MM-DD
                    except (ValueError, TypeError):
                        self.out_error('Lid %s heeft skill level met slechte datum: %s' % (
                                                lid_nr, repr(datum_raw)))
                    else:
                        try:
                            volgorde = self._speelsterkte2volgorde[(disc, beschr)]
                        except KeyError:
                            volgorde = 9999
                            self.out_warning("Kan speelsterkte volgorde niet vaststellen voor: (%s, %s)" % (
                                                repr(disc), repr(beschr)))

                        # kijk of deze al bestaat
                        found = None
                        for huidig in huidige_lijst:
                            if huidig.beschrijving == beschr and huidig.discipline == disc and huidig.category == cat:
                                # bestaat al
                                found = huidig
                                break   # from the for
                        # for

                        if found:
                            # verwijderen uit de lijst zodat echt verwijderde speelsterktes kunnen vinden
                            huidige_lijst.remove(found)
                        else:
                            # toevoegen
                            self.out_info('Lid %s: nieuwe speelsterkte %s, %s, %s' % (
                                                lid_nr, datum, disc, beschr))

                            try:
                                volgorde = self._speelsterkte2volgorde[(disc, beschr)]
                            except KeyError:
                                volgorde = 9999
                                self.out_warning('Kan speelsterkte volgorde niet vaststellen voor: (%s, %s)' % (
                                                    repr(disc), repr(beschr)))

                            sterk = Speelsterkte(
                                         sporter=obj,
                                         beschrijving=beschr,
                                         discipline=disc,
                                         category=cat,
                                         volgorde=volgorde,
                                         datum=datum,
                                         pas_code=code)
                            nieuwe_lijst.append(sterk)
                            self.count_toevoegingen += 1
                # for

                if len(nieuwe_lijst):
                    Speelsterkte.objects.bulk_create(nieuwe_lijst)
            else:
                # sporter is geen actief lid meer
                # behoud zijn speelsterktes, totdat de sporter echt verwijderd wordt
                huidige_lijst = list()

            # verwijder oude speelsterktes
            if len(huidige_lijst):
                for sterk in huidige_lijst:
                    self.out_info('Speelsterkte is vervallen: lid=%s: %s' % (lid_nr, sterk))
                    self.count_verwijderingen += 1
                    sterk.delete()
                # for
        # for member

# end of file
