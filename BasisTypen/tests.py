# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import BoogType, LeeftijdsKlasse, IndivWedstrijdklasse, TeamWedstrijdklasse
from .admin import BasisTypenIndivWedstrijdklasseAdmin, BasisTypenTeamWedstrijdklasseAdmin


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

    def test_html(self):
        adm = BasisTypenIndivWedstrijdklasseAdmin(IndivWedstrijdklasse, None)
        obj = IndivWedstrijdklasse.objects.get(volgorde=100)
        html = adm._leeftijdsklassen(obj)
        self.assertTrue(html.count('<p>') == obj.leeftijdsklassen.count())

        adm = BasisTypenTeamWedstrijdklasseAdmin(TeamWedstrijdklasse, None)
        obj = TeamWedstrijdklasse.objects.get(volgorde=10)
        html = adm._boogtypen(obj)
        self.assertTrue(html.count('<p>') == obj.boogtypen.count())

# end of file

