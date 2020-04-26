# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .menu import menu_dynamics
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from types import SimpleNamespace
import datetime


class TestPlein(E2EHelpers, TestCase):
    """ unit tests voor de Plein applicatie """

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

        self.functie_cwz = maak_functie('CWZ vereniging 1000', 'CWZ')
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_100001
        lid.save()

    def test_root_redirect(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)     # 302 = redirect
        self.assertEqual(resp.url, '/plein/')

    def test_plein_anon(self):
        self.e2e_logout()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_plein_normaal(self):
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.e2e_logout()

    def test_plein_nhblid(self):
        self.e2e_login(self.account_100001)
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-schutter.dtl', 'plein/site_layout.dtl'))
        self.e2e_logout()

    def test_plein_admin(self):
        self.e2e_login(self.account_admin)
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/beheer/')
        self.assertNotContains(resp, '/admin/')
        self.assertContains(resp, 'Wissel van rol')

        # simuleer 2FA
        self.e2e_login_and_pass_otp(self.account_admin)
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/beheer/')    # komt pas in beeld na kiezen rol IT
        self.assertContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        # wissel naar IT beheerder
        self.e2e_wisselnaarrol_beheerder()
        self.e2e_check_rol('beheerder')

        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '/beheer/')
        self.assertContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))

        # wissel naar elk van de functies

        # bb
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Manager competitiezaken')

        # bko
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'BKO')

        # rko
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.e2e_check_rol('RKO')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'RKO')

        # rcl
        self.e2e_wissel_naar_functie(self.functie_rcl)
        self.e2e_check_rol('RCL')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'RCL')

        # cwz
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'CWZ ')

        # geen
        self.e2e_wisselnaarrol_gebruiker()
        self.e2e_check_rol('geen')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Gebruiker')

    def test_privacy(self):
        resp = self.client.get('/plein/privacy/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/privacy.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported('/plein/privacy/')

    def test_dynamic_menu_assert(self):
        # test the assert in menu_dynamics
        context = dict()
        request = SimpleNamespace()      # creates an empty object
        request.user = SimpleNamespace()
        request.user.is_authenticated = False
        with self.assertRaises(AssertionError):
            menu_dynamics(request, context, actief='test-bestaat-niet')

# end of file
