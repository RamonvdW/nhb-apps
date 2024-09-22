# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.definities import (MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                                   ORGANISATIE_WA, ORGANISATIE_KHSN, ORGANISATIE_IFAA)
from BasisTypen.models import (BoogType, TeamType, Leeftijdsklasse,
                               TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse,
                               KalenderWedstrijdklasse)
from BasisTypen.admin import BasisTypenTemplateCompetitieIndivKlasseAdmin
from BasisTypen.operations import get_organisatie_boogtypen, get_organisatie_teamtypen, get_organisatie_klassen


class TestBasisTypen(TestCase):

    """ tests voor de BasisTypen applicatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_basics(self):
        obj = Leeftijdsklasse()
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

        # use the __str__ method (only used by admin interface)
        team_obj = TeamType(beschrijving='Test', afkorting='X')
        self.assertIsNotNone(str(team_obj))

        obj = TemplateCompetitieTeamKlasse(beschrijving="Test")
        self.assertIsNotNone(str(obj))

        obj.team_type = team_obj
        self.assertIsNotNone(str(obj))

        boog_obj = BoogType.objects.first()
        self.assertIsNotNone(str(boog_obj))

        obj = TemplateCompetitieIndivKlasse(beschrijving="Test", boogtype=boog_obj)
        self.assertIsNotNone(str(obj))

        obj = KalenderWedstrijdklasse(beschrijving="Test")
        self.assertIsNotNone(str(obj))

    def test_admin(self):
        # FUTURE: migreer naar Beheer/tests
        adm = BasisTypenTemplateCompetitieIndivKlasseAdmin(TemplateCompetitieIndivKlasse, None)
        obj = TemplateCompetitieIndivKlasse.objects.get(volgorde=1100)
        html = adm._leeftijdsklassen(obj)
        self.assertTrue(html.count('<p>') == obj.leeftijdsklassen.count())

    def test_max_wedstrijdleeftijd(self):
        lkl = Leeftijdsklasse(
                    wedstrijd_geslacht='M',
                    min_wedstrijdleeftijd=20,
                    max_wedstrijdleeftijd=30)

        self.assertFalse(lkl.leeftijd_is_compatible(19))
        self.assertTrue(lkl.leeftijd_is_compatible(20))
        self.assertTrue(lkl.leeftijd_is_compatible(29))
        self.assertTrue(lkl.leeftijd_is_compatible(30))
        self.assertFalse(lkl.leeftijd_is_compatible(31))

        lkl = Leeftijdsklasse(
                    wedstrijd_geslacht='M',
                    min_wedstrijdleeftijd=20,
                    max_wedstrijdleeftijd=0)

        self.assertFalse(lkl.leeftijd_is_compatible(19))
        self.assertTrue(lkl.leeftijd_is_compatible(20))
        self.assertTrue(lkl.leeftijd_is_compatible(30))
        self.assertTrue(lkl.leeftijd_is_compatible(31))
        self.assertTrue(lkl.leeftijd_is_compatible(100))

    def test_geslacht(self):
        lkl = Leeftijdsklasse(
                    wedstrijd_geslacht='M',
                    min_wedstrijdleeftijd=20,
                    max_wedstrijdleeftijd=30)

        self.assertTrue(lkl.geslacht_is_compatible('M'))
        self.assertFalse(lkl.geslacht_is_compatible('V'))
        self.assertFalse(lkl.geslacht_is_compatible('X'))

        lkl = Leeftijdsklasse(
                    wedstrijd_geslacht='V',
                    min_wedstrijdleeftijd=20,
                    max_wedstrijdleeftijd=30)

        self.assertFalse(lkl.geslacht_is_compatible('M'))
        self.assertTrue(lkl.geslacht_is_compatible('V'))
        self.assertFalse(lkl.geslacht_is_compatible('X'))

        lkl = Leeftijdsklasse(
                    wedstrijd_geslacht='A',
                    min_wedstrijdleeftijd=20,
                    max_wedstrijdleeftijd=30)

        self.assertTrue(lkl.geslacht_is_compatible('M'))
        self.assertTrue(lkl.geslacht_is_compatible('V'))
        self.assertTrue(lkl.geslacht_is_compatible('X'))

    def test_operations(self):
        self.assertEqual(get_organisatie_boogtypen(ORGANISATIE_WA).count(), 5)
        self.assertEqual(get_organisatie_boogtypen(ORGANISATIE_KHSN).count(), 5)
        self.assertEqual(get_organisatie_boogtypen(ORGANISATIE_IFAA).count(), 12)

        self.assertEqual(get_organisatie_teamtypen(ORGANISATIE_WA).count(), 3)
        self.assertEqual(get_organisatie_teamtypen(ORGANISATIE_KHSN).count(), 5)
        self.assertEqual(get_organisatie_teamtypen(ORGANISATIE_IFAA).count(), 0)

        self.assertEqual(get_organisatie_klassen(ORGANISATIE_WA).count(), 40)
        self.assertEqual(get_organisatie_klassen(ORGANISATIE_KHSN).count(), 105)
        self.assertEqual(get_organisatie_klassen(ORGANISATIE_IFAA).count(), 144)

        bogen_pks = [BoogType.objects.get(afkorting='R').pk]
        klassen = get_organisatie_klassen(ORGANISATIE_WA, filter_bogen=bogen_pks)
        self.assertEqual(klassen.count(), 8)

        bogen_pks = BoogType.objects.filter(afkorting__in=('R', 'C')).values_list('pk', flat=True)
        klassen = get_organisatie_klassen(ORGANISATIE_WA, filter_bogen=bogen_pks)
        self.assertEqual(klassen.count(), 16)

        bogen_pks = BoogType.objects.filter(afkorting__in=('R', 'C')).values_list('pk', flat=True)
        klassen = get_organisatie_klassen(ORGANISATIE_KHSN, filter_bogen=bogen_pks)
        # for klasse in klassen:
        #     print(klasse)
        self.assertEqual(klassen.count(), 42)

# end of file
