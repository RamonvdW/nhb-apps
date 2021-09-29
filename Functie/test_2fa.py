# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import pyotp


def get_otp_code(account):
    otp = pyotp.TOTP(account.otp_code)
    return otp.now()


class TestFunctie2FA(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie, module OTP / 2FA """

    test_after = ('Account', 'Functie.test_rol')

    url_koppel_stap1 = '/functie/otp-koppelen-stap1/'
    url_koppel_stap2 = '/functie/otp-koppelen-stap2/'
    url_koppel_stap3 = '/functie/otp-koppelen-stap3/'
    url_controle = '/functie/otp-controle/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.testdata.account_admin.otp_code = ""
        self.testdata.account_admin.otp_is_actief = False
        self.testdata.account_admin.save()

        self.account_normaal.otp_code = ""
        self.account_normaal.otp_is_actief = False
        self.account_normaal.save()

    def test_2fa_koppelen_niet_ingelogd(self):
        self.e2e_logout()

        # controleer redirect naar het plein, omdat de gebruiker niet ingelogd is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap1)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap2)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap3)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': '123456'})
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_koppelen_niet_nodig(self):
        self.e2e_login(self.account_normaal)

        # controleer redirect naar het plein, omdat OTP koppeling niet nodig is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap1)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap2)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap3)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': '123456'})
        self.assert403(resp)

    def test_2fa_koppelen(self):
        # reset OTP koppeling

        # log in
        self.e2e_login(self.testdata.account_admin)

        # check mogelijkheid tot koppelen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap1)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-stap1-uitleg.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap2)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-stap2-scan-qr-code.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # check dat het OTP secret aangemaakt is
        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertNotEqual(self.testdata.account_admin.otp_code, '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap3)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # geef een illegale (te korte) otp code op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': '123'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Verkeerde code. Probeer het nog eens')

        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.testdata.account_admin.otp_is_actief)

        # geef verkeerde otp code op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Verkeerde code. Probeer het nog eens')
        self.assert_html_ok(resp)

        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.testdata.account_admin.otp_is_actief)

        # juiste otp code
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-koppelen-gelukt.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertTrue(self.testdata.account_admin.otp_is_actief)

        self.e2e_assert_other_http_commands_not_supported(self.url_koppel_stap1)
        self.e2e_assert_other_http_commands_not_supported(self.url_koppel_stap2)
        self.e2e_assert_other_http_commands_not_supported(self.url_koppel_stap3, post=False)

    def test_2fa_koppelen_al_gekoppeld(self):
        # maak OTP koppeling
        self.testdata.account_admin.otp_is_actief = True
        self.testdata.account_admin.otp_code = 'xx'
        self.testdata.account_admin.save()

        # login and pass OTP
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        # TODO: e2e manier vinden om te controleren dat account OTP nodig heeft
        #self.assertTrue(account_needs_otp(self.account_admin))
        # TODO: e2e manier vinden om te controleren dat account OTP control gehad heeft
        #self.assertTrue(user_is_otp_verified(self.client))

        # probeer OTP koppelen terwijl al gedaan
        # post
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': code})
        self.assert_is_redirect(resp, '/plein/')

        # get
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap1)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap2)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap3)
        self.assert_is_redirect(resp, '/plein/')

    def test_2fa_controle_niet_ingelogd(self):
        self.e2e_logout()
        # controleer redirect naar het plein, omdat de gebruiker niet ingelogd is
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
        self.testdata.account_admin.otp_is_actief = True
        self.testdata.account_admin.otp_code = "ABCDEFGHIJKLMNOP"
        self.testdata.account_admin.save()

        self.e2e_login(self.testdata.account_admin)

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

        # foute code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Verkeerde code. Probeer het nog eens.")

        # juiste otp code
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(25):       # iets hoger ivm follow=True
            resp = self.client.post(self.url_controle, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

        # juiste otp code + next url
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': code, 'next_url': '/records/iets/'})
        self.assertEqual(resp.status_code, 302)
        self.assert_is_redirect(resp, '/records/iets/')

        self.e2e_assert_other_http_commands_not_supported(self.url_controle, post=False)

    def test_qrcode_te_groot(self):
        # log in
        self.testdata.account_admin.username = 'volledige_lengte_gebruikt_van_50_tekens__erg_lange'
        self.testdata.account_admin.save()
        self.e2e_login(self.testdata.account_admin)

        with self.settings(OTP_ISSUER_NAME='erg_lange_otp_issuer_naam_van_50_tekens__erg_lange'):
            # check mogelijkheid tot koppelen
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_koppel_stap2)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('functie/otp-koppelen-stap2-scan-qr-code.dtl', 'plein/site_layout.dtl'))
            self.assert_html_ok(resp)

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_koppel_stap3)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('functie/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
            self.assert_html_ok(resp)

# end of file
