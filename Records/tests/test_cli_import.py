# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from Records.definities import LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Records.models import IndivRecord
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime

TEST_FILES_PATH = './Records/test-files/'

TEST_FILE_BROKEN_FILE = TEST_FILES_PATH + 'testfile_01.json'
TEST_FILE_EXTRA_PAGE = TEST_FILES_PATH + 'testfile_02.json'
TEST_FILE_NO_DATA = TEST_FILES_PATH + 'testfile_03.json'
TEST_FILE_INCOMPLETE = TEST_FILES_PATH + 'testfile_04.json'
TEST_FILE_DATA_ERRORS = TEST_FILES_PATH + 'testfile_05.json'
TEST_FILE_CHANGES = TEST_FILES_PATH + 'testfile_06.json'
TEST_FILE_BAD_LID_NR = TEST_FILES_PATH + 'testfile_07.json'
TEST_FILE_BAD_DATES = TEST_FILES_PATH + 'testfile_08.json'
TEST_FILE_DOUBLE_NRS = TEST_FILES_PATH + 'testfile_09.json'
TEST_FILE_NIET_CONSECUTIEF = TEST_FILES_PATH + 'testfile_10.json'
TEST_FILE_VERKEERDE_SOORT = TEST_FILES_PATH + 'testfile_11.json'
TEST_FILE_WA_RENAMES = TEST_FILES_PATH + 'testfile_12.json'


class TestRecordsCliImport(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Import module """

    def setUp(self):
        """ initialisatie van de test case """

        # NhbLib
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
                    soort_record='Test record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    # materiaalklasse_overig
                    sporter=sporter,
                    naam='Top Schutter',
                    datum=parse_date('2017-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    # score_notitie
                    # is_european_record
                    # is_world_record
                    score=1234,
                    max_score=5678,
                    x_count=56)
        rec.save()

        self.assertEqual(rec.score_str(), '1234 (56X)')
        self.assertEqual(rec.max_score_str(), '5678 (567X)')

        # Record 43
        rec = IndivRecord(
                    volg_nr=43,
                    discipline=DISCIPLINE[1][0],   # 18
                    soort_record='Test record para',
                    geslacht=GESLACHT[1][0],       # V
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[1][0],   # S
                    materiaalklasse='R',           # Recurve
                    para_klasse='Open',
                    # rec.sporter,
                    naam='Top Schutter 2',
                    datum=datetime.datetime.now(),
                    plaats='Ergens Anders',
                    land='Nederland',
                    # score_notitie
                    # is_european_record
                    # is_world_record
                    score=1235)
        rec.save()

        self.assertIsNotNone(str(rec))
        self.assertEqual(rec.score_str(), '1235')

        # Record 44
        rec = IndivRecord(
                volg_nr=44,
                discipline=DISCIPLINE[2][0],   # 25
                soort_record='25m',
                geslacht=GESLACHT[1][0],   # V
                leeftijdscategorie=LEEFTIJDSCATEGORIE[3][0],   # C
                materiaalklasse='R',       # Recurve
                sporter=sporter,
                naam='Petra Schutter',
                datum=parse_date('2017-08-27'),
                plaats='Nergens',
                land='Niederland',      # noqa
                # score_notitie
                # is_european_record
                # is_world_record
                score=249)
        rec.save()

        self.assertIsNotNone(str(rec))

    def test_file_missing(self):
        # afhandelen niet bestaand bestand
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', './not-existing.json')
        self.assertTrue(f1.getvalue().startswith('[ERROR] Kan bestand ./not-existing.json niet lezen ('))
        self.assertEqual(f2.getvalue(), '')

    def test_broken_file(self):
        # kapot bestand
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_BROKEN_FILE)
        self.assertTrue(f1.getvalue().startswith(
            "[ERROR] Probleem met het JSON formaat in bestand "))
        self.assertEqual(f2.getvalue(), '')

    def test_extra_sheet(self):
        # onverwacht tabblad
        # verkeerde headers
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_EXTRA_PAGE,
                                                 '--dryrun')
        self.assertTrue('[ERROR] Niet ondersteunde tabblad naam: Onbekende blad naam' in f1.getvalue())
        self.assertTrue('[ERROR] Kolom headers kloppen niet voor range Data team' in f1.getvalue())
        self.assertTrue('Samenvatting: ' in f2.getvalue())
        self.assertTrue('\nDRY RUN\n' in f2.getvalue())
        self.assertTrue('\nDone\n' in f2.getvalue())

    def test_no_data(self):
        # bestand met alleen headers, geen data
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_NO_DATA)
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue('\nDone\n' in f2.getvalue())

    def test_incomplete(self):
        # incompleet bestand
        with self.assert_max_queries(50):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_INCOMPLETE)
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
            f1, f2 = self.run_management_command('import_records', TEST_FILE_DATA_ERRORS)
        self.assertTrue("[ERROR] Foute index (geen nummer): 'XA' in" in f1.getvalue())
        self.assertTrue("Fout geslacht: 'XB' + Foute leeftijdscategorie': 'XC' + Foute materiaalklasse: 'XD' + " +
                        "Foute discipline: 'XE' op blad 'OD' + Fout in soort_record: 'XF' is niet bekend + " +
                        "Fout in para klasse: 'XG' is niet bekend + Fout in pijlen: 'XI' is geen nummer + " +
                        "Fout bondsnummer: 'XJ' + Fout in score 'XK' + Fout in X-count 'XL' is geen getal + " +
                        "Foute tekst in Ook ER: 'XM' + Foute tekst in Ook WR: 'XN' in " in f1.getvalue())
        obj = IndivRecord.objects.get(discipline='18', volg_nr=2)
        self.assertEqual(obj.leeftijdscategorie, 'U')

    def test_data_changes(self):
        # all kinds of changes
        with self.assert_max_queries(37):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_CHANGES)
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
            f1, f2 = self.run_management_command('import_records', TEST_FILE_CHANGES,
                                                 '--dryrun')
        self.assertTrue("DRY RUN\nSamenvatting: 5 records;" in f2.getvalue())

    def test_onbekend_bondsnummer(self):
        # onbekend bondsnummer
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_BAD_LID_NR)
        self.assertTrue("Bondsnummer niet bekend: '999999' " in f1.getvalue())

    def test_foute_datums(self):
        # foute datums
        with self.assert_max_queries(33):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_BAD_DATES)
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
            f1, f2 = self.run_management_command('import_records', TEST_FILE_DOUBLE_NRS)
        self.assertTrue("[ERROR] Volgnummer 22 komt meerdere keren voor in" in f1.getvalue())

    def test_niet_consecutief(self):
        # test met records die niet consecutief zijn
        with self.assert_max_queries(46):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_NIET_CONSECUTIEF)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Score niet consecutief voor records OD-101 en OD-100 (1200(57X) >= 1200(56X))"
                        in f1.getvalue())
        self.assertTrue("[WARNING] Identieke datum en score voor records OD-202 en OD-102" in f1.getvalue())
        self.assertTrue("[WARNING] Score niet consecutief voor records OD-401 en OD-400 (400 >= 300)" in f1.getvalue())

    def test_verkeerde_soort_record(self):
        with self.assert_max_queries(30):
            f1, f2 = self.run_management_command('import_records', TEST_FILE_VERKEERDE_SOORT)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Max score (afgeleide van aantal pijlen) is niet consistent in soort" in f1.getvalue())

    def test_wa_renames(self):
        # IB is hernoemd naar TR, maar in de administratie ondersteunen we beide
        # Master/Senior/Junior/Cadet zijn hernoemd naar 50+/21+/Onder 21/Onder 18
        f1, f2 = self.run_management_command('import_records', TEST_FILE_WA_RENAMES)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('5 toegevoegd; 0 waarschuwingen, 0 fouten' in f2.getvalue())

# end of file
