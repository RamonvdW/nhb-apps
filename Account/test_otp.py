# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import Account
from .otp import account_otp_is_gekoppeld, account_otp_prepare_koppelen, account_otp_controleer, account_otp_koppel
from .rechten import account_rechten_is_otp_verified
from Overig.e2ehelpers import E2EHelpers
from types import SimpleNamespace
import pyotp


class TestAccountOTP(E2EHelpers, TestCase):
    """ unit tests voor de Account applicatie; module OTP """

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

        account.otp_is_actief = False
        res = account_otp_is_gekoppeld(account)
        self.assertEqual(res, False)

        # niet ingelogd
        account.is_authenticated = False
        account.otp_is_actief = False
        res = account_otp_controleer(request, account, 0)
        self.assertEqual(res, False)

        # OTP niet actief
        account.is_authenticated = True
        account.otp_is_actief = False
        res = account_otp_controleer(request, account, 0)
        self.assertEqual(res, False)

        # invalid code
        account.is_authenticated = True
        account.otp_is_actief = True
        res = account_otp_controleer(request, account, 0)
        self.assertEqual(res, False)

        # correcte code kan niet getest worden
        # te veel code met dependency op echt Account
        #code = self._get_otp_code(account)
        #res = account_otp_controleer(request, account, code)
        #self.assertFalse(res)

    def test_koppelen(self):
        account = self.account_otp

        account.otp_code = ""
        account.otp_is_actief = False
        account.save()

        # prepare
        account_otp_prepare_koppelen(account)
        account = Account.objects.get(pk=account.pk)
        self.assertEqual(len(account.otp_code), 32)
        self.assertFalse(account_otp_is_gekoppeld(account))

        # prepare: tweede aanroep doet niets
        code = account.otp_code
        account_otp_prepare_koppelen(account)
        account = Account.objects.get(pk=account.pk)
        self.assertEqual(code, account.otp_code)

        request = SimpleNamespace()
        request.user = account
        request.session = self.client.session

        # koppel met verkeerde code (is_authenticated == True)
        code = 0
        res = account_otp_koppel(request, account, code)
        self.assertEqual(res, False)

        # koppel met juiste code (is_authenticated == True)
        code = self._get_otp_code(account)
        res = account_otp_koppel(request, account, code)
        self.assertEqual(res, True)

        # niet ingelogd
        account = SimpleNamespace()
        account.is_authenticated = False

        request = SimpleNamespace()
        request.user = account
        request.session = self.client.session

        res = account_otp_koppel(request, account, 0)
        self.assertEqual(res, False)

    def test_rechten(self):
        request = self.client
        res = account_rechten_is_otp_verified(request)
        self.assertEqual(res, False)

# end of file
