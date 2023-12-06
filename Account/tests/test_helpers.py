# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.definities import SCHEIDS_NIET, SCHEIDS_BOND
from TestHelpers.e2ehelpers import E2EHelpers


class TestAccountHelpers(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; verzameling helpers """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

    def test_get_names(self):
        account = self.account_normaal
        account.first_name = "Normale"
        account.last_name = "Tester"
        self.assertEqual(account.get_first_name(), 'Normale')
        self.assertEqual(account.volledige_naam(), 'Normale Tester')
        self.assertEqual(account.get_account_full_name(), 'Normale Tester (normaal)')

        account.first_name = ""
        account.last_name = "Tester"
        self.assertEqual(account.get_first_name(), 'normaal')
        self.assertEqual(account.volledige_naam(), 'Tester')
        self.assertEqual(account.get_account_full_name(), 'Tester (normaal)')

        account.first_name = "Normale"
        account.last_name = ""
        self.assertEqual(account.get_first_name(), 'Normale')
        self.assertEqual(account.volledige_naam(), 'Normale')
        self.assertEqual(account.get_account_full_name(), 'Normale (normaal)')

        account.first_name = ""
        account.last_name = ""
        self.assertEqual(account.get_first_name(), 'normaal')
        self.assertEqual(account.volledige_naam(), 'normaal')
        self.assertEqual(account.get_account_full_name(), 'normaal (normaal)')

        account.scheids = SCHEIDS_NIET
        self.assertFalse(account.is_scheids())
        account.scheids = SCHEIDS_BOND
        self.assertTrue(account.is_scheids())

# end of file
