# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from .rol import rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle, rol_activeer_rol
from .models import Account, account_zet_sessionvars_na_login,\
                    account_zet_sessionvars_na_otp_controle,\
                    HanterenPersoonsgegevens, account_needs_vhpg, account_vhpg_is_geaccepteerd
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
import datetime


class TestAccountVHPG(TestCase):
    """ unit tests voor de Account applicatie; module VHPG """

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

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
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid1 = lid

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

    def test_vhpg_anon(self):
        self.client.logout()
        resp = self.client.get('/account/vhpg-acceptatie/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        # doe een post zonder ingelogd te zijn
        resp = self.client.post('/account/vhpg-acceptatie/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_vhpg_niet_nodig(self):
        self.client.login(username='normaal', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()
        resp = self.client.get('/account/vhpg-acceptatie/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_vhpg(self):
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/vhpg-acceptatie/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/vhpg-acceptatie.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'verplicht')

        self.assertEqual(len(HanterenPersoonsgegevens.objects.all()), 0)
        needs_vhpg, _ = account_needs_vhpg(self.account_admin)
        self.assertTrue(needs_vhpg)

        # voer de post uit zonder checkbox (dit gebeurt ook als de checkbox niet gezet wordt)
        resp = self.client.post('/account/vhpg-acceptatie/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/vhpg-acceptatie.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'verplicht')

        self.assertEqual(len(HanterenPersoonsgegevens.objects.all()), 0)

        # voer de post uit met checkbox wel gezet (waarde maakt niet uit)
        resp = self.client.post('/account/vhpg-acceptatie/', {'accepteert': 'whatever'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(len(HanterenPersoonsgegevens.objects.all()), 1)
        needs_vhpg, _ = account_needs_vhpg(self.account_admin)
        self.assertFalse(needs_vhpg)

        obj = HanterenPersoonsgegevens.objects.all()[0]
        self.assertTrue(str(obj) != "")

    def test_vhpg_overzicht(self):
        account_vhpg_is_geaccepteerd(self.account_admin)

        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()

        resp = self.client.get('/account/vhpg-overzicht/')
        self.assertEqual(resp.status_code, 403)     # 403 = Forbidden

        rol_activeer_rol(self.client, "BB").save()
        resp = self.client.get('/account/vhpg-overzicht/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/vhpg-overzicht.dtl', 'plein/site_layout.dtl'))

    def test_vhpg_afspraken_anon(self):
        self.client.logout()
        resp = self.client.get('/account/vhpg-afspraken/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))

    def test_vhpg_afspraken(self):
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/vhpg-afspraken/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/vhpg-afspraken.dtl', 'plein/site_layout.dtl'))

# end of file
