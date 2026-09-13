# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from DataApi.models import DataApiVereniging, DataApiLidmaatschap
from TestHelpers.e2ehelpers import E2EHelpers
import json

CLI_IMPORT_HISTCRM = 'import_histcrm_json'
CLI_IMPORT_KISS_LEDEN = 'import_kiss_leden'
CLI_IMPORT_KISS_VERENIGINGEN = 'import_kiss_verenigingen'
CLI_CHECK_DATA_KWALITEIT = 'check_data_kwaliteit'

TESTFILE_NOT_EXISTING = './DataApi/does-not-exist'
TEST_KISS_PAD = './DataApi/test/'
AFMELD_DATUM = '2026-09-07'


class TestDataApiViews(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, management commando's """

    url_api_ver1 = '/data-api/v1/verenigingen'
    url_api_ver2 = '/data-api/v1/verenigingen/'
    url_api_acc1 = '/data-api/v1/accommodaties'
    url_api_acc2 = '/data-api/v1/accommodaties/'
    url_api_lms1 = '/data-api/v1/lidmaatschappen'
    url_api_lms2 = '/data-api/v1/lidmaatschappen/'
    url_api_no_endpoint1 = '/data-api/'
    url_api_no_endpoint2 = '/data-api/v1/'
    url_api_no_endpoint3 = '/data-api/v1/test'
    url_api_no_endpoint4 = '/data-api/v1/test/'
    url_api_no_endpoint5 = '/data-api/v1/test/sub/'

    def setUp(self):
        # actief
        DataApiVereniging.objects.create(
                ver_nr=1000,
                naam='Grote club',
                aanmeld_datum='2000-01-03',
                afmeld_datum='',
                kvk_nummer='12345678',
                straatnaam='Pijlstraat',
                huisnummer=42,
                postcode='1111AA',
                plaats='Boogstad',
                land_iso='NL',
                lat='4.0',
                lon='55.1')

        # afgemeld
        DataApiVereniging.objects.create(
                ver_nr=1001,
                naam='Kleine club',
                aanmeld_datum='2020-01-01',
                afmeld_datum='2022-12-31',
                kvk_nummer='12345679',
                straatnaam='Pijlstraat',
                huisnummer=42,
                postcode='1111AA',
                plaats='Boogstad',
                land_iso='NL',
                lat='',
                lon='')

        # geen accommodatie
        DataApiVereniging.objects.create(
                ver_nr=1002,
                naam='Geen acc club',
                aanmeld_datum='2025-01-01',
                afmeld_datum='',
                kvk_nummer='12345680',
                straatnaam='',
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

        # ex-lid bij afgemelde vereniging
        DataApiLidmaatschap.objects.create(
                lid_nr=100002,
                ver_nr=1001,
                aanmeld_datum='2021-06-01',
                afmeld_datum='2022-12-31',
                geboorte_datum='1972-01-01',
                geslacht='X',
                land_iso='BE',
                postcode='1234')

        # lid bij ver zonder accommodatie
        DataApiLidmaatschap.objects.create(
                lid_nr=100003,
                ver_nr=1002,
                aanmeld_datum='2025-06-01',
                afmeld_datum='',
                geboorte_datum='2001-01-01',
                geslacht='M',
                land_iso='NL',
                postcode='9999ZZ')

        self.headers = {'DDI-Token': settings.DDI_AUTH_TOKEN}

    def test_no_token(self):
        rsp = self.client.get(self.url_api_ver1)
        self.assertEqual(rsp.status_code, 401)
        self.assertEqual(rsp.content, b'No valid token\n')

        rsp = self.client.get(self.url_api_ver2)
        self.assertEqual(rsp.status_code, 401)
        self.assertEqual(rsp.content, b'No valid token\n')

        rsp = self.client.get(self.url_api_acc1)
        self.assertEqual(rsp.status_code, 401)
        self.assertEqual(rsp.content, b'No valid token\n')

        rsp = self.client.get(self.url_api_acc2)
        self.assertEqual(rsp.status_code, 401)
        self.assertEqual(rsp.content, b'No valid token\n')

        rsp = self.client.get(self.url_api_lms1)
        self.assertEqual(rsp.status_code, 401)
        self.assertEqual(rsp.content, b'No valid token\n')

        rsp = self.client.get(self.url_api_lms2)
        self.assertEqual(rsp.status_code, 401)
        self.assertEqual(rsp.content, b'No valid token\n')

    def test_no_endpoint(self):
        for url in (self.url_api_no_endpoint1, self.url_api_no_endpoint2, self.url_api_no_endpoint3,
                    self.url_api_no_endpoint4, self.url_api_no_endpoint5):
            rsp = self.client.get(url)
            self.assertEqual(rsp.status_code, 400)
        # for

    def test_api_ver(self):
        rsp = self.client.get(self.url_api_ver1, headers=self.headers)
        self.assertEqual(rsp.status_code, 200)
        # print(rsp.content)

        data = json.loads(rsp.content)
        self.assertEqual(data['meta']['count'], 3)
        self.assertEqual(data['meta']['total'], 3)
        vers = data['Verenigingsgegevens']
        self.assertEqual(len(vers), 3)

        ver = vers[0]
        self.assertEqual(ver['Verenigingscode'], '1000')
        self.assertEqual(ver['Naam'], 'Grote club')
        self.assertEqual(ver['Aanmelddatum'], '2000-01-03')
        self.assertEqual(ver['KVKnummer'], '12345678')
        accs = ver['Accommodaties']
        self.assertEqual(len(accs), 1)
        acc = accs[0]
        self.assertEqual(acc['Postcode'], '1111AA')
        self.assertEqual(acc['Huisnummer'], 42)

    def test_api_acc(self):
        rsp = self.client.get(self.url_api_acc1, headers=self.headers)
        self.assertEqual(rsp.status_code, 200)
        # print(rsp.content)

        data = json.loads(rsp.content)
        self.assertEqual(data['meta']['count'], 2)
        self.assertEqual(data['meta']['total'], 2)
        accs = data['Accommodatiegegevens']
        self.assertEqual(len(accs), 2)

        acc = accs[0]
        self.assertEqual(acc['Naam'], 'Grote club')
        self.assertEqual(acc['Postcode'], '1111AA')
        self.assertEqual(acc['Straat'], 'Pijlstraat')
        self.assertEqual(acc['Huisnummer'], 42)
        self.assertEqual(acc['Plaats'], 'Boogstad')
        self.assertEqual(acc['Land'], 'NL')
        self.assertEqual(acc['Latitude'], '4.0')
        self.assertEqual(acc['Longitude'], '55.1')


# end of file
