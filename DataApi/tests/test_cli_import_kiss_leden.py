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
        self._tmp_dir.cleanup()

    def _maak_test_csvs(self):
        # handmatig opruimen als deze functie 2x aangeroepen wordt
        if self._tmp_dir:               # pragma no cover
            self._tmp_dir.cleanup()
        # maak tijdelijke directory; wordt automatisch verwijderd
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.csv_path = self._tmp_dir.name

        # record bij oude vereniging krijgt kleine correctie
        DataApiLidmaatschap.objects.create(
                lid_nr=100003,
                ver_nr=1002,
                aanmeld_datum='2000-01-01',
                afmeld_datum='2020-08-20',          # wordt gecorrigeerd naar 2020-09-01
                geboorte_datum='1970-01-01',
                geslacht='V',
                land_iso='NL',
                postcode='1111CC')

        # record voor mutaties
        DataApiLidmaatschap.objects.create(
                lid_nr=100003,
                ver_nr=1001,
                aanmeld_datum='2020-09-02',
                afmeld_datum='',
                geboorte_datum='1990-01-01',        # niet 1970-01-01
                geslacht='X',                       # niet V
                land_iso='NL',
                postcode='4444CC')                  # niet 1111 CC

        # lms dat al in de database stond
        DataApiLidmaatschap.objects.create(
                lid_nr=100004,
                ver_nr=1002,
                aanmeld_datum='2020-01-01',
                afmeld_datum='',
                geboorte_datum='1970-01-01',
                geslacht='M',
                land_iso='NL',
                postcode='1111DD')

        # record dat afgemeld gaat worden
        DataApiLidmaatschap.objects.create(
                lid_nr=100009,
                ver_nr=1000,
                aanmeld_datum='2000-01-01',
                afmeld_datum='',
                geboorte_datum='1990-01-01',
                geslacht='X',
                land_iso='NL',
                postcode='4444CC')

        self.csv_1 = os.path.join(self.csv_path, 'kiss-leden-%s.csv' % self.jaar)
        with open(self.csv_1, "w") as f:
            writer = csv.writer(f, delimiter=';')
            # al deze velden worden gebruikt
            writer.writerow(['Postcode', 'Geboortedatum', 'Geslacht', 'BondIngangsdatum', 'Sporttak',      'Verenigingscode'])
            writer.writerow(['1111 AA',  '01-01-1970',    'M',        '06-06-2018',       'handboogsport', '1001'])
            writer.writerow(['1111 BB',  '01-01-1970',    'V',        '06-06-2018',       'handboogsport', '1000'])
            writer.writerow(['1111 CC',  '01-01-1970',    'V',        '06-06-2018',       'handboogsport', '1001'])
            writer.writerow(['1111 DD',  '01-01-1970',    'M',        '01-01-2020',       'handboogsport', '1002'])

        self.csv_2 = os.path.join(self.csv_path, 'kiss-leden-met-lidnr-%s.csv' % self.jaar)
        with open(self.csv_2, "w") as f:
            writer = csv.writer(f, delimiter=';')
            # alleen veel Relatienummer (getal) en Aanvangsdatum worden gebruikt
            writer.writerow(['#', 'Relatienummer', 'Relatienummer', '#', 'Postcode', 'Geboortedatum', 'Geslacht', 'Aanvangsdatum', 'Discipline'])
            writer.writerow(['1', '100001',        'Naam 1',        '1', '1111 AA',  '01-01-1970',    'M',        '06-06-2018',    'handboogsport'])
            writer.writerow(['2', '100002',        'Naam 2',        '2', '1111 BB',  '01-01-1970',    'V',        '06-06-2018',    'handboogsport'])
            writer.writerow(['3', '100003',        'Naam 3',        '3', '1111 CC',  '01-01-1970',    'V',        '06-06-2018',    'handboogsport'])
            writer.writerow(['4', '100004',        'Naam 4',        '4', '1111 DD',  '01-01-1970',    'M',        '01-01-2020',    'handboogsport'])

        self.csv_3 = os.path.join(self.csv_path, 'overstappers-%s.csv' % self.jaar)
        with open(self.csv_3, "w") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Lid',    'Lid',    'Vereniging', 'Vereniging', 'Overschrijving', 'Overschrijving', 'Vereniging', 'Vereniging'])

            # 100001 vertrekt uit verkeerde vereniging
            writer.writerow(['100001', 'Naam 1', '1000',       'Ver 1',      '31-07-2020',     '01-08-2020',     '1001',       'Ver 2'])

            # 100001 overstap naar dezelfde vereniging
            writer.writerow(['100001', 'Naam 1', '1001',       'Ver 2',      '01-09-2020',     '02-09-2020',     '1001',       'Ver 2'])

            # 100003 overstap stond al in het systeem
            writer.writerow(['100003', 'Naam 3', '1002',       'Ver 3',      '01-09-2020',     '02-09-2020',     '1001',       'Ver 2'])

            # 100004 nieuwe overstap
            writer.writerow(['100004', 'Naam 4', '1002',       'Ver 3',      '01-05-2020',     '02-05-2020',     '1000',       'Ver 1'])

    def test_leden(self):
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_LEDEN,
                                             TEST_KISS_PAD,
                                             1900,
                                             report_exit_code=False)
        # f1 bevat "[TEST] Management command raised SystemExit(1)"
        # self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

        self._maak_test_csvs()

        # dryrun: geeft extra coverage and side-effects
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_LEDEN,
                                             self.csv_path,
                                             self.jaar,
                                             '--dryrun')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Geen lms gevonden voor overstapper lid 100001' in f2.getvalue())    # komt door dryrun

        # echt import: mutaties, overstappers
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_LEDEN,
                                             self.csv_path,
                                             self.jaar)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[WARNING] Overstap onduidelijk voor lid 100001 weg van ver 1000" in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100001 stapt over naar dezelfde vereniging 1001" in f2.getvalue())
        self.assertTrue("[INFO] Samenvatting jaar 2020: 2 gevonden, 3 aangemaakt, 1 afgemeld, 6 wijzigingen" in f2.getvalue())
        self.assertTrue("[INFO] 4 actieve lidmaatschappen" in f2.getvalue())

        # nog een keer, nu zijn er geen mutaties meer
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_LEDEN,
                                             self.csv_path,
                                             self.jaar)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        lid = DataApiLidmaatschap.objects.first()
        self.assertIsNotNone(lid)
        self.assertTrue(str(lid) != '')     # coverage


# end of file
