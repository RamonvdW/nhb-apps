# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import account_test_wachtwoord_sterkte, account_email_bevestiging_ontvangen
from Overig.e2ehelpers import E2EHelpers


class TestAccountAanmaken(E2EHelpers, TestCase):
    """ unit tests voor de Account applicatie; module Aanmaken/Email bevestigen """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_metmail = self.e2e_create_account('metmail', 'metmail@test.com', 'MetMail')

        self.email_normaal = self.account_normaal.accountemail_set.all()[0]
        self.email_metmail = self.account_metmail.accountemail_set.all()[0]

    def test_aangemaakt_direct(self):
        # test rechtstreeks de 'aangemaakt' pagina ophalen, zonder registratie stappen
        # hierbij ontbreekt er een sessie variabele --> exceptie en redirect naar het plein
        resp = self.client.get('/account/aangemaakt/')
        self.assert_is_redirect(resp, '/plein/')

    def test_account_helpers(self):
        account = self.account_normaal
        account.first_name = "Normale"
        account.last_name = "Tester"
        account.save()
        self.assertEqual(account.get_first_name(), 'Normale')
        self.assertEqual(account.volledige_naam(), 'Normale Tester')
        self.assertEqual(account.get_account_full_name(), 'Normale Tester (normaal)')

        account.first_name = ""
        account.last_name = "Tester"
        account.save()
        self.assertEqual(account.get_first_name(), 'normaal')
        self.assertEqual(account.volledige_naam(), 'Tester')
        self.assertEqual(account.get_account_full_name(), 'Tester (normaal)')

        account.first_name = "Normale"
        account.last_name = ""
        account.save()
        self.assertEqual(account.get_first_name(), 'Normale')
        self.assertEqual(account.volledige_naam(), 'Normale')
        self.assertEqual(account.get_account_full_name(), 'Normale (normaal)')

        account.first_name = ""
        account.last_name = ""
        account.save()
        self.assertEqual(account.get_first_name(), 'normaal')
        self.assertEqual(account.volledige_naam(), 'normaal')
        self.assertEqual(account.get_account_full_name(), 'normaal (normaal)')

    def test_email(self):
        account = self.account_normaal
        email = self.email_normaal
        self.assertEqual(account.get_email(), 'normaal@test.com')

        email.delete()
        self.assertEqual(account.get_email(), '')

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
        email = self.email_metmail

        email.nieuwe_email = 'nieuwe@nhb.not'
        email.bevestigde_email = 'oude@nhb.not'
        email.email_is_bevestigd = True
        account_email_bevestiging_ontvangen(email)
        self.assertEqual(email.nieuwe_email, '')
        self.assertEqual(email.bevestigde_email, 'nieuwe@nhb.not')
        self.assertTrue(email.email_is_bevestigd)

        email.nieuwe_email = ''
        email.bevestigde_email = 'oude@nhb.not'
        email.email_is_bevestigd = True
        account_email_bevestiging_ontvangen(email)
        self.assertEqual(email.nieuwe_email, '')
        self.assertEqual(email.bevestigde_email, 'oude@nhb.not')
        self.assertTrue(email.email_is_bevestigd)

        email.nieuwe_email = 'nieuwe@nhb.not'
        email.bevestigde_email = ''
        email.email_is_bevestigd = False
        account_email_bevestiging_ontvangen(email)
        self.assertEqual(email.nieuwe_email, '')
        self.assertEqual(email.bevestigde_email, 'nieuwe@nhb.not')
        self.assertTrue(email.email_is_bevestigd)

    # er is geen view om een account direct aan te maken
    # dit wordt via Schutter gedaan

# end of file
