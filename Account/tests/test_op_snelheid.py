# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import AccountVerzoekenTeller
from Account.operations import account_controleer_snelheid_verzoeken
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestAccountAanmaken(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; operations module Snelheid """

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account = self.testdata.account_admin

    def test_rate_limiter(self):

        # 0 --> 1
        check = account_controleer_snelheid_verzoeken(self.account)
        self.assertTrue(check)

        # 1 --> 2
        check = account_controleer_snelheid_verzoeken(self.account, limiet=2)
        self.assertTrue(check)

        # 2 --> 3 > limiet
        check = account_controleer_snelheid_verzoeken(self.account, limiet=2)
        self.assertFalse(check)

        # verander het uur nummer
        teller = AccountVerzoekenTeller.objects.get(account=self.account)
        teller.uur_nummer -= 1
        teller.save()

        check = account_controleer_snelheid_verzoeken(self.account, limiet=2)
        self.assertTrue(check)

# end of file
