# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Locatie.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers


class TestWedstrijdenLocatie(E2EHelpers, TestCase):

    """ Tests voor de Wedstrijden applicatie, module locatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_locatie(self):
        locatie = WedstrijdLocatie(
                    adres='Hallo\ndaar')
        self.assertTrue(str(locatie) != '')

        locatie.discipline_25m1pijl = True
        locatie.discipline_outdoor = True
        locatie.discipline_indoor = True
        locatie.discipline_clout = True
        locatie.discipline_veld = True
        locatie.discipline_run = True
        locatie.discipline_3d = True
        self.assertTrue(str(locatie) != '')

        locatie.zichtbaar = False
        self.assertTrue(str(locatie) != '')

# end of file
