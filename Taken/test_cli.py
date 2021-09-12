# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from .models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
import io


class TestTakenCLI(E2EHelpers, TestCase):
    """ unittests voor de Taken applicatie, management command maak_taak """

    def setUp(self):
        """ initialisatie van de test case """
        self.account1 = self.e2e_create_account('eerste', 'eerste@test.com', 'Eer ste')
        self.account2 = self.e2e_create_account('tweede', 'tweede@test.com', 'Twee de')

    def test_een(self):
        self.assertEqual(0, Taak.objects.count())
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_taak', 'eerste', 'tweede', '2020-02-03', '', 'Hallo', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertEqual(1, Taak.objects.count())

        taak = Taak.objects.all()[0]
        self.assertEqual(str(taak.deadline), '2020-02-03')

    def test_systeem(self):
        self.assertEqual(0, Taak.objects.count())
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_taak', 'eerste', 'systeem', '2020-02-03', '', 'Hallo', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertEqual(1, Taak.objects.count())

    def test_bad(self):
        self.assertEqual(0, Taak.objects.count())
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_taak', 'derde', 'systeem', '2020-02-03', '', 'Hallo', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertEqual(0, Taak.objects.count())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_taak', 'eerste', 'derde', '2020-02-03', '', 'Hallo', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertEqual(0, Taak.objects.count())

    def test_no_email(self):
        email = self.account1.accountemail_set.all()[0]
        email.bevestigde_email = ''
        email.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('maak_taak', 'eerste', 'systeem', '2020-02-03', '', 'Hallo', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[ERROR] geen e-mailadres bekend voor account Eer' in f1.getvalue())

# end of file
