# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from Records.definities import LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Records.models import IndivRecord
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestRecordsCliImport(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Import module """

    def setUp(self):
        """ initialisatie van de test case """

        # NhbLib
        sporter = Sporter()
        sporter.lid_nr = 123456
        sporter.voornaam = 'Jan'
        sporter.achternaam = 'Schutter'
        sporter.email = 'jan@test.nl'
        sporter.geboorte_datum = parse_date('1970-03-03')
        sporter.woon_straatnaam = 'Papendal'
        sporter.geslacht = 'M'
        sporter.sinds_datum = parse_date("1991-02-03")  # Y-M-D
        sporter.save()

        sporter = Sporter()
        sporter.lid_nr = 123457
        sporter.voornaam = 'Petra'
        sporter.achternaam = 'Schutter'
        sporter.email = 'petra@test.nl'
        sporter.geboorte_datum = parse_date('1970-01-30')
        sporter.woon_straatnaam = 'Arnhem'
        sporter.geslacht = 'V'
        sporter.sinds_datum = parse_date("1991-02-05")  # Y-M-D
        sporter.save()

        # Record 42
        rec = IndivRecord()
        rec.volg_nr = 42
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Test record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = MATERIAALKLASSE[0][0]     # R
        # rec.materiaalklasse_overig =
        rec.sporter = sporter
        rec.naam = 'Top Schutter'
        rec.datum = parse_date('2017-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 1234
        rec.max_score = 5678
        rec.x_count = 56
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        self.assertEqual(rec.score_str(), '1234 (56X)')
        self.assertEqual(rec.max_score_str(), '5678 (567X)')

        # Record 43
        rec = IndivRecord()
        rec.volg_nr = 43
        rec.discipline = DISCIPLINE[1][0]   # 18
        rec.soort_record = 'Test record para'
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

        self.assertIsNotNone(str(rec))
        self.assertEqual(rec.score_str(), '1235')

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

        self.assertIsNotNone(str(rec))

    def test_file_missing(self):
        # afhandelen niet bestaand bestand
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', './notexisting.json')
        self.assertTrue(f1.getvalue().startswith('[ERROR] Kan bestand ./notexisting.json niet lezen ('))
        self.assertEqual(f2.getvalue(), '')

    def test_broken_file(self):
        # kapot bestand
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_01.json')
        self.assertTrue(f1.getvalue().startswith("[ERROR] Probleem met het JSON formaat in bestand './Records/management/testfiles/testfile_01.json'"))
        self.assertEqual(f2.getvalue(), '')

    def test_extra_sheet(self):
        # onverwacht tabblad
        # verkeerde headers
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_02.json', '--dryrun')
        self.assertTrue('[ERROR] Niet ondersteunde tabblad naam: Onbekende blad naam' in f1.getvalue())
        self.assertTrue('[ERROR] Kolom headers kloppen niet voor range Data team' in f1.getvalue())
        self.assertTrue('Samenvatting: ' in f2.getvalue())
        self.assertTrue('\nDRY RUN\n' in f2.getvalue())
        self.assertTrue('\nDone\n' in f2.getvalue())

    def test_no_data(self):
        # bestand met alleen headers, geen data
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_03.json')
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue('\nDone\n' in f2.getvalue())

    def test_incomplete(self):
        # incompleet bestand
        with self.assert_max_queries(50):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_04.json')
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue('[INFO] Record OD-1 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record OD-2 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 18-1 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 18-2 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 25-1 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 25-2 toegevoegd' in f2.getvalue())
        self.assertTrue('; 1 ongewijzigd;' in f2.getvalue())    # 25-44

    def test_data_errors(self):
        # all kinds of errors
        with self.assert_max_queries(37):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_05.json')
        self.assertTrue("[ERROR] Foute index (geen nummer): 'XA' in" in f1.getvalue())
        self.assertTrue("Fout geslacht: 'XB' + Foute leeftijdscategorie': 'XC' + Foute materiaalklasse: 'XD' + Foute discipline: 'XE' op blad 'OD' + Fout in soort_record: 'XF' is niet bekend + Fout in para klasse: 'XG' is niet bekend + Fout in pijlen: 'XI' is geen nummer + Fout bondsnummer: 'XJ' + Fout in score 'XK' + Fout in X-count 'XL' is geen getal + Foute tekst in Ook ER: 'XM' + Foute tekst in Ook WR: 'XN' in " in f1.getvalue())
        obj = IndivRecord.objects.get(discipline='18', volg_nr=2)
        self.assertEqual(obj.leeftijdscategorie, 'U')

    def test_data_changes(self):
        # all kinds of changes
        with self.assert_max_queries(37):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_06.json')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("Wijzigingen voor record OD-42:" in f2.getvalue())
        self.assertTrue("geslacht: 'M' --> 'V'" in f2.getvalue())
        self.assertTrue("leeftijdscategorie: 'M' --> 'C'" in f2.getvalue())
        self.assertTrue("materiaalklasse: 'R' --> 'C'" in f2.getvalue())
        self.assertTrue("soort_record: 'Test record' --> '60m'" in f2.getvalue())
        self.assertTrue("para_klasse: '' --> 'W1'" in f2.getvalue())
        self.assertTrue("max_score: 5678 --> 1200" in f2.getvalue())
        self.assertTrue("sporter: 123457 Petra Schutter [V, 1970] --> 123456 Jan Schutter [M, 1970]" in f2.getvalue())
        self.assertTrue("naam: 'Top Schutter' --> 'Jan Schutter'" in f2.getvalue())
        self.assertTrue("datum: 2017-08-27 --> 1901-01-01" in f2.getvalue())
        self.assertTrue("plaats: 'Papendal' --> 'Elbonia'" in f2.getvalue())
        self.assertTrue("land: 'Nederland' --> 'Mudland'" in f2.getvalue())
        self.assertTrue("score: 1234 --> 1032" in f2.getvalue())
        self.assertTrue("x_count: 56 --> 21" in f2.getvalue())
        self.assertTrue("is_european_record: False --> True" in f2.getvalue())
        self.assertTrue("is_world_record: False --> True" in f2.getvalue())
        self.assertTrue("score_notitie: '' --> 'Geen notitie'" in f2.getvalue())
        self.assertTrue("verbeterbaar: True --> False" in f2.getvalue())

        self.assertTrue("Wijzigingen voor record 25-44:" in f2.getvalue())
        self.assertTrue("score_notitie: '' --> 'gedeeld'" in f2.getvalue())

    def test_foutvrij_dryrun(self):
        with self.assert_max_queries(25):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_06.json', '--dryrun')
        self.assertTrue("DRY RUN\nSamenvatting: 5 records;" in f2.getvalue())

    def test_onbekend_bondsnummer(self):
        # onbekend bondsnummer
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_07.json')
        self.assertTrue("Bondsnummer niet bekend: '999999' " in f1.getvalue())

    def test_foute_datums(self):
        # foute datums
        with self.assert_max_queries(33):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_08.json')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '6-30-2017' in ['2'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-6-17' in ['3'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-617' in ['4'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30/6/2017' in ['5'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-6-1917' in ['6'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-6-2099' in ['7'," in f1.getvalue())

    def test_dubbele_nrs(self):
        # dubbele nummers
        with self.assert_max_queries(35):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_09.json')
        self.assertTrue("[ERROR] Volgnummer 22 komt meerdere keren voor in" in f1.getvalue())

    def test_niet_consecutief(self):
        # test met records die niet consecutief zijn
        with self.assert_max_queries(46):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_10.json')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Score niet consecutief voor records OD-101 en OD-100 (1200(57X) >= 1200(56X))" in f1.getvalue())
        self.assertTrue("[WARNING] Identieke datum en score voor records OD-202 en OD-102" in f1.getvalue())
        self.assertTrue("[WARNING] Score niet consecutief voor records OD-401 en OD-400 (400 >= 300)" in f1.getvalue())

    def test_verkeerde_soort_record(self):
        with self.assert_max_queries(30):
            f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_11.json')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Max score (afgeleide van aantal pijlen) is niet consistent in soort" in f1.getvalue())

    def test_wa_renames(self):
        # IB is hernoemd naar TR, maar in de administratie ondersteunen we beide
        # Master/Senior/Junior/Cadet zijn hernoemd naar 50+/21+/Onder 21/Onder 18
        f1, f2 = self.run_management_command('import_records', './Records/management/testfiles/testfile_12.json')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('5 toegevoegd; 0 waarschuwingen, 0 fouten' in f2.getvalue())

# end of file
