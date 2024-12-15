# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers


class TestInstaptoetsCli(E2EHelpers, TestCase):
    """ unittests voor de Instaptoets applicatie, management command laad_instaptoets """

    file_vragen_1 = 'test-files/vragen_1.csv'

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_basis(self):
        f1, f2 = self.run_management_command('laad_instaptoets')
        print("f1: %s" % f1.getvalue())
        print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')

# end of file
