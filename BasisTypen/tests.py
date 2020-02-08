# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import BoogType, TeamType, WedstrijdKlasse, LeeftijdsKlasse, TeamTypeBoog, WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd
from Account.models import Account, account_zet_sessionvars_na_otp_controle
from Account.rol import rol_zet_sessionvars_na_login
from Plein.tests import assert_html_ok, assert_template_used


class TestBasisTypen(TestCase):
    """ unit tests voor de BasisTypen applicatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BKO aan, nodig om de competitie defaults in te zien
        usermodel = get_user_model()
        usermodel.objects.create_user('bko', 'bko@test.com', 'wachtwoord')
        account = Account.objects.get(username='bko')
        account.is_BKO = True
        account.save()
        self.account_bko = account

    def test_boogtype(self):
        obj = BoogType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_teamtype(self):
        obj = TeamType.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_wedstrijdklasse(self):
        obj = WedstrijdKlasse.objects.filter(is_voor_teams=False)[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = WedstrijdKlasse.objects.filter(is_voor_teams=True)[0]
        self.assertIsNotNone(str(obj))

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

# end of file

