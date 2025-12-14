# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Account.operations import qrcode_get
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestAccountOpQRcode(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; operations module QR code """

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_qrcode_get(self):
        account = self.testdata.account_admin

        # normaal
        html = qrcode_get(account)
        self.assertTrue(len(html) > 0)

        # te lange URI
        account.username = 'volledige_lengte_gebruikt_van_50_tekens__erg_lange'
        account.save(update_fields=['username'])

        with override_settings(OTP_ISSUER_NAME='erg_lange_otp_issuer_naam_van_50_tekens__erg_lange'):
            html = qrcode_get(account)
            self.assertTrue(len(html) > 0)

# end of file
