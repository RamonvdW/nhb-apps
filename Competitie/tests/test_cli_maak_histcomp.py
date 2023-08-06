# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.operations import competities_aanmaken
from TestHelpers.e2ehelpers import E2EHelpers


class TestCompetitieCliMaakHistcomp(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command maak_histcomp """

    def test_maak(self):
        f1, f2 = self.run_management_command('maak_histcomp', '18')
        competities_aanmaken(2019)

        f1, f2 = self.run_management_command('maak_histcomp', '18')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

# end of file
