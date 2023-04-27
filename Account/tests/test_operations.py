# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.operations import account_test_wachtwoord_sterkte, account_email_bevestiging_ontvangen
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestAccountAanmaken(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; module Aanmaken/Email bevestigen """

    url_aangemaakt = '/account/aangemaakt/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_metmail = self.e2e_create_account('metmail', 'metmail@test.com', 'MetMail')

    def test_account_helpers(self):
        account = self.account_normaal
        account.first_name = "Normale"
        account.last_name = "Tester"
        account.save(update_fields=['first_name', 'last_name'])
        self.assertEqual(account.get_first_name(), 'Normale')
        self.assertEqual(account.volledige_naam(), 'Normale Tester')
        self.assertEqual(account.get_account_full_name(), 'Normale Tester (normaal)')

        account.first_name = ""
        account.last_name = "Tester"
        account.save(update_fields=['first_name', 'last_name'])
        self.assertEqual(account.get_first_name(), 'normaal')
        self.assertEqual(account.volledige_naam(), 'Tester')
        self.assertEqual(account.get_account_full_name(), 'Tester (normaal)')

        account.first_name = "Normale"
        account.last_name = ""
        account.save(update_fields=['first_name', 'last_name'])
        self.assertEqual(account.get_first_name(), 'Normale')
        self.assertEqual(account.volledige_naam(), 'Normale')
        self.assertEqual(account.get_account_full_name(), 'Normale (normaal)')

        account.first_name = ""
        account.last_name = ""
        account.save(update_fields=['first_name', 'last_name'])
        self.assertEqual(account.get_first_name(), 'normaal')
        self.assertEqual(account.volledige_naam(), 'normaal')
        self.assertEqual(account.get_account_full_name(), 'normaal (normaal)')

    def test_wachtwoord_sterkte(self):
        res, msg = account_test_wachtwoord_sterkte('xx', '')
        self.assertEqual((res, msg), (False, "Wachtwoord moet minimaal 9 tekens lang zijn"))

        res, msg = account_test_wachtwoord_sterkte('NHB123456', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord bevat een verboden reeks"))

        res, msg = account_test_wachtwoord_sterkte('xxxxxXXXXX', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('jajajaJAJAJA', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('blablabla', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('grootGROOT', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord bevat te veel gelijke tekens"))

        res, msg = account_test_wachtwoord_sterkte('groteGROTE', '123456')
        self.assertEqual((res, msg), (True, None))

        res, msg = account_test_wachtwoord_sterkte('wachtwoord', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('mijnGeheim', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('HandBoogSport', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('qwertyuiop', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('234567890', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('zxcvbnm,.', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord is niet sterk genoeg"))

        res, msg = account_test_wachtwoord_sterkte('passWORD!', '123456')
        self.assertEqual((res, msg), (False, "Wachtwoord is niet sterk genoeg"))

    def test_bevestiging(self):
        # corner-cases van e-mail bevestiging ontvangen
        account = self.account_metmail

        account.nieuwe_email = 'nieuwe@nhb.not'
        account.bevestigde_email = 'oude@nhb.not'
        account.email_is_bevestigd = True
        account_email_bevestiging_ontvangen(account)
        self.assertEqual(account.nieuwe_email, '')
        self.assertEqual(account.bevestigde_email, 'nieuwe@nhb.not')
        self.assertTrue(account.email_is_bevestigd)

        account.nieuwe_email = ''
        account.bevestigde_email = 'oude@nhb.not'
        account.email_is_bevestigd = True
        account_email_bevestiging_ontvangen(account)
        self.assertEqual(account.nieuwe_email, '')
        self.assertEqual(account.bevestigde_email, 'oude@nhb.not')
        self.assertTrue(account.email_is_bevestigd)

        account.nieuwe_email = 'nieuwe@nhb.not'
        account.bevestigde_email = ''
        account.email_is_bevestigd = False
        account_email_bevestiging_ontvangen(account)
        self.assertEqual(account.nieuwe_email, '')
        self.assertEqual(account.bevestigde_email, 'nieuwe@nhb.not')
        self.assertTrue(account.email_is_bevestigd)

    # er is geen view om een account direct aan te maken
    # dit wordt via Sporter gedaan

# end of file
