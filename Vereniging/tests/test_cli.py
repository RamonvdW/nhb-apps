# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers


class TestVerenigingCli(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, command line interfaces (CLI) """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_all(self):
        f1, f2 = self.run_management_command('maak_vereniging', '1999', 'Test club', 'Test plaats')
        self.assertEqual(f1.getvalue(), '')


# end of file
