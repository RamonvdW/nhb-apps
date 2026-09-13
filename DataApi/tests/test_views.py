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
        with self.assert_max_queries(20):
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

        # bad token
        rsp = self.client.get(self.url_api_lms2, headers={'DDI-Token': 'bad'})
        self.assertEqual(rsp.status_code, 401)
        self.assertEqual(rsp.content, b'No valid token\n')

    def test_no_endpoint(self):
        for url in (self.url_api_no_endpoint1, self.url_api_no_endpoint2, self.url_api_no_endpoint3,
                    self.url_api_no_endpoint4, self.url_api_no_endpoint5):
            rsp = self.client.get(url)
            self.assertEqual(rsp.status_code, 400)
        # for

    def test_api_ver(self):
        with self.assert_max_queries(20):
            rsp = self.client.get(self.url_api_ver1, headers=self.headers)
        self.assertEqual(rsp.status_code, 200)
        # print(rsp.content)

        data = json.loads(rsp.content)
        self.assertEqual(data['meta']['count'], 3)
        self.assertEqual(data['meta']['total'], 3)
        ver_lijst = data['Verenigingsgegevens']
        self.assertEqual(len(ver_lijst), 3)

        ver = ver_lijst[0]
        self.assertEqual(ver['Verenigingscode'], '1000')
        self.assertEqual(ver['Naam'], 'Grote club')
        self.assertEqual(ver['Aanmelddatum'], '2000-01-03')
        self.assertEqual(ver['KVKnummer'], '12345678')
        acc_lijst = ver['Accommodaties']
        self.assertEqual(len(acc_lijst), 1)
        acc = acc_lijst[0]
        self.assertEqual(acc['Postcode'], '1111AA')
        self.assertEqual(acc['Huisnummer'], 42)

    def test_api_acc(self):
        with self.assert_max_queries(20):
            rsp = self.client.get(self.url_api_acc1, headers=self.headers)
        self.assertEqual(rsp.status_code, 200)
        # print(rsp.content)

        data = json.loads(rsp.content)
        self.assertEqual(data['meta']['count'], 2)
        self.assertEqual(data['meta']['total'], 2)
        acc_lijst = data['Accommodatiegegevens']
        self.assertEqual(len(acc_lijst), 2)

        acc = acc_lijst[0]
        self.assertEqual(acc['Naam'], 'Grote club')
        self.assertEqual(acc['Postcode'], '1111AA')
        self.assertEqual(acc['Straat'], 'Pijlstraat')
        self.assertEqual(acc['Huisnummer'], 42)
        self.assertEqual(acc['Plaats'], 'Boogstad')
        self.assertEqual(acc['Land'], 'NL')
        self.assertEqual(acc['Latitude'], '4.0')
        self.assertEqual(acc['Longitude'], '55.1')

    def test_api_lms(self):
        with self.assert_max_queries(20):
            rsp = self.client.get(self.url_api_lms1, headers=self.headers)
        self.assertEqual(rsp.status_code, 200)
        # print(rsp.content)

        data = json.loads(rsp.content)
        self.assertEqual(data['meta']['count'], 3)
        self.assertEqual(data['meta']['total'], 3)
        self.assertEqual(data['meta']['limit'], 0)
        self.assertEqual(data['meta']['offset'], 0)

        lms_lijst = data['Lidmaatschapsgegevens']
        self.assertEqual(len(lms_lijst), 3)

        lms = lms_lijst[0]
        self.assertEqual(lms['Lidcode'], '100001')
        self.assertEqual(lms['Verenigingscode'], '1000')
        self.assertEqual(lms['Postcode'], '1234AB')
        self.assertEqual(lms['Land'], 'NL')
        self.assertEqual(lms['Geboortedatum'], '1972-01-01')
        self.assertEqual(lms['Geslacht'], 'x')
        self.assertEqual(lms['Aanmelddatum'], '2001-06-01')
        self.assertEqual(lms['Afmelddatum'], '')
        tak_lijst = lms['Sporttak']
        self.assertEqual(len(tak_lijst), 1)
        self.assertEqual(tak_lijst[0], 'handboogsport')

        # met peildatum en offset
        rsp = self.client.get(self.url_api_lms2 + '?peildatum=2010-01-01&offset=2&limit=1', headers=self.headers)
        data = json.loads(rsp.content)
        self.assertEqual(data['meta']['count'], 1)
        self.assertEqual(data['meta']['total'], 3)
        self.assertEqual(data['meta']['limit'], 1)
        self.assertEqual(data['meta']['offset'], 2)

    def test_bad_params(self):
        url = self.url_api_lms2 + '?'

        # peildatum
        rsp = self.client.get(url + 'peildatum=haha', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide peildatum lengte\n')

        rsp = self.client.get(url + 'peildatum=hahahahaha', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide peildatum (YMD)\n')

        rsp = self.client.get(url + 'peildatum=1900-01-01', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide peildatum eeuw\n')

        rsp = self.client.get(url + 'peildatum=2000-99-01', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide peildatum (inhoudelijk)\n')

        # limit
        rsp = self.client.get(url + 'limit=haha', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide limit (getal)\n')

        rsp = self.client.get(url + 'limit=0', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide limit (range)\n')

        rsp = self.client.get(url + 'limit=-1', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide limit (range)\n')

        rsp = self.client.get(url + 'limit=9999999', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide limit (range)\n')

        # offset
        rsp = self.client.get(url + 'offset=haha', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide offset (getal)\n')

        rsp = self.client.get(url + 'offset=-1', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide offset (range)\n')

        rsp = self.client.get(url + 'offset=999999999', headers=self.headers)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.content, b'Geen valide offset (range)\n')

# end of file
