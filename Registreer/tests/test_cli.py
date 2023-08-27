# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestRegistreerCli(E2EHelpers, TestCase):

    """ tests voor de Registreer application, command line interfaces (CLI) """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_all(self):
        ver = Vereniging.objects.first()

        f1, f2 = self.run_management_command('maak_gebruiker', str(ver.ver_nr), '199901', 'Voornaam', '2000-01-01', 'BB+C')
        self.assertEqual(f1.getvalue(), '')


# end of file
