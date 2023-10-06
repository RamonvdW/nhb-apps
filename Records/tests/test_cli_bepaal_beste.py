# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.utils.dateparse import parse_date
from Records.definities import LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Records.models import IndivRecord, BesteIndivRecords
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


class TestRecordsCliBepaalBeste(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Import module """

    def setUp(self):
        """ initialisatie van de test case """

        # leden
        sporter = Sporter(
                    lid_nr=123456,
                    voornaam='Jan',
                    achternaam='Schutter',
                    email='jan@test.nl',
                    geboorte_datum=parse_date('1970-03-03'),
                    adres_code='Papendal',
                    geslacht='M',
                    sinds_datum=parse_date("1991-02-03"))  # Y-M-D
        sporter.save()

        sporter = Sporter(
                    lid_nr=123457,
                    voornaam='Petra',
                    achternaam='Schutter',
                    email='petra@test.nl',
                    geboorte_datum=parse_date('1970-01-30'),
                    adres_code='Arnhem',
                    geslacht='V',
                    sinds_datum=parse_date("1991-02-05"))  # Y-M-D
        sporter.save()

        # Record 42
        rec = IndivRecord(
                volg_nr=42,
                discipline=DISCIPLINE[0][0],   # OD
                soort_record='WA1440',
                geslacht=GESLACHT[0][0],   # M
                leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                materiaalklasse=MATERIAALKLASSE[0][0],     # R
                # materiaalklasse_overig=
                sporter=sporter,
                naam='Top Schutter',
                datum=parse_date('2017-08-27'),
                plaats='Papendal',
                land='Nederland',
                # score_notitie=
                # is_european_record=
                # is_world_record=
                score=1234,
                max_score=5678,
                x_count=56)
        rec.save()

        # Record 43
        rec = IndivRecord()
        rec.volg_nr = 43
        rec.discipline = DISCIPLINE[1][0]   # 18
        rec.soort_record = '18m (60p)'
        rec.geslacht = GESLACHT[1][0]   # V
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[1][0]   # S
        rec.materiaalklasse = 'R'       # Recurve
        rec.para_klasse = 'Open'
        # rec.sporter =
        rec.naam = 'Top Schutter 2'
        rec.datum = datetime.datetime.now()
        rec.plaats = 'Ergens Anders'
        rec.land = 'Nederland'
        rec.score = 1235
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        # Record 44
        rec = IndivRecord()
        rec.volg_nr = 44
        rec.discipline = DISCIPLINE[2][0]   # 25
        rec.soort_record = '25m'
        rec.geslacht = GESLACHT[1][0]   # V
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[3][0]   # C
        rec.materiaalklasse = 'R'       # Recurve
        rec.sporter = sporter
        rec.naam = 'Petra Schutter'
        rec.datum = parse_date('2017-08-27')
        rec.plaats = 'Nergens'
        rec.land = 'Niederland'
        rec.score = 249
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

    def test_bepaal(self):
        self.assertEqual(BesteIndivRecords.objects.count(), 0)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(27):
            management.call_command('bepaal_beste_records', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("Done" in f2.getvalue())
        self.assertEqual(BesteIndivRecords.objects.count(), 3)

        # draai nog een keer om alle 'geen wijzig' takken te raken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('bepaal_beste_records', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("Done" in f2.getvalue())
        self.assertEqual(BesteIndivRecords.objects.count(), 3)

# end of file
