# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import BoogType, TeamType, WedstrijdKlasse, LeeftijdsKlasse, TeamTypeBoog, WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd
from Plein.tests import assert_html_ok, assert_template_used


class TestBasisTypen(TestCase):
    """ unit tests voor de BasisTypen application """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        obj = BoogType(afkorting='R', beschrijving='Recurve')
        obj.save()

        obj = TeamType(beschrijving="Een team type")
        obj.save()

        obj = WedstrijdKlasse(beschrijving="Wedstrijdklasse Test", niet_voor_rk_bk=True, is_voor_teams=False, min_ag='9.000')
        obj.save()

        obj = LeeftijdsKlasse(afkorting="CH", geslacht="M", max_wedstrijdleeftijd=17, beschrijving="Heren Cadet")
        obj.save()

    def test_boogtype(self):
        obj = BoogType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_teamtype(self):
        obj = TeamType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_wedstrijdklasse(self):
        obj = WedstrijdKlasse.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_leeftijdklasse(self):
        obj = LeeftijdsKlasse()
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_teamtypeboog(self):
        obj = TeamTypeBoog()
        obj.teamtype = TeamType.objects.all()[0]
        obj.boogtype = BoogType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_wedstrijdklasseboog(self):
        obj = WedstrijdKlasseBoog()
        obj.wedstrijdklasse = WedstrijdKlasse.objects.all()[0]
        obj.boogtype = BoogType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_wedstrijdklasseleeftijd(self):
        obj = WedstrijdKlasseLeeftijd()
        obj.wedstrijdklasse = WedstrijdKlasse.objects.all()[0]
        obj.leeftijdsklasse = LeeftijdsKlasse.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_competitie_defaults(self):
        resp = self.client.get('/overig/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('basistypen/competitie-defaults.dtl', 'plein/site_layout.dtl'))

# end of file

