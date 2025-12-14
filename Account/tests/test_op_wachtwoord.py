# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.operations import account_test_wachtwoord_sterkte
from TestHelpers.e2ehelpers import E2EHelpers


class TestAccountOpWachtwoord(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; operations module Wachtwoord """

    def test_wachtwoord_sterkte(self):
        res, msg = account_test_wachtwoord_sterkte('xx', '')
        self.assertEqual((res, msg), (False, "wachtwoord is te kort"))

        res, msg = account_test_wachtwoord_sterkte('KHSN123456', '123456')
        self.assertEqual((res, msg), (False, "wachtwoord bevat een verboden reeks"))

        res, msg = account_test_wachtwoord_sterkte('xxxxxXXXXX', '123456')      # noqa
        self.assertEqual((res, msg), (False, "wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('jajajaJAJAJA', '123456')    # noqa
        self.assertEqual((res, msg), (False, "wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('blablabla', '123456')       # noqa
        self.assertEqual((res, msg), (False, "wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('grootGROOT', '123456')
        self.assertEqual((res, msg), (False, "wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('groteGROTE', '123456')
        self.assertEqual((res, msg), (True, None))

        res, msg = account_test_wachtwoord_sterkte('wachtwoord', '123456')
        self.assertEqual((res, msg), (False, "wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('mijnGeheim', '123456')
        self.assertEqual((res, msg), (False, "wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('HandBoogSport', '123456')
        self.assertEqual((res, msg), (False, "wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('qwertyuiop', '123456')      # noqa
        self.assertEqual((res, msg), (False, "wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('234567890', '123456')
        self.assertEqual((res, msg), (False, "wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('zxcvbnm,.', '123456')       # noqa
        self.assertEqual((res, msg), (False, "wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('passWORD!', '123456')
        self.assertEqual((res, msg), (False, "wachtwoord is niet sterk genoeg"))

# end of file
