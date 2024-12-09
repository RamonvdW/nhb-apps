# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
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


class TestAccountOtpKoppelen(E2EHelpers, TestCase):

    """ tests voor de Account applicatie, OTP Koppelen view """

    test_after = ('Account.tests.test_op_qrcode', 'Account.tests.test_op_otp')

    url_koppel_stap1 = '/account/otp-koppelen-stap1/'
    url_koppel_stap2 = '/account/otp-koppelen-stap2/'
    url_koppel_stap3 = '/account/otp-koppelen-stap3/'

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

    def test_niet_nodig(self):
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

    def test_koppel(self):
        # log in
        self.e2e_login(self.testdata.account_admin)

        # check mogelijkheid tot koppelen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap1)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-koppelen-stap1-uitleg.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap2)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-koppelen-stap2-scan-qr-code.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # check dat het OTP secret aangemaakt is
        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertNotEqual(self.testdata.account_admin.otp_code, '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppel_stap3)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # geef een illegale (te korte) otp code op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': '123'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Verkeerde code. Probeer het nog eens')

        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.testdata.account_admin.otp_is_actief)

        # geef out of range otp code op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': '-10000'})      # moet 6 posities zijn
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: voer de vereiste code in')
        self.assert_html_ok(resp)

        # geef verkeerde otp code op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': '123456'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-koppelen-stap3-code-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Fout: verkeerde code. Probeer het nog eens')
        self.assert_html_ok(resp)

        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertFalse(self.testdata.account_admin.otp_is_actief)

        # juiste otp code
        code = get_otp_code(self.testdata.account_admin)
        with self.assert_max_queries(28):
            resp = self.client.post(self.url_koppel_stap3, {'otp_code': code}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/otp-koppelen-gelukt.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.testdata.account_admin = Account.objects.get(username='admin')
        self.assertTrue(self.testdata.account_admin.otp_is_actief)

        # self.e2e_assert_other_http_commands_not_supported(self.url_koppel_stap1)
        self.e2e_assert_other_http_commands_not_supported(self.url_koppel_stap2, post=False)
        self.e2e_assert_other_http_commands_not_supported(self.url_koppel_stap3, post=False)

    def test_al_gekoppeld(self):
        # maak OTP koppeling
        self.testdata.account_admin.otp_is_actief = True
        self.testdata.account_admin.otp_code = 'xx'
        self.testdata.account_admin.save()

        # login and pass OTP
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        # FUTURE: e2e manier vinden om te controleren dat account OTP nodig heeft
        # self.assertTrue(account_needs_otp(self.account_admin))
        # FUTURE: e2e manier vinden om te controleren dat account OTP control gehad heeft
        # self.assertTrue(user_is_otp_verified(self.client))

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


# end of file
