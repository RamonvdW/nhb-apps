# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from Account.models import Account
from Logboek.models import LogboekRegel
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


class TestAccountCli(E2EHelpers, TestCase):

    """ tests voor de Account command line interface (CLI) applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        user = get_user_model()
        user.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        user.objects.create_user('admin', 'admin@test.com', 'wachtwoord')
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
            management.call_command('deblok_account', 'niet_bestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_maak_account(self):
        with self.assertRaises(ObjectDoesNotExist):
            Account.objects.get(username='nieuwe_login')
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_account', 'Voornaam', 'nieuwe_login', 'nieuw_wachtwoord',
                                    'nieuw@test.not', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue(), "Aanmaken van account 'nieuwe_login' is gelukt\n")

        account = Account.objects.get(username='nieuwe_login')
        self.assertEqual(account.username, 'nieuwe_login')
        self.assertEqual(account.first_name, 'Voornaam')
        self.assertEqual(account.email, '')
        self.assertTrue(account.is_active)
        self.assertFalse(account.is_staff)
        self.assertTrue(account.email_is_bevestigd)
        self.assertEqual(account.bevestigde_email, 'nieuw@test.not')
        self.assertEqual(account.nieuwe_email, '')

        # exception cases
        f1 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_account', 'Voornaam', 'nieuwe_login', 'nieuw_wachtwoord',
                                    'nieuw@test.not', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account bestaat al\n')

        f1 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_account', 'Voornaam', 'nieuwe_login', 'nieuw_wachtwoord',
                                    'nieuw.mh.test', stderr=f1, stdout=f2)
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
            management.call_command('maak_beheerder', 'niet_bestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_reset_otp(self):
        # non-existing user
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('reset_otp', 'nou ja zeg', stderr=f1, stdout=f2)
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
            management.call_command('deblok_account', 'niet_bestaand', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_zet_geheim(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('zet_2fa_geheim', '--zet-actief', 'normaal', '1234567890123456',
                                    stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("2FA is opgeslagen voor account 'normaal'" in f2.getvalue())

        # zonder zet-actief
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('zet_2fa_geheim', 'normaal', '1234567890123456',
                                    stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("2FA is opgeslagen voor account 'normaal'" in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('zet_2fa_geheim', 'niet_bestaand', '1', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Foutief 2FA geheim: moet 16 of 32 tekens lang zijn\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('zet_2fa_geheim', 'niet_bestaand', '1234567890123456',
                                    stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), 'Account matching query does not exist.\n')

    def test_maak_bb(self):
        LogboekRegel.objects.all().delete()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_bb', 'niet_bestaand', stderr=f1, stdout=f2)

        self.assertTrue('Kies een van --set_bb of --clr_bb' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_bb', '--set_bb', '--clr_bb', 'niet_bestaand',
                                    stderr=f1, stdout=f2)

        self.assertTrue('Kies --set_bb of --clr_bb, niet beide' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_bb', '--clr_bb', 'niet_bestaand', stderr=f1, stdout=f2)

        self.assertTrue("Geen account met de inlog naam 'niet_bestaand'" in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_bb', '--clr_bb', 'normaal', stderr=f1, stdout=f2)

        self.assertTrue("Account 'normaal' is geen BB -- geen wijziging" in f2.getvalue())
        self.assertEqual(0, LogboekRegel.objects.count())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_bb', '--set_bb', 'normaal', stderr=f1, stdout=f2)

        self.assertTrue("Account 'normaal' is BB gemaakt" in f2.getvalue())
        self.assertEqual(1, LogboekRegel.objects.count())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_bb', '--set_bb', 'normaal', 'admin', stderr=f1, stdout=f2)

        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        self.assertTrue("Account 'normaal' is al BB -- geen wijziging" in f2.getvalue())
        self.assertTrue("Account 'admin' is BB gemaakt" in f2.getvalue())
        self.assertEqual(2, LogboekRegel.objects.count())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_bb', '--clr_bb', 'normaal', stderr=f1, stdout=f2)

        self.assertTrue("Account 'normaal' is nu geen BB meer" in f2.getvalue())
        self.assertEqual(3, LogboekRegel.objects.count())

# end of file
