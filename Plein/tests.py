# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from .menu import menu_dynamics
from Account.rol import rol_zet_sessionvars_na_login
from Account.leeftijdsklassen import leeftijdsklassen_zet_sessionvars_na_login
from Account.models import Account, account_zet_sessionvars_na_login, account_zet_sessionvars_na_otp_controle
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
import datetime


def assert_html_ok(testcase, response):
    """ Doe een aantal basic checks op een html response """
    html = str(response.content)
    testcase.assertContains(response, "<html")
    testcase.assertIn("lang=", html)
    testcase.assertIn("</html>", html)
    testcase.assertIn("<head>", html)
    testcase.assertIn("</head>", html)
    testcase.assertIn("<body ", html)
    testcase.assertIn("</body>", html)
    testcase.assertIn("<!DOCTYPE html>", html)


def assert_template_used(testcase, response, template_names):
    """ Controleer dat de gevraagde templates gebruikt zijn """
    lst = list(template_names)
    for templ in response.templates:
        # print("template name: %s" % templ.name)
        if templ.name in lst:
            lst.remove(templ.name)
    # for
    if len(lst):    # pragma: no coverage
        msg = "Following templates should have been used: %s\n(actually used: %s)" % (repr(lst), repr([t.name for t in response.templates]))
        testcase.assertTrue(False, msg=msg)


def assert_other_http_commands_not_supported(testcase, url, post=True, delete=True, put=True, patch=True):
    """ Test een aantal 'common' http methoden
        en controleer dat deze niet ondersteund zijn (status code 405 = not allowed)
        POST, DELETE, PATCH
    """
    if post:
        resp = testcase.client.post(url)
        testcase.assertEqual(resp.status_code, 405)  # 405=not allowd

    if delete:
        resp = testcase.client.delete(url)
        testcase.assertEqual(resp.status_code, 405)

    if put:
        resp = testcase.client.put(url)
        testcase.assertEqual(resp.status_code, 405)

    if patch:
        resp = testcase.client.patch(url)
        testcase.assertEqual(resp.status_code, 405)


class PleinTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('100001', 'nhb100001@test.com', 'wachtwoord')
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')
        self.account_100001 = Account.objects.get(username='100001')

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.postcode = "1234PC"
        lid.huisnummer = "42bis"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.account_100001.nhblid = lid
        self.account_100001.save()

    def test_root_redirect(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)     # 302 = redirect
        self.assertEqual(resp.url, '/plein/')

    def test_plein_annon(self):
        self.client.logout()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_plein_normaal(self):
        self.client.login(username='normaal', password='wachtwoord')
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_plein_nhblid(self):
        self.client.login(username='100001', password='wachtwoord')
        rol_zet_sessionvars_na_login(self.account_100001, self.client).save()
        leeftijdsklassen_zet_sessionvars_na_login(self.account_100001, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        assert_template_used(self, resp, ('plein/plein-schutter.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_plein_admin(self):
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/beheer/')
        self.assertNotContains(resp, '/admin/')
        self.assertContains(resp, 'Wissel van rol')
        # simuleert 2FA
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '/beheer/')
        self.assertContains(resp, 'Wissel van rol')
        assert_template_used(self, resp, ('plein/plein-bko.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_privacy(self):
        resp = self.client.get('/plein/privacy/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/privacy.dtl', 'plein/site_layout.dtl'))
        assert_other_http_commands_not_supported(self, '/plein/privacy/')

    def test_dynamic_menu_asssert(self):
        # test the assert in menu_dynamics
        context = dict()
        request = lambda: None      # create an empty object
        request.user = lambda: None
        request.user.is_authenticated = False
        with self.assertRaises(AssertionError):
            menu_dynamics(request, context, actief='test-bestaat-niet')

    def test_leeftijdsklassen_anon(self):
        self.client.logout()
        resp = self.client.get('/plein/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

    def test_leeftijdsklassen_nhblid(self):
        self.client.login(username='100001', password='wachtwoord')
        rol_zet_sessionvars_na_login(self.account_100001, self.client).save()
        leeftijdsklassen_zet_sessionvars_na_login(self.account_100001, self.client).save()
        resp = self.client.get('/plein/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

# end of file
