# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from django.core import management
from .models import Account, AccountEmail
from Overig.e2ehelpers import E2EHelpers
import datetime
import io


class TestAccountCLI(E2EHelpers, TestCase):
    """ unit tests voor de Account command line interface (CLI) applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

    def test_deblok_account(self):
        # validate precondition
        self.assertIsNone(self.account_normaal.is_geblokkeerd_tot)

        # de-block when not blocked
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('deblok_account', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' is niet geblokkeerd\n")

        # blokkeren
        self.account_normaal.is_geblokkeerd_tot = timezone.now() + datetime.timedelta(hours=1)
        self.account_normaal.save()

        # de-block
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('deblok_account', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' is niet meer geblokkeerd\n")
        # validate
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertTrue(self.account_normaal.is_geblokkeerd_tot <= timezone.now())

        # exception case
        with self.assert_max_queries(20):
            management.call_command('deblok_account', 'nietbestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_maak_account(self):
        with self.assertRaises(Account.DoesNotExist):
            Account.objects.get(username='nieuwelogin')
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_account', 'Voornaam', 'nieuwelogin', 'nieuwwachtwoord', 'nieuw@nhb.test', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Aanmaken van account 'nieuwelogin' is gelukt\n")
        obj = Account.objects.get(username='nieuwelogin')
        self.assertEqual(obj.username, 'nieuwelogin')
        self.assertEqual(obj.first_name, 'Voornaam')
        self.assertEqual(obj.email, '')
        self.assertTrue(obj.is_active)
        self.assertFalse(obj.is_staff)
        self.assertFalse(obj.is_superuser)

        mail = AccountEmail.objects.get(account=obj)
        self.assertTrue(mail.email_is_bevestigd)
        self.assertEqual(mail.bevestigde_email, 'nieuw@nhb.test')
        self.assertEqual(mail.nieuwe_email, '')

        # coverage voor AccountEmail.__str__()
        self.assertEqual(str(mail), "E-mail voor account 'nieuwelogin' (nieuw@nhb.test)")

        # exception cases
        f1 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_account', 'Voornaam', 'nieuwelogin', 'nieuwwachtwoord', 'nieuw@nhb.test', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account bestaat al\n')

        f1 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_account', 'Voornaam', 'nieuwelogin', 'nieuwwachtwoord', 'nieuw.nhb.test', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Dat is geen valide e-mail\n')

    def test_maak_beheerder(self):
        self.assertFalse(self.account_normaal.is_staff)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_beheerder', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' is beheerder gemaakt\n")
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertTrue(self.account_normaal.is_staff)

        # exception case
        with self.assert_max_queries(20):
            management.call_command('maak_beheerder', 'nietbestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_reset_otp(self):
        # non-existing user
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('reset_otp', 'noujazeg', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), "Account matching query does not exist.\n")
        self.assertEqual(f2.getvalue(), '')

        # OTP is niet actief
        self.account_normaal.otp_is_actief = False
        self.account_normaal.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('reset_otp', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' heeft OTP niet aan staan\n")

        # OTP resetten
        self.account_normaal.otp_is_actief = True
        self.account_normaal.otp_code = "1234"
        self.account_normaal.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('reset_otp', 'normaal', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' moet nu opnieuw de OTP koppeling leggen\n")
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertFalse(self.account_normaal.otp_is_actief)
        self.assertEqual(self.account_normaal.otp_code, "1234")

        # OTP resetten + otp_code vergeten
        self.account_normaal.otp_is_actief = True
        self.account_normaal.otp_code = "1234"
        self.account_normaal.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('reset_otp', 'normaal', '--reset_secret', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Account 'normaal' moet nu opnieuw de OTP koppeling leggen\n")
        self.account_normaal = Account.objects.get(username='normaal')
        self.assertFalse(self.account_normaal.otp_is_actief)
        self.assertNotEqual(self.account_normaal.otp_code, "1234")

        # exception case
        with self.assert_max_queries(20):
            management.call_command('deblok_account', 'nietbestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_zet_geheim(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('zet_2fa_geheim', 'normaal', '1234567890123456', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("2FA is opgeslagen voor account 'normaal'" in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('zet_2fa_geheim', 'nietbestaand', '1', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Foutief 2FA geheim: moet 16 of 32 tekens lang zijn\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('zet_2fa_geheim', 'nietbestaand', '1234567890123456', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

# end of file
