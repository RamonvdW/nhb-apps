# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from Account.models import Account
from Account.operations.otp import (otp_prepare_koppelen, otp_controleer_code, otp_koppel_met_code,
                                    otp_is_controle_gelukt, otp_loskoppelen, otp_stuur_email_losgekoppeld)
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from types import SimpleNamespace
import pyotp


class TestAccountOTP(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; module OTP """

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_otp = self.e2e_create_account('otp', 'otp@test.com', 'Otp')

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        account = self.testdata.account_admin
        account.otp_code = ""
        account.otp_is_actief = False
        account.save(update_fields=['otp_is_actief', 'otp_code'])

        account = self.account_normaal
        account.otp_code = ""
        account.otp_is_actief = False
        account.save(update_fields=['otp_is_actief', 'otp_code'])

    @staticmethod
    def _get_otp_code(account):
        otp = pyotp.TOTP(account.otp_code)
        return otp.now()

    def test_controleer_code(self):
        account = SimpleNamespace()
        account.otp_code = ""
        account.username = 'otp'
        account.is_staff = False
        account.is_BB = True

        request = SimpleNamespace()
        request.user = account
        request.session = self.client.session

        # niet ingelogd
        account.is_authenticated = False
        account.otp_is_actief = False
        res = otp_controleer_code(request, account, 0)
        self.assertEqual(res, False)

        # OTP niet actief
        account.is_authenticated = True
        account.otp_is_actief = False
        res = otp_controleer_code(request, account, 0)
        self.assertEqual(res, False)

        # invalid code
        account.is_authenticated = True
        account.otp_is_actief = True
        res = otp_controleer_code(request, account, 0)
        self.assertEqual(res, False)

        # correcte code kan niet getest worden
        # te veel code met dependency op echt Account
        # code = self._get_otp_code(account)
        # res = account_otp_controleer(request, account, code)
        # self.assertFalse(res)

    def test_koppelen(self):
        account = self.account_otp
        account.otp_code = ""
        account.otp_is_actief = False
        account.save(update_fields=['otp_code', 'otp_is_actief'])

        request = SimpleNamespace()
        request.user = account
        request.session = self.client.session

        # prepare
        otp_prepare_koppelen(account)
        account = Account.objects.get(pk=account.pk)
        self.assertEqual(len(account.otp_code), 32)
        self.assertFalse(account.otp_is_actief)

        res = otp_is_controle_gelukt(request)
        self.assertFalse(res)

        # prepare: tweede aanroep doet niets
        code = account.otp_code
        otp_prepare_koppelen(account)
        account = Account.objects.get(pk=account.pk)
        self.assertEqual(code, account.otp_code)

        res = otp_is_controle_gelukt(request)
        self.assertFalse(res)

        # koppel met verkeerde code (is_authenticated == True)
        code = 0
        res = otp_koppel_met_code(request, account, code)
        self.assertEqual(res, False)

        res = otp_is_controle_gelukt(request)
        self.assertFalse(res)

        # koppel met juiste code (is_authenticated == True)
        code = self._get_otp_code(account)
        res = otp_koppel_met_code(request, account, code)
        self.assertEqual(res, True)

        res = otp_is_controle_gelukt(request)
        self.assertTrue(res)

        # niet ingelogd
        account = SimpleNamespace()
        account.is_authenticated = False

        request = SimpleNamespace()
        request.user = account
        request.session = self.client.session

        res = otp_koppel_met_code(request, account, 0)
        self.assertEqual(res, False)

    def test_loskoppelen(self):
        # niet ingelogd
        request = SimpleNamespace()
        request.user = AnonymousUser()
        request.session = self.client.session
        self.assertFalse(otp_loskoppelen(request, self.account_normaal))

        # wel ingelogd, geen OTP
        request = SimpleNamespace()
        request.user = self.testdata.account_admin
        request.session = self.client.session
        self.assertFalse(otp_loskoppelen(request, self.account_normaal))

        # normaal
        self.assertTrue(otp_loskoppelen(request, self.account_otp))
        otp_stuur_email_losgekoppeld(self.account_otp)


# end of file
