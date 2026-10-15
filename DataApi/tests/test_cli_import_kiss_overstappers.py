# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.models import DataApiVereniging, DataApiLidmaatschap
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import csv
import os

CLI_IMPORT_KISS_OVERSTAPPERS = 'import_kiss_overstappers'

TESTFILE_NOT_EXISTING = './DataApi/does-not-exist'
TEST_KISS_PAD = './DataApi/test/'
CUT_OFF_DATE = '2001-10-01'


class TestDataApiCliImportKissOverstappers(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, management commando import_kiss_overstappers"""

    def setUp(self):
        self._tmp_dir = None

    def tearDown(self):
        if self._tmp_dir:               # pragma: no branch
            self._tmp_dir.cleanup()

    def _maak_test_csvs(self):
        # handmatig opruimen als deze functie 2x aangeroepen wordt
        if self._tmp_dir:               # pragma no cover
            self._tmp_dir.cleanup()
        # maak tijdelijke directory; wordt automatisch verwijderd
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.csv_path = self._tmp_dir.name

        self.csv_1 = os.path.join(self.csv_path, 'kiss-overstappers-1.csv')
        with open(self.csv_1, "w") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['#', 'Lid', 'Lid', 'Vereniging', 'Vereniging', 'Overschrijving', 'Overschrijving', 'Vereniging', 'Vereniging'])
            writer.writerow(['1', '100001', 'Bos Jager', '1001', 'Bosjagers', '31-05-2001', '01-06-2001', '1002', 'Veldschutters'])
            writer.writerow(['1', '100001', 'Bos Jager', '1002', 'Veldschutters', '15-07-2001', '01-08-2001', '1002', 'Veldschutters'])     # naar zelfde vereniging
            writer.writerow(['1', '100042', 'On Bekend', '1001', 'Bosjagers', '31-05-2001', '01-06-2001', '1002', 'Veldschutters'])         # geen lms gevonden

        DataApiLidmaatschap.objects.create(
                lid_nr=100001,
                ver_nr=1001,
                aanmeld_datum='2001-01-01',
                geboorte_datum='01-01-1990',
                geslacht='V',
                land_iso='NL',
                postcode='4444CC')

        # zonder de eerste kolom
        self.csv_2 = os.path.join(self.csv_path, 'kiss-overstappers-2.csv')
        with open(self.csv_2, "w") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Lid', 'Lid', 'Vereniging', 'Vereniging', 'Overschrijving', 'Overschrijving', 'Vereniging', 'Vereniging'])
            writer.writerow(['100002', 'Bos Jager', '1001', 'Bosjagers', '01-05-2001', '01-06-2001', '1002', 'Veldschutters'])
            writer.writerow(['100003', 'Bas Jager', '1001', 'Bosjagers', '10-10-2001', '01-11-2001', '1002', 'Veldschutters'])  # > cut-off-datum
            writer.writerow(['100004', 'Bes Jager', '1001', 'Bosjagers', '01-05-2001', '01-06-2001', '1002', 'Veldschutters'])  # geen passend lms

        # 1 ouder record, moet overgeslagen worden
        DataApiLidmaatschap.objects.create(
                lid_nr=100002,
                ver_nr=1000,
                aanmeld_datum='2000-01-01',
                afmeld_datum='2000-12-31',
                geboorte_datum='01-01-1990',
                geslacht='V',
                land_iso='NL',
                postcode='4444CC')

        DataApiLidmaatschap.objects.create(
                lid_nr=100002,
                ver_nr=1001,
                aanmeld_datum='2001-01-01',
                geboorte_datum='01-01-1990',
                geslacht='V',
                land_iso='NL',
                postcode='4444CC')

        DataApiLidmaatschap.objects.create(
                lid_nr=100004,
                ver_nr=1042,
                aanmeld_datum='2000-01-01',
                afmeld_datum='',
                geboorte_datum='01-01-1990',
                geslacht='V',
                land_iso='NL',
                postcode='4444CC')


    def test_overstappers(self):
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_OVERSTAPPERS,
                                             TESTFILE_NOT_EXISTING,
                                             CUT_OFF_DATE,
                                             report_exit_code=False)
        self.assertTrue('[TEST] Management command raised SystemExit(1)' in f1.getvalue())

        self._maak_test_csvs()
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_OVERSTAPPERS,
                                             self.csv_1,
                                             CUT_OFF_DATE)
        print(f1.getvalue())
        print(f2.getvalue())
        self.assertEqual(f1.getvalue(), '')
        #self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

        # dry-run, for extra coverage
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_OVERSTAPPERS,
                                             self.csv_2,
                                             CUT_OFF_DATE,
                                             '--dryrun')
        print(f1.getvalue())
        print(f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_OVERSTAPPERS,
                                             self.csv_2,
                                             CUT_OFF_DATE)
        print(f1.getvalue())
        print(f2.getvalue())
        self.assertEqual(f1.getvalue(), '')
        #self.assertTrue('[WARNING] Overstap onduidelijk voor lid 100004 weg van ver 1001' in f2.getvalue())

        # herhaal zelfde bestand --> geen nieuwe mutatie
        c1 = DataApiLidmaatschap.objects.count()
        self.run_management_command(CLI_IMPORT_KISS_OVERSTAPPERS,
                                    self.csv_2,
                                    CUT_OFF_DATE)
        c2 = DataApiLidmaatschap.objects.count()
        self.assertEqual(c1, c2)

        # UnicodeDecodeError
        with open(self.csv_1, "ab") as f:
            f.write(b'10002;Kl\xE1 club;;99999999;Str\\U;;1111AA;Boogstad\n')
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_OVERSTAPPERS,
                                             self.csv_1,
                                             CUT_OFF_DATE,
                                             report_exit_code=False)
        self.assertTrue("[ERROR] Bestand heeft unicode problemen" in f2.getvalue())


# end of file
