# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.models import DataApiVereniging, DataApiLidmaatschap
from TestHelpers.e2ehelpers import E2EHelpers

CLI_CHECK_DATA_KWALITEIT = 'check_data_kwaliteit'


class TestDataApiCli(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, management commando check_data_kwaliteit """

    def setUp(self):
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

        DataApiLidmaatschap.objects.create(
                lid_nr=100006,
                ver_nr=42,
                aanmeld_datum='2022+06+02',     # fout formaat
                afmeld_datum='2023-01-01',
                geboorte_datum='1999-01-01',
                geslacht='V',
                land_iso='BE',
                postcode='1234')

    def test_kwaliteit(self):
        f1, f2 = self.run_management_command(CLI_CHECK_DATA_KWALITEIT)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[ERROR] Vereniging 1001 is afgemeld per 2022-12-31 maar heeft nog 1 lidmaatschappen:" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1001 is afgemeld per 2022-12-31 maar 1 lidmaatschappen lopen langer door:"  in f2.getvalue())
        self.assertTrue("[ERROR] Lid 100002 heeft meerdere actieve lms:" in f2.getvalue())
        self.assertTrue("[WARNING] Niet standaard postcode '1234' (land NL) voor Lid 100002" in f2.getvalue())
        self.assertTrue("[ERROR] Onbekende vereniging 1003 voor lms Lid 100003" in f2.getvalue())
        self.assertTrue("[WARNING] Onverwachte land code: 'XX' in Lid 100003" in f2.getvalue())
        self.assertTrue("[ERROR] Illegale aanmelddatum '2022+06+02' in " in f2.getvalue())


# end of file
