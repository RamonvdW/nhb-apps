# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Functie.rol import rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle,\
                        rol_activeer_rol, rol_activeer_functie
from Account.models import Account, account_zet_sessionvars_na_login, account_zet_sessionvars_na_otp_controle,\
                           account_vhpg_is_geaccepteerd
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from .menu import menu_dynamics
from Schutter.leeftijdsklassen import leeftijdsklassen_zet_sessionvars_na_login
from Overig.helpers import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from types import SimpleNamespace
import datetime


class TestPlein(TestCase):
    """ unit tests voor de Plein applicatie """

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('100001', 'nhb100001@test.com', 'wachtwoord')
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_admin.is_BB = True
        self.account_admin.save()
        self.account_normaal = Account.objects.get(username='normaal')
        self.account_100001 = Account.objects.get(username='100001')

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

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
        lid.save()
        self.account_100001.nhblid = lid
        self.account_100001.save()

    def test_root_redirect(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)     # 302 = redirect
        self.assertEqual(resp.url, '/plein/')

    def test_plein_anon(self):
        self.client.logout()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_plein_normaal(self):
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_plein_nhblid(self):
        self.client.login(username=self.account_100001.username, password='wachtwoord')
        rol_zet_sessionvars_na_login(self.account_100001, self.client).save()
        leeftijdsklassen_zet_sessionvars_na_login(self.account_100001, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        self.assertNotContains(resp, 'Wissel van rol')
        assert_template_used(self, resp, ('plein/plein-schutter.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_plein_admin(self):
        self.account_admin.functies.add(self.functie_bko)
        self.client.login(username=self.account_admin.username, password='wachtwoord')

        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/beheer/')
        self.assertNotContains(resp, '/admin/')
        self.assertContains(resp, 'Wissel van rol')

        # simuleer 2FA
        account_vhpg_is_geaccepteerd(self.account_admin)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/beheer/')    # komt pas in beeld na kiezen rol IT
        self.assertContains(resp, 'Wissel van rol')
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        # wissel naar IT beheerder
        rol_activeer_rol(self.client, 'beheerder').save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '/beheer/')
        self.assertContains(resp, 'Wissel van rol')
        assert_template_used(self, resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))

        # wissel naar elk van de functies

        # bb
        rol_activeer_rol(self.client, "BB").save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Manager competitiezaken')

        # bko
        rol_activeer_functie(self.client, self.functie_bko.pk).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'BKO')

        # rko
        rol_activeer_functie(self.client, self.functie_rko.pk).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'RKO')

        # rcl
        rol_activeer_functie(self.client, self.functie_rcl.pk).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'RCL')

        # cwz
        rol_activeer_functie(self.client, self.functie_cwz.pk).save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'CWZ ')

        # geen
        rol_activeer_rol(self.client, "geen").save()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Gebruiker')

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
        request = SimpleNamespace()      # creates an empty object
        request.user = SimpleNamespace()
        request.user.is_authenticated = False
        with self.assertRaises(AssertionError):
            menu_dynamics(request, context, actief='test-bestaat-niet')

# end of file
