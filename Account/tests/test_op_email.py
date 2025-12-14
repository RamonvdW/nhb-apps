# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.operations import account_email_bevestiging_ontvangen
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestAccountOpEmail(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; operations module wachtwoord """

    url_aangemaakt = '/account/aangemaakt/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_metmail = self.e2e_create_account('metmail', 'metmail@test.com', 'MetMail')

    def test_bevestiging(self):
        # corner-cases van e-mail bevestiging ontvangen
        account = self.account_metmail

        account.nieuwe_email = 'nieuwe@test.not'
        account.bevestigde_email = 'oude@test.not'
        account.email_is_bevestigd = True
        account_email_bevestiging_ontvangen(account)
        self.assertEqual(account.nieuwe_email, '')
        self.assertEqual(account.bevestigde_email, 'nieuwe@test.not')
        self.assertTrue(account.email_is_bevestigd)

        account.nieuwe_email = ''
        account.bevestigde_email = 'oude@test.not'
        account.email_is_bevestigd = True
        account_email_bevestiging_ontvangen(account)
        self.assertEqual(account.nieuwe_email, '')
        self.assertEqual(account.bevestigde_email, 'oude@test.not')
        self.assertTrue(account.email_is_bevestigd)

        account.nieuwe_email = 'nieuwe@test.not'
        account.bevestigde_email = ''
        account.email_is_bevestigd = False
        account_email_bevestiging_ontvangen(account)
        self.assertEqual(account.nieuwe_email, '')
        self.assertEqual(account.bevestigde_email, 'nieuwe@test.not')
        self.assertTrue(account.email_is_bevestigd)

# end of file
