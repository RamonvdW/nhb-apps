# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import (BoogType, TeamType, LeeftijdsKlasse, MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                     IndivWedstrijdklasse, TeamWedstrijdklasse, KalenderWedstrijdklasse)
from .admin import BasisTypenIndivWedstrijdklasseAdmin, BasisTypenTeamWedstrijdklasseAdmin


class TestBasisTypen(TestCase):
    """ unit tests voor de BasisTypen applicatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_basics(self):
        obj = BoogType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = LeeftijdsKlasse()
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj.min_wedstrijdleeftijd = 0
        obj.max_wedstrijdleeftijd = MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT - 1
        self.assertTrue(obj.is_aspirant_klasse())

        obj.min_wedstrijdleeftijd = 0
        obj.max_wedstrijdleeftijd = MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT + 1
        self.assertFalse(obj.is_aspirant_klasse())

        obj.min_wedstrijdleeftijd = 0
        obj.max_wedstrijdleeftijd = MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
        self.assertTrue(obj.is_aspirant_klasse())

        obj.min_wedstrijdleeftijd = 0
        obj.max_wedstrijdleeftijd = 0
        self.assertFalse(obj.is_aspirant_klasse())

        obj.min_wedstrijdleeftijd = 0
        obj.min_wedstrijdleeftijd = 60
        self.assertFalse(obj.is_aspirant_klasse())

        obj = IndivWedstrijdklasse(beschrijving="Test")
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = TeamWedstrijdklasse(beschrijving="Test")
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = KalenderWedstrijdklasse(beschrijving="Test")
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = TeamType(beschrijving='Test', afkorting='X')
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_admin(self):
        adm = BasisTypenIndivWedstrijdklasseAdmin(IndivWedstrijdklasse, None)
        obj = IndivWedstrijdklasse.objects.get(volgorde=100)
        html = adm._leeftijdsklassen(obj)
        self.assertTrue(html.count('<p>') == obj.leeftijdsklassen.count())

    def test_max_wedstrijdleeftijd(self):
        lkl = LeeftijdsKlasse(
                    geslacht='M',
                    min_wedstrijdleeftijd=20,
                    max_wedstrijdleeftijd=30)

        self.assertFalse(lkl.leeftijd_is_compatible(19))
        self.assertTrue(lkl.leeftijd_is_compatible(20))
        self.assertTrue(lkl.leeftijd_is_compatible(29))
        self.assertTrue(lkl.leeftijd_is_compatible(30))
        self.assertFalse(lkl.leeftijd_is_compatible(31))

        lkl = LeeftijdsKlasse(
                    geslacht='M',
                    min_wedstrijdleeftijd=20,
                    max_wedstrijdleeftijd=0)

        self.assertFalse(lkl.leeftijd_is_compatible(19))
        self.assertTrue(lkl.leeftijd_is_compatible(20))
        self.assertTrue(lkl.leeftijd_is_compatible(30))
        self.assertTrue(lkl.leeftijd_is_compatible(31))
        self.assertTrue(lkl.leeftijd_is_compatible(100))

# end of file

