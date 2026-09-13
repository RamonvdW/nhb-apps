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


CLI_IMPORT_HISTCRM = 'import_histcrm_json'
CLI_IMPORT_KISS_LEDEN = 'import_kiss_leden'
CLI_IMPORT_KISS_VERENIGINGEN = 'import_kiss_verenigingen'
CLI_CHECK_DATA_KWALITEIT = 'check_data_kwaliteit'

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

    def _maak_data(self):
        # actief
        DataApiVereniging.objects.create(
                ver_nr=1000,
                naam='Grote club',
                aanmeld_datum='2000-01-01',
                afmeld_datum='',
                kvk_nummer='12345678',
                straatnaam='Pijlstraat',
                huisnummer=42,
                postcode='1111AA',
                plaats='Boogstad',
                land_iso='NL',
                lat='',
                lon='')

        # afgemeld
        DataApiVereniging.objects.create(
                ver_nr=1001,
                naam='Kleine club',
                aanmeld_datum='2020-01-01',
                afmeld_datum='2022-12-31',
                kvk_nummer='12345678',
                straatnaam='Pijlstraat',
                huisnummer=42,
                postcode='1111AA',
                plaats='Boogstad',
                land_iso='NL',
                lat='',
                lon='')

        # afgemeld, geen leden
        # geen accommodatie
        DataApiVereniging.objects.create(
                ver_nr=1002,
                naam='Afgemelde club',
                aanmeld_datum='2020-01-01',
                afmeld_datum='2022-12-31',
                kvk_nummer='12345678',
                straatnaam='Pijlstraat',
                huisnummer=0,
                postcode='',
                plaats='',
                land_iso='NL',
                lat='',
                lon='')

        DataApiLidmaatschap.objects.create(
                lid_nr=100001,
                ver_nr=1000,
                aanmeld_datum='2001-06-01',
                afmeld_datum='',
                geboorte_datum='1972-01-01',
                geslacht='X',
                land_iso='NL',
                postcode='1234AB')

        DataApiLidmaatschap.objects.create(
                lid_nr=100002,
                ver_nr=1000,
                aanmeld_datum='2001-06-01',
                afmeld_datum='',
                geboorte_datum='1972-01-01',
                geslacht='X',
                land_iso='NL',
                postcode='1234')        # fout

        # actief lid bij afgemelde ver
        DataApiLidmaatschap.objects.create(
                lid_nr=100002,
                ver_nr=1001,
                aanmeld_datum='2025-06-01',
                afmeld_datum='',
                geboorte_datum='1972-01-01',
                geslacht='X',
                land_iso='NL',
                postcode='1234')        # fout

        DataApiLidmaatschap.objects.create(
                lid_nr=100003,
                ver_nr=1003,            # fout
                aanmeld_datum='2024-06-02',
                afmeld_datum='2024-12-31',
                geboorte_datum='1999-01-01',
                geslacht='M',
                land_iso='XX',          # fout
                postcode='1234')

        # afgemeld lid bij afgemelde ver
        DataApiLidmaatschap.objects.create(
                lid_nr=100004,
                ver_nr=1001,
                aanmeld_datum='2022-06-02',
                afmeld_datum='2022-12-30',      # moet voor 2022-12-31 zijn
                geboorte_datum='1999-01-01',
                geslacht='M',
                land_iso='BE',
                postcode='1234')

        DataApiLidmaatschap.objects.create(
                lid_nr=100005,
                ver_nr=1001,
                aanmeld_datum='2022-06-02',
                afmeld_datum='2023-01-01',      # moet na 2022-12-31 zijn
                geboorte_datum='1999-01-01',
                geslacht='V',
                land_iso='BE',
                postcode='1234')

    def test_histcrm(self):
        f1, f2 = self.run_management_command(CLI_IMPORT_HISTCRM,
                                             TESTFILE_NOT_EXISTING,
                                             AFMELD_DATUM)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

    def test_verenigingen(self):
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_VERENIGINGEN,
                                             TEST_KISS_PAD,
                                             report_exit_code=False)
        # f1 bevat "[TEST] Management command raised SystemExit(1)"
        # self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

        self._maak_test_csvs()

        # 1e run: dryrun
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_VERENIGINGEN,
                                             self.csv_path,
                                             '--dryrun')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Samenvatting: 0 gevonden, 2 aangemaakt, 0 afgemeld, 0 wijzigingen" in f2.getvalue())
        self.assertTrue("[INFO] 0 actieve verenigingen" in f2.getvalue())

        # 2e run: verenigingen worden aangemaakt
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_VERENIGINGEN,
                                             self.csv_path)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Samenvatting: 0 gevonden, 2 aangemaakt, 0 afgemeld, 0 wijzigingen" in f2.getvalue())
        self.assertTrue("[INFO] 2 actieve verenigingen" in f2.getvalue())

        ver = DataApiVereniging.objects.get(ver_nr=1000)
        self.assertEqual(ver.ver_nr, 1000)
        self.assertEqual(ver.naam, 'Grote club')
        self.assertEqual(ver.aanmeld_datum, '2020-02-01')
        self.assertEqual(ver.afmeld_datum, '')
        self.assertEqual(ver.kvk_nummer, '12345678')
        self.assertEqual(ver.straatnaam, 'Pijlstraat')
        self.assertEqual(ver.huisnummer, 42)
        self.assertEqual(ver.postcode, '1111AA')
        self.assertEqual(ver.plaats, 'Boogstad')
        self.assertEqual(ver.land_iso, 'NL')
        self.assertEqual(ver.lat, '')
        self.assertEqual(ver.lon, '')

        ver = DataApiVereniging.objects.get(ver_nr=1001)
        self.assertEqual(ver.ver_nr, 1001)
        self.assertEqual(ver.naam, 'Kleine club')
        self.assertEqual(ver.aanmeld_datum, '')
        self.assertEqual(ver.afmeld_datum, '')
        self.assertEqual(ver.kvk_nummer, '12345679')
        self.assertEqual(ver.straatnaam, 'Pijlstraat')
        self.assertEqual(ver.huisnummer, 0)
        self.assertEqual(ver.postcode, '1111AA')
        self.assertEqual(ver.plaats, 'Boogstad')
        self.assertEqual(ver.land_iso, 'NL')
        self.assertEqual(ver.lat, '')
        self.assertEqual(ver.lon, '')

        self.assertTrue(str(ver) != '')     # coverage

        # 3e run: verenigingen bestaan al
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_VERENIGINGEN,
                                             self.csv_path)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Samenvatting: 2 gevonden, 0 aangemaakt, 0 afgemeld, 0 wijzigingen" in f2.getvalue())
        self.assertTrue("[INFO] 2 actieve verenigingen" in f2.getvalue())

        # UnicodeDecodeError
        with open(self.csv_4, "a") as f:
            f.write('\\U')
        f1, f2 = self.run_management_command(CLI_IMPORT_KISS_VERENIGINGEN,
                                             self.csv_path,
                                             report_exit_code=False)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[ERROR] Bestand heeft unicode problemen" in f2.getvalue())

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

    def test_kwaliteit(self):
        self._maak_data()

        f1, f2 = self.run_management_command(CLI_CHECK_DATA_KWALITEIT)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[ERROR] Vereniging 1001 is afgemeld per 2022-12-31 maar heeft nog 1 lidmaatschappen:" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1001 is afgemeld per 2022-12-31 maar 1 lidmaatschappen lopen langer door:"  in f2.getvalue())
        self.assertTrue("[ERROR] Lid 100002 heeft meerdere actieve lms:" in f2.getvalue())
        self.assertTrue("[WARNING] Niet standaard postcode '1234' (land NL) voor Lid 100002" in f2.getvalue())
        self.assertTrue("[ERROR] Onbekende vereniging 1003 voor lms Lid 100003" in f2.getvalue())
        self.assertTrue("[WARNING] Onverwachte land code: 'XX' in Lid 100003" in f2.getvalue())


# end of file
