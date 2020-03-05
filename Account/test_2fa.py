# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from .rol import rol_zet_sessionvars_na_login
from .models import Account, AccountEmail,\
                    account_zet_sessionvars_na_login,\
                    account_prep_for_otp, account_needs_otp
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
import datetime
import pyotp


def get_otp_code(account):
    otp = pyotp.TOTP(account.otp_code)
    return otp.now()


class TestAccount2FA(TestCase):
    """ unit tests voor de Account applicatie, module OTP / 2FA """

    def setUp(self):
        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_user('metmail', 'metmail@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')
        self.account_metmail = Account.objects.get(username='metmail')

        email, created_new = AccountEmail.objects.get_or_create(account=self.account_metmail)
        email.email_is_bevestigd = True
        email.bevestigde_email = 'metmail@test.com'
        email.save()
        self.email_metmail = email

        self.group_bko, _ = Group.objects.get_or_create(name="BKO test")
        self.group_rko, _ = Group.objects.get_or_create(name="RKO test")
        self.group_rcl, _ = Group.objects.get_or_create(name="RCL test")
        self.group_cwz, _ = Group.objects.get_or_create(name="CWZ test")
        self.group_tst, _ = Group.objects.get_or_create(name="Test test")

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

    def test_otp_koppelen_niet_ingelogd(self):
        self.client.logout()
        # controleer redirect naar het plein, omdat de gebruiker niet ingelogged is
        resp = self.client.get('/account/otp-koppelen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_otp_koppelen_niet_nodig(self):
        self.client.login(username='normaal', password='wachtwoord')
        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        resp = self.client.get('/account/otp-koppelen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_otp_koppelen_al_gekoppeld(self):
        self.account_admin.otp_is_actief = True
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        # controleer redirect naar het plein, omdat OTP koppeling er al is
        resp = self.client.get('/account/otp-koppelen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_otp_koppelen(self):
        # reset OTP koppeling
        self.account_admin.otp_is_actief = False
        self.account_admin.otp_code = 'xx'
        self.account_admin.save()
        # log in
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        # check mogelijkheid tot koppelen
        resp = self.client.get('/account/otp-koppelen/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        # check dat het OTP secret aangemaakt is
        self.account_admin = Account.objects.get(username='admin')
        self.assertNotEqual(self.account_admin.otp_code, 'xx')
        # geef foute otp code op
        resp = self.client.post('/account/otp-koppelen/', {'otp_code': '123456'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        self.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.account_admin.otp_is_actief)
        # juiste otp code
        code = get_otp_code(self.account_admin)
        resp = self.client.post('/account/otp-koppelen/', {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-koppelen-gelukt.dtl', 'plein/site_layout.dtl'))
        self.account_admin = Account.objects.get(username='admin')
        self.assertTrue(self.account_admin.otp_is_actief)

    def test_otp_controle_niet_ingelogd(self):
        self.client.logout()
        # controleer redirect naar het plein, omdat de gebruiker niet ingelogged is
        resp = self.client.get('/account/otp-controle/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-controle/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_otp_controle_niet_nodig(self):
        self.client.login(username='normaal', password='wachtwoord')
        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        resp = self.client.get('/account/otp-controle/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post('/account/otp-controle/', {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_otp_controle(self):
        self.account_admin.otp_is_actief = True
        self.account_admin.otp_code = "ABCDEFGHIJKLMNOP"
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/otp-controle/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        # geen code
        resp = self.client.post('/account/otp-controle/', {'jaja': 'nee'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")
        # lege code
        resp = self.client.post('/account/otp-controle/', {'otp_code': ''}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")
        # illegale code
        resp = self.client.post('/account/otp-controle/', {'otp_code': 'ABCDEF'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Voer de vereiste code in")
        # fout code
        resp = self.client.post('/account/otp-controle/', {'otp_code': '123456'}, follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Verkeerde code. Probeer het nog eens.")
        # juiste otp code resulteert in redirect naar het plein
        code = get_otp_code(self.account_admin)
        resp = self.client.post('/account/otp-controle/', {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

    def test_account_needs_otp(self):
        account = self.account_normaal

        account.is_BB = False
        account.is_staff = False
        account.groups.clear()

        self.assertFalse(account_needs_otp(account))

        account.is_BB = True
        self.assertTrue(account_needs_otp(account))
        account.is_BB = False
        self.assertFalse(account_needs_otp(account))

        account.is_staff = True
        self.assertTrue(account_needs_otp(account))
        account.is_staff = False
        self.assertFalse(account_needs_otp(account))

        account.groups.add(self.group_tst)
        self.assertFalse(account_needs_otp(account))
        account.groups.clear()

        account.groups.add(self.group_bko)
        self.assertTrue(account_needs_otp(account))
        account.groups.clear()
        self.assertFalse(account_needs_otp(account))

        account.groups.add(self.group_rko)
        self.assertTrue(account_needs_otp(account))
        account.groups.clear()
        self.assertFalse(account_needs_otp(account))

        account.groups.add(self.group_rcl)
        self.assertTrue(account_needs_otp(account))
        account.groups.clear()
        self.assertFalse(account_needs_otp(account))

        account.groups.add(self.group_cwz)
        self.assertTrue(account_needs_otp(account))
        account.groups.clear()
        self.assertFalse(account_needs_otp(account))

    def test_account_prep_for_otp(self):
        account = self.account_normaal

        account.otp_code = ""
        account_prep_for_otp(account)
        account = Account.objects.get(username=account.username)
        self.assertEqual(len(account.otp_code), 16)

        account.otp_code = "niet 16 lang"
        account_prep_for_otp(account)
        account = Account.objects.get(username=account.username)
        self.assertEqual(len(account.otp_code), 16)

        # branch coverage: already good
        account_prep_for_otp(account)
        account = Account.objects.get(username=account.username)
        self.assertEqual(len(account.otp_code), 16)

# end of file
