# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .menu import menu_dynamics
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from types import SimpleNamespace
from .views import is_browser_supported
import datetime


class TestPlein(E2EHelpers, TestCase):
    """ unit tests voor de Plein applicatie """

    test_after = ('Functie',)

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()
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
        ver.nhb_nr = "1000"
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
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_100001
        lid.email = lid.account.email
        lid.save()

        self.useragent_msie_1 = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'
        self.useragent_msie_2 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko'
        self.useragent_firefox = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0'

        self.url_root = '/'
        self.url_plein = '/plein/'
        self.url_privacy = '/plein/privacy/'
        self.url_niet_ondersteund = '/plein/niet-ondersteund/'

    def test_root_redirect(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_root)
        self.assertEqual(resp.status_code, 302)     # 302 = redirect
        self.assertEqual(resp.url, '/plein/')

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
        self.assert_template_used(resp, ('plein/plein-schutter.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.e2e_logout()

    def test_plein_admin(self):
        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wissel van rol')
        urls = [url for url in self.extract_all_urls(resp) if "admin" in url or "beheer" in url]
        self.assertEqual(0, len(urls))

        # simuleer 2FA
        self.e2e_login_and_pass_otp(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp) if "beheer" in url]
        self.assertEqual(0, len(urls))  # komt pas in beeld na kiezen rol IT

        # wissel naar IT beheerder
        self.e2e_wisselnaarrol_it()
        self.e2e_check_rol('IT')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp) if "beheer" in url]
        self.assertEqual(1, len(urls))

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
        self.assertContains(resp, 'Gebruiker')

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

        # sporter
        self.e2e_wisselnaarrol_sporter()
        self.e2e_check_rol('sporter')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Sporter')

    def test_privacy(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_privacy)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/privacy.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.e2e_assert_other_http_commands_not_supported(self.url_privacy)

    def test_dynamic_menu_assert(self):
        # test the assert in menu_dynamics
        context = dict()
        request = SimpleNamespace()      # creates an empty object
        request.user = SimpleNamespace()
        request.user.is_authenticated = False
        with self.assertRaises(AssertionError):
            menu_dynamics(request, context, actief='test-bestaat-niet')

    def test_quick(self):
        # voor test.sh om met een snelle run in debug mode
        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp)      # for coverage

    def test_is_browser_supported(self):
        request = SimpleNamespace()
        request.META = dict()

        # geen header
        self.assertTrue(is_browser_supported(request))

        # internet explorer
        request.META['HTTP_USER_AGENT'] = self.useragent_msie_1
        self.assertFalse(is_browser_supported(request))
        request.META['HTTP_USER_AGENT'] = self.useragent_msie_2
        self.assertFalse(is_browser_supported(request))

        # andere
        request.META['HTTP_USER_AGENT'] = self.useragent_firefox
        self.assertTrue(is_browser_supported(request))

    def test_browser_support(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_root, HTTP_USER_AGENT=self.useragent_msie_1)
        self.assert_is_redirect(resp, self.url_niet_ondersteund)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein, HTTP_USER_AGENT=self.useragent_msie_2)
        self.assert_is_redirect(resp, self.url_niet_ondersteund)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_root, HTTP_USER_AGENT=self.useragent_firefox)
        self.assert_is_redirect(resp, self.url_plein)

    def test_niet_ondersteund(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_niet_ondersteund)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/niet-ondersteund.dtl',))
        self.assert_html_ok(resp)

        # site_layout.dtl moet niet gebruikt worden ivm alle javascript
        for templ in resp.templates:
            self.assertFalse("site_layout.dtl" in templ.name)
        # for

        self.e2e_assert_other_http_commands_not_supported(self.url_niet_ondersteund)

# end of file
