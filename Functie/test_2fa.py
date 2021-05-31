# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from Overig.e2ehelpers import E2EHelpers
import pyotp


def get_otp_code(account):
    otp = pyotp.TOTP(account.otp_code)
    return otp.now()


class TestFunctie2FA(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie, module OTP / 2FA """

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

        self.url_koppel = '/functie/otp-koppelen/'
        self.url_controle = '/functie/otp-controle/'

    def test_2fa_koppelen_niet_ingelogd(self):
        self.e2e_logout()

        # controleer redirect naar het plein, omdat de gebruiker niet ingelogd is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel, {'otp_code': '123456'})
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_koppelen_niet_nodig(self):
        self.e2e_login(self.account_normaal)

        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel, {'otp_code': '123456'})
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_koppelen(self):
        # reset OTP koppeling

        # log in
        self.e2e_login(self.account_admin)

        # check mogelijkheid tot koppelen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # check dat het OTP secret aangemaakt is
        self.account_admin = Account.objects.get(username='admin')
        self.assertNotEqual(self.account_admin.otp_code, '')

        # geef een illegale (te korte) otp code op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel, {'otp_code': '123'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Verkeerde code. Probeer het nog eens')

        self.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.account_admin.otp_is_actief)

        # geef verkeerde otp code op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Verkeerde code. Probeer het nog eens')
        self.assert_html_ok(resp)

        self.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.account_admin.otp_is_actief)

        # juiste otp code
        code = get_otp_code(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-gelukt.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.account_admin = Account.objects.get(username='admin')
        self.assertTrue(self.account_admin.otp_is_actief)

        self.e2e_assert_other_http_commands_not_supported(self.url_koppel, post=False)

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
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel, {'otp_code': code})
        self.assert_is_redirect(resp, '/plein/')
        # get
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel)
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_controle_niet_ingelogd(self):
        self.e2e_logout()
        # controleer redirect naar het plein, omdat de gebruiker niet ingelogged is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_controle, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_2fa_controle_niet_nodig(self):
        self.e2e_login(self.account_normaal)
        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_controle, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': '123456'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_2fa_controle(self):
        self.account_admin.otp_is_actief = True
        self.account_admin.otp_code = "ABCDEFGHIJKLMNOP"
        self.account_admin.save()

        self.e2e_login(self.account_admin)

        # ophalen van de OTP controle pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_controle)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))

        # geen code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'jaja': 'nee'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")

        # lege code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")

        # illegale code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': 'ABCDEF'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Voer de vereiste code in")

        # fout code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Verkeerde code. Probeer het nog eens.")

        # juiste otp code
        code = get_otp_code(self.account_admin)
        with self.assert_max_queries(25):       # iets hoger ivm follow=True
            resp = self.client.post(self.url_controle, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_controle, post=False)

    def test_qrcode_te_groot(self):
        # log in
        self.account_admin.username = 'volledige_lengte_gebruikt_van_50_tekens__erg_lange'
        self.account_admin.save()
        self.e2e_login(self.account_admin)

        with self.settings(OTP_ISSUER_NAME='erg_lange_otp_issuer_naam_van_50_tekens__erg_lange'):
            # check mogelijkheid tot koppelen
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_koppel)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('functie/otp-koppelen.dtl', 'plein/site_layout.dtl'))
            self.assert_html_ok(resp)

# end of file
