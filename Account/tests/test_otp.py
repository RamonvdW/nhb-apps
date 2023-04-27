# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from Account.otp import otp_prepare_koppelen, otp_controleer_code, otp_koppel_met_code, otp_is_controle_gelukt
from TestHelpers.e2ehelpers import E2EHelpers
from types import SimpleNamespace
import pyotp


class TestAccountOTP(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; module OTP """

    @staticmethod
    def _get_otp_code(account):
        otp = pyotp.TOTP(account.otp_code)
        return otp.now()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_otp = self.e2e_create_account('otp', 'otp@test.com', 'Otp')

    def test_controleer(self):
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
        account.save()

        # prepare
        otp_prepare_koppelen(account)
        account = Account.objects.get(pk=account.pk)
        self.assertEqual(len(account.otp_code), 32)
        self.assertFalse(account.otp_is_actief)

        # prepare: tweede aanroep doet niets
        code = account.otp_code
        otp_prepare_koppelen(account)
        account = Account.objects.get(pk=account.pk)
        self.assertEqual(code, account.otp_code)

        request = SimpleNamespace()
        request.user = account
        request.session = self.client.session

        # koppel met verkeerde code (is_authenticated == True)
        code = 0
        res = otp_koppel_met_code(request, account, code)
        self.assertEqual(res, False)

        # koppel met juiste code (is_authenticated == True)
        code = self._get_otp_code(account)
        res = otp_koppel_met_code(request, account, code)
        self.assertEqual(res, True)

        # niet ingelogd
        account = SimpleNamespace()
        account.is_authenticated = False

        request = SimpleNamespace()
        request.user = account
        request.session = self.client.session

        res = otp_koppel_met_code(request, account, 0)
        self.assertEqual(res, False)

    def test_rechten(self):
        request = self.client
        res = otp_is_controle_gelukt(request)
        self.assertEqual(res, False)

# end of file
