# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestPlein(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie """

    test_after = ('Functie',)

    url_root = '/'
    url_plein = '/plein/'
    url_privacy = '/plein/privacy/'
    url_niet_ondersteund = '/plein/niet-ondersteund/'
    url_speciale_pagina = '/plein/test-speciale-pagina/%s/'     # code

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_100001 = self.e2e_create_account('100001', 'nhb100001@test.com', 'Ramon')

        self.functie_bko = maak_functie('BKO Test', 'BKO')

        self.functie_rko = maak_functie('RKO Test', 'RKO')
        self.functie_rko.nhb_rayon = NhbRayon.objects.get(rayon_nr=3)
        self.functie_rko.save()

        self.functie_rcl = maak_functie('RCL Test', 'RCL')
        self.functie_rcl.nhb_regio = NhbRegio.objects.get(regio_nr=111)
        self.functie_rcl.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.functie_sec = maak_functie('Secretaris vereniging 1000', 'SEC')
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie('Hoofdwedstrijdleider 1000', 'HWL')
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie('Wedstrijdleider 1000', 'WL')
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_100001
        sporter.email = sporter.account.email
        sporter.save()

        # maak een lid aan voor de admin
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "M"
        sporter.voornaam = "Ad"
        sporter.achternaam = "Min"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.testdata.account_admin
        sporter.email = sporter.account.email
        sporter.save()

    def test_plein_anon(self):
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_plein_normaal(self):
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.e2e_logout()

    def test_plein_nhblid(self):
        self.e2e_login(self.account_100001)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.e2e_logout()

    def test_plein_admin(self):
        # voordat de 2FA control gedaan is, geen admin scherm link in het dropdown menu
        self.e2e_login(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wissel van rol')
        urls = [url for url in self.extract_all_urls(resp) if "admin" in url or "beheer" in url]
        self.assertEqual(0, len(urls))

        # simuleer 2FA, waarna het admin scherm in het dropdown menu komt
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp) if "beheer" in url]
        self.assertEqual(1, len(urls))      # is globaal beschikbaar bij is_staff

        # wissel naar elk van de functies

        # bb
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Manager competitiezaken')

        # bko
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'BKO')

        # rko
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.e2e_check_rol('RKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'RKO')

        # rcl
        self.e2e_wissel_naar_functie(self.functie_rcl)
        self.e2e_check_rol('RCL')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'RCL')

        # sec
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Hoofdwedstrijdleider 1000')

        # wl
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wedstrijdleider 1000')

        # geen
        self.e2e_wisselnaarrol_gebruiker()
        self.e2e_check_rol('geen')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_sec(self):
        # login als secretaris
        account_sec = self.account_100001
        self.functie_sec.accounts.add(account_sec)
        self.e2e_account_accepteert_vhpg(account_sec)
        self.e2e_login_and_pass_otp(account_sec)

        # sec
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Secretaris vereniging 1000')
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))

        # sporter
        self.e2e_wisselnaarrol_sporter()
        self.e2e_check_rol('sporter')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))

# end of file
