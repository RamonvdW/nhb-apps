# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from BasisTypen.definities import SCHEIDS_NIET, SCHEIDS_VERENIGING, SCHEIDS_BOND, SCHEIDS_INTERNATIONAAL
from ImportCRM.import_base import ImportCrmBase
from Opleiding.definities import CODE_SR_VER, CODE_SR_BOND, CODE_SR_INTERNATIONAAL
from Opleiding.models import OpleidingDiploma


class ImportCrmOpleidingen(ImportCrmBase):

    """ importeert de genoten opleidingen en bepaalt het scheidsrechter-niveau """

    def __init__(self, *args):
        super().__init__(*args)

        self._import_sporters = None

        self._cache_diploma = dict()            # [lid_nr, code] = OpleidingDiploma()
        self._code2opleiding = dict()           # [opleiding code] = (beschrijving, toon_op_pas)
        self._opleiding_onbekend = dict()       # [opleiding code] = aantal

        self._vul_cache()

        self.count_diplomas = len(self._cache_diploma)

    def zet_refs(self, import_sporters):
        self._import_sporters = import_sporters

    def _vul_cache(self):
        for code, afkorting, beschrijving, _ in settings.OPLEIDING_CODES:
            toon_op_pas = afkorting != ''
            self._code2opleiding[code] = (beschrijving, toon_op_pas)
        # for

        for diploma in OpleidingDiploma.objects.select_related('sporter').all():
            tup = (diploma.sporter.lid_nr, diploma.code)
            diploma.gezien_tijdens_import = False
            self._cache_diploma[tup] = diploma
        # for

    def _verwijder_verlopen_diplomas(self):
        # verwijder verlopen diplomas
        pks = list()
        for diploma in self._cache_diploma.values():
            if not diploma.gezien_tijdens_import:
                pks.append(diploma.pk)
                self.out_debug('Opleiding diploma met pk=%s wordt verwijderd' % diploma.pk)
        # for
        if len(pks) > 0:
            OpleidingDiploma.objects.filter(pk__in=pks).delete()

    def importeer(self, data: list):
        """ Importeert de opleidingen van alle leden
            Zet ook het sporter.scheids veld, aan de hand van de genoten scheidsrechter-opleidingen
        """

        """ JSON velden:
            [
                {
                    'member_number': int,
                    'educations': [
                        {
                            "code": "011",
                            "name": "HANDBOOGTRAINER A",
                            "date_start": "1990-01-01",
                            "date_stop": "1990-01-01"
                        },
                        ...
                    ],
                },
                ...
             ]
        """
        for member in data:
            lid_nr = member['member_number']

            obj = self._import_sporters.vind_sporter(lid_nr)
            if not obj:
                continue

            # "educations": [
            #    {"code": "011", "name": "HANDBOOGTRAINER A", "date_start": "1990-01-01", "date_stop": "1990-01-01"},
            lid_edus = list()
            lid_scheids = SCHEIDS_NIET

            for edu in member.get('educations', []):
                code = edu['code']
                # kennen we deze opleiding?
                try:
                    beschrijving, toon_op_pas = self._code2opleiding[code]
                except KeyError:
                    try:
                        self._opleiding_onbekend[code] += 1
                    except KeyError:
                        self._opleiding_onbekend[code] = 1
                else:
                    date_start = edu['date_start']
                    date_stop = edu['date_stop']

                    if date_stop.startswith('9999-'):
                        # niet verlopen
                        tup = (code, beschrijving, toon_op_pas, date_start)
                        lid_edus.append(tup)

                        # opleiding codes voor scheidsrechters
                        if code == CODE_SR_VER:
                            # voorkom downgrade
                            if lid_scheids == SCHEIDS_NIET:
                                lid_scheids = SCHEIDS_VERENIGING

                        elif code == CODE_SR_BOND:
                            # voorkom downgrade
                            if lid_scheids != SCHEIDS_INTERNATIONAAL:
                                lid_scheids = SCHEIDS_BOND

                        elif code == CODE_SR_INTERNATIONAAL:
                            lid_scheids = SCHEIDS_INTERNATIONAAL
            # for

            if obj.scheids != lid_scheids:
                self.out_info('Lid %s: scheids %s --> %s' % (lid_nr, obj.scheids, lid_scheids))
                self.count_wijzigingen += 1
                obj.scheids = lid_scheids
                obj.save(update_fields=['scheids'])

            if obj.is_actief_lid:
                dupe_codes = list()
                for code, beschrijving, toon_op_pas, date_start in lid_edus:
                    # meld dubbele codes omdat we er niet tegen kunnen en het gejojo met de datums veroorzaakt
                    if code in dupe_codes:
                        self.out_warning('Lid %s heeft een dubbele opleiding: code %s' % (lid_nr, code))
                        continue        # niet importeren

                    dupe_codes.append(code)

                    try:
                        tup = (lid_nr, code)
                        diploma = self._cache_diploma[tup]
                    except KeyError:
                        diploma = OpleidingDiploma(
                                        sporter=obj,
                                        code=code,
                                        beschrijving=beschrijving,
                                        toon_op_pas=toon_op_pas,
                                        datum_begin=date_start)
                    else:
                        diploma.gezien_tijdens_import = True

                        if diploma.beschrijving != beschrijving:
                            diploma.beschrijving = beschrijving

                        if str(diploma.datum_begin) != date_start:
                            self.out_info('Lid %s: opleiding %s datum_begin: %s --> %s' % (
                                                lid_nr, code, diploma.datum_begin, date_start))
                            diploma.datum_begin = date_start

                    if not self.dryrun:
                        diploma.save()
                # for
        # for member

        for code, aantal in self._opleiding_onbekend.items():
            self.out_warning('Opleiding code %s is niet bekend (%s keer in gebruik)' % (code, aantal))
        # for

        self._verwijder_verlopen_diplomas()

# end of file
