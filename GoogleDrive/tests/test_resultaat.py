# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers


class TestGoogleDriveResultaat(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, module view_resultaat """

    url_resultaat_gelukt = '/google/resultaat-gelukt/'
    url_resultaat_mislukt = '/google/resultaat-mislukt/'

    def setUp(self):
        self.account_admin = self.e2e_create_account_admin()

    def test_gelukt(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_resultaat_gelukt)
        self.assert_is_redirect_login(resp)

        # login en wissel naar rol BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_resultaat_gelukt)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('googledrive/resultaat-gelukt.dtl', 'design/site_layout.dtl'))

    def test_mislukt(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_resultaat_mislukt)
        self.assert_is_redirect_login(resp)

        # login en wissel naar rol BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_resultaat_mislukt)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('googledrive/resultaat-mislukt.dtl', 'design/site_layout.dtl'))


# end of file
