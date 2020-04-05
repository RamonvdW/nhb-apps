# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from Account.models import Account
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
import datetime
import pyotp


def get_otp_code(account):
    otp = pyotp.TOTP(account.otp_code)
    return otp.now()


class TestAccount2FA(E2EHelpers, TestCase):
    """ unit tests voor de Account applicatie, module OTP / 2FA """

    test_after = ('Account', 'Functie.test_rol')

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.account_admin.otp_code = ""
        self.account_admin.otp_is_actief = False
        self.account_admin.save()

        self.account_normaal.otp_code = ""
        self.account_normaal.otp_is_actief = False
        self.account_normaal.save()

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

        self.url_koppel = '/functie/otp-koppelen/'
        self.url_controle = '/functie/otp-controle/'

    def test_2fa_koppelen_niet_ingelogd(self):
        self.e2e_logout()

        # controleer redirect naar het plein, omdat de gebruiker niet ingelogd is
        resp = self.client.get(self.url_koppel)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.post(self.url_koppel, {'otp_code': '123456'})
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_koppelen_niet_nodig(self):
        self.e2e_login(self.account_normaal)

        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        resp = self.client.get(self.url_koppel)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.post(self.url_koppel, {'otp_code': '123456'})
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_koppelen(self):
        # reset OTP koppeling

        # log in
        self.e2e_login(self.account_admin)

        # check mogelijkheid tot koppelen
        resp = self.client.get(self.url_koppel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen.dtl', 'plein/site_layout.dtl'))

        # check dat het OTP secret aangemaakt is
        self.account_admin = Account.objects.get(username='admin')
        self.assertNotEqual(self.account_admin.otp_code, '')

        # geef een illegale (te korte) otp code op
        resp = self.client.post(self.url_koppel, {'otp_code': '123'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Verkeerde code. Probeer het nog eens')

        self.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.account_admin.otp_is_actief)

        # geef verkeerde otp code op
        resp = self.client.post(self.url_koppel, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Verkeerde code. Probeer het nog eens')

        self.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.account_admin.otp_is_actief)

        # juiste otp code
        code = get_otp_code(self.account_admin)
        resp = self.client.post(self.url_koppel, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-gelukt.dtl', 'plein/site_layout.dtl'))

        self.account_admin = Account.objects.get(username='admin')
        self.assertTrue(self.account_admin.otp_is_actief)

    def test_2fa_koppelen_al_gekoppeld(self):
        # maak OTP koppeling
        self.account_admin.otp_is_actief = True
        self.account_admin.otp_code = 'xx'
        self.account_admin.save()

        # login and pass OTP
        self.e2e_login_and_pass_otp(self.account_admin)
        # TODO: e2e manier vinden om te controleren dat account OTP nodig heeft
        #self.assertTrue(account_needs_otp(self.account_admin))
        # TODO: e2e manier vinden om te controleren dat account OTP control gehad heeft
        #self.assertTrue(user_is_otp_verified(self.client))

        # probeer OTP koppelen terwijl al gedaan
        # post
        code = get_otp_code(self.account_admin)
        resp = self.client.post(self.url_koppel, {'otp_code': code})
        self.assert_is_redirect(resp, '/plein/')
        # get
        resp = self.client.get(self.url_koppel)
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_controle_niet_ingelogd(self):
        self.e2e_logout()
        # controleer redirect naar het plein, omdat de gebruiker niet ingelogged is
        resp = self.client.get(self.url_controle, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post(self.url_controle, {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_2fa_controle_niet_nodig(self):
        self.e2e_login(self.account_normaal)
        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        resp = self.client.get(self.url_controle, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post(self.url_controle, {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_2fa_controle(self):
        self.account_admin.otp_is_actief = True
        self.account_admin.otp_code = "ABCDEFGHIJKLMNOP"
        self.account_admin.save()

        self.e2e_login(self.account_admin)

        # ophalen van de OTP controle pagina
        resp = self.client.get(self.url_controle)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))

        # geen code
        resp = self.client.post(self.url_controle, {'jaja': 'nee'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")

        # lege code
        resp = self.client.post(self.url_controle, {'otp_code': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")

        # illegale code
        resp = self.client.post(self.url_controle, {'otp_code': 'ABCDEF'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Voer de vereiste code in")

        # fout code
        resp = self.client.post(self.url_controle, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Verkeerde code. Probeer het nog eens.")

        # juiste otp code
        code = get_otp_code(self.account_admin)
        resp = self.client.post(self.url_controle, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

# TODO: gebruik assert_other_http_commands_not_supported

# end of file
