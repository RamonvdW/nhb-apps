# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers


class TestTakenCLI(E2EHelpers, TestCase):
    """ unittests voor de applicatie Taken, management command maak_taak """

    emailadres = 'mwz@nhb.not'

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_alles(self):
        self.assertEqual(0, Taak.objects.count())

        account = self.e2e_create_account('normal', 'normal@nhb.not', 'Normaal')
        functie = Functie.objects.get(rol='MWZ')

        f1, f2 = self.run_management_command('maak_taak', 'BlaBla', '', '2020-02-03', 'Hallo')
        self.assertTrue("[ERROR] Geen functie gevonden die voldoet aan 'BlaBla'")
        self.assertEqual(f2.getvalue(), '')
        self.assertEqual(0, Taak.objects.count())

        functie.bevestigde_email = ''
        functie.save(update_fields=['bevestigde_email'])

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_taak', 'MWZ', '', '2020-02-03', 'Hallo')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[WARNING] Geen e-mailadres bekend voor functie Manager Wedstrijdzaken" in f2.getvalue())

        self.assertEqual(1, Taak.objects.count())
        taak = Taak.objects.all()[0]
        self.assertEqual(str(taak.deadline), '2020-02-03')
        self.assertEqual(taak.toegekend_aan_functie, functie)
        self.assertIsNone(taak.aangemaakt_door)
        taak.delete()

        functie.bevestigde_email = self.emailadres
        functie.save(update_fields=['bevestigde_email'])

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_taak', 'MWZ', account.username, '2020-02-03', 'Hallo')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue('Taak aangemaakt door normal voor functie Manager Wedstrijdzaken met deadline 2020-02-03' in f2.getvalue())

        self.assertEqual(1, Taak.objects.count())
        taak = Taak.objects.all()[0]
        self.assertEqual(str(taak.deadline), '2020-02-03')
        self.assertEqual(taak.aangemaakt_door, account)
        self.assertEqual(taak.toegekend_aan_functie, functie)

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_taak', 'MWZ', 'BlaBla', '2020-02-03', 'Hallo')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Account matching query does not exist' in f1.getvalue())

        # er zijn meerdere RCL's, dus dit is niet duidelijk genoeg
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('maak_taak', 'RCL', 'BlaBla', '2020-02-03', 'Hallo')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Meerdere functies gevonden die voldoen aan 'RCL'" in f1.getvalue())

# end of file
