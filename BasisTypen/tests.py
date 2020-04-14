# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import BoogType, LeeftijdsKlasse, IndivWedstrijdklasse, TeamWedstrijdklasse


class TestBasisTypen(TestCase):
    """ unit tests voor de BasisTypen applicatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_boogtype(self):
        obj = BoogType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_leeftijdklasse(self):
        obj = LeeftijdsKlasse()
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_indiv_wedstrijdklasse(self):
        obj = IndivWedstrijdklasse(beschrijving="Test")
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_team_wedstrijdklasse(self):
        obj = TeamWedstrijdklasse(beschrijving="Test")
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

# end of file

