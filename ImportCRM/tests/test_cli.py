# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management import call_command
from TestHelpers.e2ehelpers import E2EHelpers
import io


DUMP_EDUCATIONS_COMMAND = 'dump_educations'

TESTFILES_PATH = './ImportCRM/test-files/'

TESTFILE_NOT_EXISTING = TESTFILES_PATH + 'notexisting.json'             # noqa
TESTFILE_01_EMPTY = TESTFILES_PATH + 'testfile_01.json'
TESTFILE_02_INCOMPLETE = TESTFILES_PATH + 'testfile_02.json'
TESTFILE_03_BASE_DATA = TESTFILES_PATH + 'testfile_03.json'
TESTFILE_04_UNICODE_ERROR = TESTFILES_PATH + 'testfile_04.json'
TESTFILE_05_MISSING_KEYS = TESTFILES_PATH + 'testfile_05.json'
TESTFILE_06_BAD_RAYON_REGIO = TESTFILES_PATH + 'testfile_06.json'
TESTFILE_07_NO_CLUBS = TESTFILES_PATH + 'testfile_07.json'
TESTFILE_08_VER_MUTATIES = TESTFILES_PATH + 'testfile_08.json'
TESTFILE_09_LID_MUTATIES = TESTFILES_PATH + 'testfile_09.json'
TESTFILE_10_TOEVOEGING_NAAM = TESTFILES_PATH + 'testfile_10.json'
TESTFILE_11_BAD_DATE = TESTFILES_PATH + 'testfile_11.json'
TESTFILE_12_MEMBER_INCOMPLETE_1 = TESTFILES_PATH + 'testfile_12.json'
TESTFILE_13_WIJZIG_GESLACHT_1 = TESTFILES_PATH + 'testfile_13.json'
TESTFILE_14_WIJZIG_GESLACHT_2 = TESTFILES_PATH + 'testfile_14.json'
TESTFILE_15_CLUB_1377 = TESTFILES_PATH + 'testfile_15.json'
TESTFILE_16_VERWIJDER_LID = TESTFILES_PATH + 'testfile_16.json'
TESTFILE_17_MEMBER_INCOMPLETE_2 = TESTFILES_PATH + 'testfile_17.json'
TESTFILE_18_LID_UITGESCHREVEN = TESTFILES_PATH + 'testfile_18.json'
TESTFILE_19_STR_NOT_NR = TESTFILES_PATH + 'testfile_19.json'
TESTFILE_20_SPEELSTERKTE = TESTFILES_PATH + 'testfile_20.json'
TESTFILE_21_IBAN_BIC = TESTFILES_PATH + 'testfile_21.json'
TESTFILE_22_CRASH = TESTFILES_PATH + 'testfile_22.json'
TESTFILE_23_DIPLOMA = TESTFILES_PATH + 'testfile_23.json'


class TestImportCRMImport(E2EHelpers, TestCase):

    """ tests voor de ImportCRM applicatie, management commando dump_educations """

    # CRM bestanden met wijzigende volgorde van tabellen te vinden (no order_by)

    def test_file_not_found(self):
        # afhandelen niet bestaand bestand
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(DUMP_EDUCATIONS_COMMAND,
                                                 TESTFILE_NOT_EXISTING)

        self.assertTrue(f1.getvalue().startswith('[ERROR] Bestand kan niet gelezen worden'))
        # self.assertEqual(f2.getvalue(), '')

    def test_bad_json(self):
        # afhandelen slechte/lege JSON file
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(DUMP_EDUCATIONS_COMMAND,
                                                 TESTFILE_01_EMPTY)

        self.assertTrue(f1.getvalue().startswith('[ERROR] Probleem met het JSON formaat in bestand'))
        # self.assertEqual(f2.getvalue(), '')

    def test_import(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(DUMP_EDUCATIONS_COMMAND,
                                                 TESTFILE_23_DIPLOMA)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

    def test_unicode_error(self):
        # UnicodeDecodeError
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(DUMP_EDUCATIONS_COMMAND,
                                                 TESTFILE_04_UNICODE_ERROR)
        self.assertTrue(
            "[ERROR] Bestand heeft unicode problemen ('rawunicodeescape' codec can't decode bytes in position 180-181:"
            in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_bad_nrs(self):
        # controleer dat de import tegen niet-nummers kan
        f1, f2 = self.run_management_command(DUMP_EDUCATIONS_COMMAND,
                                             TESTFILE_19_STR_NOT_NR)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

    def test_crash(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(SystemExit):
            call_command(DUMP_EDUCATIONS_COMMAND,
                         TESTFILE_02_INCOMPLETE,  # triggers crash
                         stderr=f1,  # noodzakelijk voor de test!
                         stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())


# end of file
