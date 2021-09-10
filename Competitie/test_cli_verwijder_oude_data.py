# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from Overig.e2ehelpers import E2EHelpers
import io


class TestCompetitieCliRegiocompTussenstand(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command verwijder_oude_data """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_basis(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('verwijder_oude_data', stderr=f1, stdout=f2)

        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Searching' in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('verwijder_oude_data', '--commit', stderr=f1, stdout=f2)

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Searching' in f2.getvalue())


# end of file
