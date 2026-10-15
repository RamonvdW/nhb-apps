# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.models import DataApiLidmaatschap
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import csv
import os

CLI_IMPORT_KISS_LEDEN = 'import_kiss_leden'
TEST_KISS_PAD = './DataApi/test/'


class TestDataApiCliImportKissLeden(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, management commando import_kiss_leden """

    def setUp(self):
        # maak een paar testbestanden aan
        self._tmp_dir = None
        self.csv_path = ''
        self.jaar = 2020

    def tearDown(self):
        if self._tmp_dir:
            self._tmp_dir.cleanup()

    def _maak_test_csvs(self):
        # handmatig opruimen als deze functie 2x aangeroepen wordt
        if self._tmp_dir:               # pragma no cover
            self._tmp_dir.cleanup()
        # maak tijdelijke directory; wordt automatisch verwijderd
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

        self.csv_4 = os.path.join(self.csv_path, "all-verenigingen.csv")
        with open(self.csv_4, "w") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Relatienummer', 'Naam', 'Status', 'Oprichtingsdatum', 'KvK Nummer', 'Adres - Straatnaam', 'Adres - Huisnummer', 'Adres - Postcode', 'Adres - Plaatsnaam'])
            writer.writerow(['1000', 'Grote club', 'Actief', '01-02-2020', '12345678', 'Pijlstraat', '42', '1111AA', 'Boogstad'])

            # geen huisnr
            # geen oprichtsdatum
            writer.writerow(['1001', 'Kleine club', 'Actief', '', '12345679', 'Pijlstraat', '', '1111AA', 'Boogstad'])

    def test_leden(self):
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_LEDEN,
                                             TEST_KISS_PAD,
                                             1900,
                                             report_exit_code=False)
        # f1 bevat "[TEST] Management command raised SystemExit(1)"
        # self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

        self._maak_test_csvs()

        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_LEDEN,
                                             self.csv_path,
                                             self.jaar,
                                             report_exit_code=False)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_LEDEN,
                                             self.csv_path,
                                             self.jaar,
                                             report_exit_code=False)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        lid = DataApiLidmaatschap.objects.first()
        self.assertIsNotNone(lid)
        self.assertTrue(str(lid) != '')     # coverage


# end of file
