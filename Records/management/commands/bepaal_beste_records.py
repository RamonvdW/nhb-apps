# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Tabel met de beste Nederlandse Records invullen """

from django.conf import settings
from django.db.models import F
from django.core.management.base import BaseCommand
from Records.models import IndivRecord, BesteIndivRecords


GESLACHT2INDEX = {'M': 1, 'V': 2}

MATERIAALKLASSE2INDEX = {'R': 1, 'C': 2, 'BB': 3, 'LB': 4, 'IB': 5, 'TR': 6}

LEEFTIJDSCATEGORIE2INDEX = {'C': 1, 'J': 2, 'S': 3, 'M': 4, 'U': 5}


class Command(BaseCommand):
    help = "Bepaal de beste NL records (voor presentatie)"

    @staticmethod
    def _bepaal_volgorde(obj):
        # bepaal de presentatie volgorde
        index_s = 1 + settings.RECORDS_TOEGESTANE_SOORTEN.index(obj.soort_record)
        index_l = LEEFTIJDSCATEGORIE2INDEX[obj.leeftijdscategorie]
        index_g = GESLACHT2INDEX[obj.geslacht]
        index_m = MATERIAALKLASSE2INDEX[obj.materiaalklasse]
        if obj.para_klasse:
            index_p = 1 + settings.RECORDS_TOEGESTANE_PARA_KLASSEN.index(obj.para_klasse)
        else:
            index_p = 0

        # index_s needs 8 bits
        # index_m needs 3 bits
        # index_l needs 3 bits
        # index_p needs 8 bits
        # index_g needs 2 bits
        volgorde = index_s << (3+3+8+2) | index_m << (3+8+2) | index_l << (8+2) | index_p << 2 | index_g

        # print('''volgorde?
        # soort_record: %s       --> %s
        # leeftijdscategorie: %s --> %s
        # materiaalklasse: %s    --> %s
        # para_klasse: %s        --> %s
        # geslacht: %s           --> %s
        #      ---> volgorde=%s''' % (obj.soort_record, index_s,
        #                             obj.leeftijdscategorie, index_l,
        #                             obj.materiaalklasse, index_m,
        #                             obj.para_klasse, index_p,
        #                             obj.geslacht, index_g,
        #                             volgorde))
        return volgorde

    def handle(self, *args, **options):

        # para records zijn een keer omgezet van specifieke leeftijdscategorie naar 'U'
        # ruime de oude 'beste' records op
        objs = (BesteIndivRecords
                .objects
                .exclude(beste__leeftijdscategorie=F('leeftijdscategorie')))
        self.stdout.write("[INFO] Verwijder beste records met inconsistente leeftijdscategorie: %s" % objs.count())
        objs.delete()

        # ruim fout op: niet-para record gekoppeld aan beste record voor para
        objs = (BesteIndivRecords
                .objects
                .exclude(beste__para_klasse=F('para_klasse')))
        self.stdout.write("[INFO] Verwijder beste records met inconsistente para_klasse: %s" % objs.count())
        objs.delete()

        # ruim fout op: soort_record komt niet overeen met gekoppelde soort_record
        objs = (BesteIndivRecords
                .objects
                .exclude(beste__soort_record=F('soort_record')))
        self.stdout.write("[INFO] Verwijder beste records met inconsistente soort_record: %s" % objs.count())
        objs.delete()

        # bepaal alle unieke combinaties
        objs = (IndivRecord
                .objects
                .filter(verbeterbaar=True)
                .distinct('discipline', 'soort_record', 'geslacht', 'leeftijdscategorie',
                          'materiaalklasse', 'para_klasse'))

        # voor elke combi, bepaal de hoogste score
        for obj in objs:

            updated = list()        # voor save() optimalisatie

            beste, _ = (BesteIndivRecords
                        .objects
                        .select_related('beste')
                        .get_or_create(
                            discipline=obj.discipline,
                            soort_record=obj.soort_record,
                            geslacht=obj.geslacht,
                            leeftijdscategorie=obj.leeftijdscategorie,
                            materiaalklasse=obj.materiaalklasse,
                            para_klasse=obj.para_klasse))

            volgorde = self._bepaal_volgorde(beste)

            if beste.volgorde != volgorde:
                beste.volgorde = volgorde
                updated.append('volgorde')

            alle = (IndivRecord
                    .objects
                    .filter(verbeterbaar=True,
                            discipline=obj.discipline,
                            soort_record=obj.soort_record,
                            geslacht=obj.geslacht,
                            leeftijdscategorie=obj.leeftijdscategorie,
                            materiaalklasse=obj.materiaalklasse,
                            para_klasse=obj.para_klasse)
                    .order_by('-score', '-x_count'))

            hoogste = alle[0]

            if beste.beste != hoogste:
                beste.beste = hoogste
                updated.append('beste')

            if len(updated):
                beste.save(update_fields=updated)

        # for

        # verwijder oude records die niet meer verbeterbaar zijn
        objs = (BesteIndivRecords
                .objects
                .filter(beste__verbeterbaar=False))
        self.stdout.write("[INFO] Verwijder niet meer verbeterbare beste records: %s" % objs.count())
        objs.delete()

        self.stdout.write('Done')


# end of file
