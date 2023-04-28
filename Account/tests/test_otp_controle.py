# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import pyotp


def get_otp_code(account):
    otp = pyotp.TOTP(account.otp_code)
    return otp.now()


class TestAccountOtpControle(E2EHelpers, TestCase):

    """ tests voor de Account applicatie, OTP Control view """

    test_after = ('Account.tests.test_op_otp',)

    url_controle = '/account/otp-controle/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()        # admin & bb

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        account = self.testdata.account_admin
        account.otp_code = ""
        account.otp_is_actief = False
        account.save(update_fields=['otp_is_actief', 'otp_code'])

        account = self.account_normaal
        account.otp_code = ""
        account.otp_is_actief = False
        account.save(update_fields=['otp_is_actief', 'otp_code'])

    def test_niet_ingelogd(self):
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

    def test_niet_nodig(self):
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

    def test_controle(self):
        self.testdata.account_admin.otp_is_actief = True
        self.testdata.account_admin.otp_code = "ABCDEFGHIJKLMNOP"
        self.testdata.account_admin.save()

        self.e2e_login(self.testdata.account_admin)

        # ophalen van de OTP controle pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_controle)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # geen code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'jaja': 'nee'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")

        # lege code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "De gegevens worden niet geaccepteerd")

        # illegale code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': 'ABCDEF'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Voer de vereiste code in")

        # foute code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Verkeerde code. Probeer het nog eens.")

        # juiste otp code
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(44):       # iets hoger ivm follow=True
            resp = self.client.post(self.url_controle, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

        # juiste otp code + next url
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_controle, {'otp_code': code, 'next_url': '/records/niet-bekend/'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-controle.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De gegevens worden niet geaccepteerd')

        # juiste otp code + next url zonder final slash
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(21):
            resp = self.client.post(self.url_controle, {'otp_code': code, 'next_url': '/records'})
        self.assertEqual(resp.status_code, 302)
        self.assert_is_redirect(resp, '/records/')

        self.e2e_assert_other_http_commands_not_supported(self.url_controle, post=False)

# end of file
