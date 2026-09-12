# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management import call_command
from ImportCRM.models import ImportLimieten
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import csv
import os
import io


IMPORT_HISTCRM_COMMANDO = 'import_histcrm_json'
IMPORT_KISS_LEDEN_COMMANDO = 'import_kiss_leden'
IMPORT_KISS_VERENIGINGEN_COMMANDO = 'import_kiss_verenigingen'

TESTFILE_NOT_EXISTING = './DataApi/does-not-exist'
TEST_KISS_PAD = './DataApi/test/'
AFMELD_DATUM = '2026-09-07'


class TestDataApiCli(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, management commando's """

    def setUp(self):
        # maak een paar testbestanden aan
        self._tmp_dir = None
        self.csv_path = ''
        self.jaar = 2020

    def tearDown(self):
        if self._tmp_dir:
            self._tmp_dir.cleanup()

    def _maak_test_csvs(self):
        # maak tijdelijke directory; wordt automatisch verwijderd
        if self._tmp_dir:
            self._tmp_dir.cleanup()
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.csv_path = self._tmp_dir.name

        self.csv_1 = os.path.join(self.csv_path, 'kiss-leden-%s.csv' % self.jaar)
        with open(self.csv_1, "w") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Postcode', 'Geboortedatum', 'Geslacht', 'BondIngangsdatum', 'Sporttak', 'Verenigingscode'])
            writer.writerow(['1111 AA', '01-01-1970', 'M', '06-06-2018', 'handboogsport', '1001'])
            writer.writerow(['1111 AA', '01-01-1970', 'V', '06-06-2018', 'handboogsport', '1000'])

        self.csv_2 = os.path.join(self.csv_path, 'kiss-leden-met-lidnr-%s.csv' % self.jaar)
        with open(self.csv_2, "w") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['#', 'Relatienummer', 'Relatienummer', '#', 'Postcode', 'Geboortedatum', 'Geslacht', 'Aanvangsdatum', 'Discipline'])
            writer.writerow(['1', '100001', 'Naam 1', '1', '1111 AA', '01-01-1970', 'M', '06-06-2018', 'handboogsport'])
            writer.writerow(['2', '100002', 'Naam 2', '2', '1111 AA', '01-01-1970', 'V', '06-06-2018', 'handboogsport'])

        self.csv_3 = os.path.join(self.csv_path, 'overstappers-%s.csv' % self.jaar)
        with open(self.csv_3, "w") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Lid', 'Lid', 'Vereniging', 'Vereniging', 'Overschrijving', 'Overschrijving', 'Vereniging', 'Vereniging'])
            writer.writerow(['100001', 'Naam 1', '1000', 'Ver 1', '31-07-2020', '01-08-2020', '1001', 'Ver 2'])

    def test_params(self):
        f1, f2 = self.run_management_command(IMPORT_HISTCRM_COMMANDO,
                                             TESTFILE_NOT_EXISTING,
                                             AFMELD_DATUM)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

        f1, f2 = self.run_management_command(IMPORT_KISS_LEDEN_COMMANDO,
                                             TEST_KISS_PAD,
                                             1900,
                                             report_exit_code=False)
        # f1 bevat "[TEST] Management command raised SystemExit(1)"
        # self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

        f1, f2 = self.run_management_command(IMPORT_KISS_VERENIGINGEN_COMMANDO,
                                             TEST_KISS_PAD,
                                             report_exit_code=False)
        # f1 bevat "[TEST] Management command raised SystemExit(1)"
        # self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

    def test_leden(self):
        self._maak_test_csvs()
        f1, f2 = self.run_management_command(IMPORT_KISS_LEDEN_COMMANDO,
                                             self.csv_path,
                                             self.jaar,
                                             report_exit_code=False)
        print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

# end of file
