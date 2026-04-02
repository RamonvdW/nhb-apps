# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.operations import account_create, AccountCreateError


class TestAccountOpAanmaken(TestCase):

    """ tests voor de Account applicatie; operations module Aanmaken """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_create(self):
        with self.assertRaises(AccountCreateError) as exc:
            account_create('123456', 'Test', 'de Tester', 'wachtwoord',
                           'bad email', False)
            self.assertTrue('Dit is geen valide e-mail' in str(exc))

        email = 'test@khsn.not'

        account = account_create('123456', 'Test', 'de Tester', 'wachtwoord', email, False)
        self.assertFalse(account.email_is_bevestigd)
        self.assertEqual(account.bevestigde_email, '')
        self.assertEqual(account.nieuwe_email, email)

        account = account_create('123457', 'Test', 'de Tester', 'wachtwoord', email, True)
        self.assertTrue(account.email_is_bevestigd)
        self.assertEqual(account.bevestigde_email, email)
        self.assertEqual(account.nieuwe_email, '')

        # double create
        with self.assertRaises(AccountCreateError) as exc:
            account_create('123457', 'Test', 'de Tester', 'wachtwoord', email, True)
            self.assertTrue('Account bestaat al' in str(exc))

# end of file
