# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import (GESLACHT_ANDERS, GESLACHT_MAN, GESLACHT_VROUW,
                               ORGANISATIE_IFAA, ORGANISATIE_NHB, ORGANISATIE_WA)
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.leeftijdsklassen import (bereken_leeftijdsklassen_wa,
                                      bereken_leeftijdsklassen_nhb,
                                      bereken_leeftijdsklassen_ifaa,
                                      bereken_leeftijdsklassen_bondscompetitie,
                                      bereken_leeftijdsklasse_wa,
                                      bereken_leeftijdsklasse_nhb,
                                      bereken_leeftijdsklasse_ifaa)
from Sporter.models import Sporter, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestSporterLeeftijdsklassen(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Leeftijdsklassen """

    url_leeftijdsklassen = '/sporter/leeftijden/persoonlijk/'
    url_leeftijdsgroepen = '/sporter/leeftijden/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@test.com', 'Geen')

        now = timezone.now()  # is in UTC
        now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
        self.huidige_jaar = now.year

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_normaal
        sporter.email = sporter.account.email
        sporter.save()
        self.sporter1 = sporter

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

    def test_model(self):
        datum_wedstrijd_voor_verjaardag = datetime.date(2022, month=self.sporter1.geboorte_datum.month,
                                                        day=self.sporter1.geboorte_datum.day-1)
        datum_wedstrijd_op_verjaardag = datetime.date(2022, month=self.sporter1.geboorte_datum.month,
                                                      day=self.sporter1.geboorte_datum.day)
        datum_wedstrijd_na_verjaardag = datetime.date(2022, month=self.sporter1.geboorte_datum.month,
                                                      day=self.sporter1.geboorte_datum.day+1)

        # IFAA hanteert echte leeftijd
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_IFAA)
        self.assertEqual(n, 49)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_IFAA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_IFAA)
        self.assertEqual(n, 50)

        # WA en NHB hanteren kijken het hele jaar naar de leeftijd die je bereikt
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)

        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_NHB)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_NHB)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_NHB)
        self.assertEqual(n, 50)

    def test_leeftijdsklassen_wa(self):
        # Onder 12
        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 9, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 9,
                          'Onder 18 Heren',
                          ['Onder 18 Heren', 'Onder 18 Heren', 'Onder 18 Heren', 'Onder 18 Heren', 'Onder 18 Heren']))

        # Onder 18
        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 17, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 17,
                          'Onder 18 Heren',
                          ['Onder 18 Heren', 'Onder 18 Heren', 'Onder 21 Heren', 'Onder 21 Heren', 'Onder 21 Heren']))

        # Onder 21
        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 20, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 20,
                          'Onder 21 Heren',
                          ['Onder 21 Heren', 'Onder 21 Heren', 'Heren', 'Heren', 'Heren']))

        # 21+
        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 21, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 21,
                          'Heren',
                          ['Onder 21 Heren', 'Heren', 'Heren', 'Heren', 'Heren']))

        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 49, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 49,
                          'Heren',
                          ['Heren', 'Heren', '50+ Heren', '50+ Heren', '50+ Heren']))

        # 50+
        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 50, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 50,
                          '50+ Heren',
                          ['Heren', '50+ Heren', '50+ Heren', '50+ Heren', '50+ Heren']))

        # 50+
        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 100, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 100,
                          '50+ Heren',
                          ['50+ Heren', '50+ Heren', '50+ Heren', '50+ Heren', '50+ Heren']))

        # niet compatibel
        tup = bereken_leeftijdsklassen_wa(self.huidige_jaar - 50, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertIsNone(tup[2])

    def test_leeftijdsklasse_wa(self):
        # Onder 12
        beschrijving = bereken_leeftijdsklasse_wa(9, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Onder 18 Heren')

        # Onder 18
        beschrijving = bereken_leeftijdsklasse_wa(17, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Onder 18 Heren')

        # Onder 21
        beschrijving = bereken_leeftijdsklasse_wa(20, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Onder 21 Heren')

        # 21+
        beschrijving = bereken_leeftijdsklasse_wa(21, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Heren')

        beschrijving = bereken_leeftijdsklasse_wa(49, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Heren')

        # 50+
        beschrijving = bereken_leeftijdsklasse_wa(50, GESLACHT_MAN)
        self.assertEqual(beschrijving, '50+ Heren')

        # 50+
        beschrijving = bereken_leeftijdsklasse_wa(100, GESLACHT_VROUW)
        self.assertEqual(beschrijving, '50+ Dames')

        # niet compatibel
        beschrijving = bereken_leeftijdsklasse_wa(50, GESLACHT_ANDERS)
        self.assertEqual(beschrijving, '?')

    def test_leeftijdsklassen_nhb(self):
        # Onder 12
        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 9, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 9,
                          'Onder 12 Uniseks of Onder 12 Jongens',
                          ['Onder 12 Uniseks of Onder 12 Jongens', 'Onder 12 Uniseks of Onder 12 Jongens',
                           'Onder 12 Uniseks of Onder 12 Jongens', 'Onder 12 Uniseks of Onder 12 Jongens',
                           'Onder 14 Uniseks of Onder 14 Jongens']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 9, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 9,
                          'Onder 12 Uniseks of Onder 12 Meisjes',
                          ['Onder 12 Uniseks of Onder 12 Meisjes', 'Onder 12 Uniseks of Onder 12 Meisjes',
                           'Onder 12 Uniseks of Onder 12 Meisjes', 'Onder 12 Uniseks of Onder 12 Meisjes',
                           'Onder 14 Uniseks of Onder 14 Meisjes']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 9, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 9,
                          'Onder 12 Uniseks',
                          ['Onder 12 Uniseks', 'Onder 12 Uniseks', 'Onder 12 Uniseks',
                           'Onder 12 Uniseks', 'Onder 14 Uniseks']))

        # Onder 14
        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 13, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 13,
                          'Onder 14 Uniseks of Onder 14 Jongens',
                          ['Onder 14 Uniseks of Onder 14 Jongens', 'Onder 14 Uniseks of Onder 14 Jongens',
                           'Onder 18 Uniseks of Onder 18 Heren', 'Onder 18 Uniseks of Onder 18 Heren',
                           'Onder 18 Uniseks of Onder 18 Heren']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 13, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 13,
                          'Onder 14 Uniseks of Onder 14 Meisjes',
                          ['Onder 14 Uniseks of Onder 14 Meisjes', 'Onder 14 Uniseks of Onder 14 Meisjes',
                           'Onder 18 Uniseks of Onder 18 Dames', 'Onder 18 Uniseks of Onder 18 Dames',
                           'Onder 18 Uniseks of Onder 18 Dames']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 13, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 13,
                          'Onder 14 Uniseks',
                          ['Onder 14 Uniseks', 'Onder 14 Uniseks', 'Onder 18 Uniseks',
                           'Onder 18 Uniseks', 'Onder 18 Uniseks']))

        # 21+
        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 21, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 21,
                          'Uniseks of Heren',
                          ['Onder 21 Uniseks of Onder 21 Heren', 'Uniseks of Heren', 'Uniseks of Heren',
                           'Uniseks of Heren', 'Uniseks of Heren']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 21, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 21,
                          'Uniseks of Dames',
                          ['Onder 21 Uniseks of Onder 21 Dames', 'Uniseks of Dames', 'Uniseks of Dames',
                           'Uniseks of Dames', 'Uniseks of Dames']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 21, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 21,
                          'Uniseks',
                          ['Onder 21 Uniseks', 'Uniseks', 'Uniseks', 'Uniseks', 'Uniseks']))

        # 50+
        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 50, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 50,
                          '50+ Uniseks of 50+ Heren',
                          ['Uniseks of Heren', '50+ Uniseks of 50+ Heren', '50+ Uniseks of 50+ Heren',
                           '50+ Uniseks of 50+ Heren', '50+ Uniseks of 50+ Heren']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 50, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 50,
                          '50+ Uniseks of 50+ Dames',
                          ['Uniseks of Dames', '50+ Uniseks of 50+ Dames', '50+ Uniseks of 50+ Dames',
                           '50+ Uniseks of 50+ Dames', '50+ Uniseks of 50+ Dames']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 50, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 50,
                          '50+ Uniseks',
                          ['Uniseks', '50+ Uniseks', '50+ Uniseks', '50+ Uniseks', '50+ Uniseks']))

        # 60+
        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 60, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 60,
                          '60+ Uniseks of 60+ Heren',
                          ['50+ Uniseks of 50+ Heren', '60+ Uniseks of 60+ Heren', '60+ Uniseks of 60+ Heren',
                           '60+ Uniseks of 60+ Heren', '60+ Uniseks of 60+ Heren']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 60, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 60,
                          '60+ Uniseks of 60+ Dames',
                          ['50+ Uniseks of 50+ Dames', '60+ Uniseks of 60+ Dames', '60+ Uniseks of 60+ Dames',
                           '60+ Uniseks of 60+ Dames', '60+ Uniseks of 60+ Dames']))

        tup = bereken_leeftijdsklassen_nhb(self.huidige_jaar - 60, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (2022, 60,
                          '60+ Uniseks',
                          ['50+ Uniseks', '60+ Uniseks', '60+ Uniseks', '60+ Uniseks', '60+ Uniseks']))

    def test_leeftijdsklasse_nhb(self):
        # Onder 12
        tup = bereken_leeftijdsklasse_nhb(9, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 12 Jongens')

        tup = bereken_leeftijdsklasse_nhb(10, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 12 Meisjes')

        tup = bereken_leeftijdsklasse_nhb(11, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 12 Uniseks')

        # Onder 14
        tup = bereken_leeftijdsklasse_nhb(12, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 14 Jongens')

        tup = bereken_leeftijdsklasse_nhb(13, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 14 Meisjes')

        tup = bereken_leeftijdsklasse_nhb(13, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 14 Uniseks')

        # Onder 18
        tup = bereken_leeftijdsklasse_nhb(14, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 18 Heren')

        tup = bereken_leeftijdsklasse_nhb(15, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 18 Dames')

        tup = bereken_leeftijdsklasse_nhb(17, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 18 Uniseks')

        # Onder 21
        tup = bereken_leeftijdsklasse_nhb(18, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 21 Heren')

        tup = bereken_leeftijdsklasse_nhb(19, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 21 Dames')

        tup = bereken_leeftijdsklasse_nhb(20, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 21 Uniseks')

        # 21+
        tup = bereken_leeftijdsklasse_nhb(21, GESLACHT_MAN)
        self.assertEqual(tup, 'Heren')

        tup = bereken_leeftijdsklasse_nhb(30, GESLACHT_VROUW)
        self.assertEqual(tup, 'Dames')

        tup = bereken_leeftijdsklasse_nhb(40, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Uniseks')

        # 50+
        tup = bereken_leeftijdsklasse_nhb(50, GESLACHT_MAN)
        self.assertEqual(tup, '50+ Heren')

        tup = bereken_leeftijdsklasse_nhb(50, GESLACHT_VROUW)
        self.assertEqual(tup, '50+ Dames')

        tup = bereken_leeftijdsklasse_nhb(50, GESLACHT_ANDERS)
        self.assertEqual(tup, '50+ Uniseks')

        # 60+
        tup = bereken_leeftijdsklasse_nhb(60, GESLACHT_MAN)
        self.assertEqual(tup, '60+ Heren')

        tup = bereken_leeftijdsklasse_nhb(60, GESLACHT_VROUW)
        self.assertEqual(tup, '60+ Dames')

        tup = bereken_leeftijdsklasse_nhb(60, GESLACHT_ANDERS)
        self.assertEqual(tup, '60+ Uniseks')

    def test_leeftijdsklassen_ifaa(self):
        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 9, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Welpen Jongens', 'Welpen Jongens'),
                               (2022, 'Welpen Jongens', 'Welpen Jongens'),
                               (2023, 'Welpen Jongens', 'Welpen Jongens'),
                               (2024, 'Welpen Jongens', 'Welpen Jongens'),
                               (2025, 'Welpen Jongens', 'Welpen Jongens')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 13, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Welpen Jongens', 'Welpen Jongens'),
                               (2022, 'Welpen Jongens', 'Junioren Jongens'),
                               (2023, 'Junioren Jongens', 'Junioren Jongens'),
                               (2024, 'Junioren Jongens', 'Junioren Jongens'),
                               (2025, 'Junioren Jongens', 'Junioren Jongens')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 16, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Junioren Jongens', 'Junioren Jongens'),
                               (2022, 'Junioren Jongens', 'Junioren Jongens'),
                               (2023, 'Junioren Jongens', 'Jongvolwassen Heren'),
                               (2024, 'Jongvolwassen Heren', 'Jongvolwassen Heren'),
                               (2025, 'Jongvolwassen Heren', 'Jongvolwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 20, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Jongvolwassen Heren', 'Jongvolwassen Heren'),
                               (2022, 'Jongvolwassen Heren', 'Jongvolwassen Heren'),
                               (2023, 'Jongvolwassen Heren', 'Volwassen Heren'),
                               (2024, 'Volwassen Heren', 'Volwassen Heren'),
                               (2025, 'Volwassen Heren', 'Volwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 30, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Volwassen Heren', 'Volwassen Heren'),
                               (2022, 'Volwassen Heren', 'Volwassen Heren'),
                               (2023, 'Volwassen Heren', 'Volwassen Heren'),
                               (2024, 'Volwassen Heren', 'Volwassen Heren'),
                               (2025, 'Volwassen Heren', 'Volwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 50, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Volwassen Heren', 'Volwassen Heren'),
                               (2022, 'Volwassen Heren', 'Volwassen Heren'),
                               (2023, 'Volwassen Heren', 'Volwassen Heren'),
                               (2024, 'Volwassen Heren', 'Volwassen Heren'),
                               (2025, 'Volwassen Heren', 'Volwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 55, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Volwassen Heren', 'Volwassen Heren'),
                               (2022, 'Volwassen Heren', 'Veteranen Heren (55+)'),
                               (2023, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (2024, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (2025, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 60, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (2022, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (2023, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (2024, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (2025, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 65, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(2021, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (2022, 'Veteranen Heren (55+)', 'Senioren Heren (65+)'),
                               (2023, 'Senioren Heren (65+)', 'Senioren Heren (65+)'),
                               (2024, 'Senioren Heren (65+)', 'Senioren Heren (65+)'),
                               (2025, 'Senioren Heren (65+)', 'Senioren Heren (65+)')])

    def test_leeftijdsklasse_ifaa(self):
        # <13 = Welp
        beschrijving = bereken_leeftijdsklasse_ifaa(9, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Welpen Jongens')

        # 13-16 = Junior
        beschrijving = bereken_leeftijdsklasse_ifaa(13, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Junioren Jongens')

        beschrijving = bereken_leeftijdsklasse_ifaa(16, GESLACHT_VROUW)
        self.assertEqual(beschrijving, 'Junioren Meisjes')

        # 17-20 = Jongvolwassen
        beschrijving = bereken_leeftijdsklasse_ifaa(20, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Jongvolwassen Heren')

        # 21-54 = Volwassen
        beschrijving = bereken_leeftijdsklasse_ifaa(30, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Volwassen Heren')

        beschrijving = bereken_leeftijdsklasse_ifaa(50, GESLACHT_VROUW)
        self.assertEqual(beschrijving, 'Volwassen Dames')

        # 55-64 = Veteranen
        beschrijving = bereken_leeftijdsklasse_ifaa(55, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Veteranen Heren (55+)')

        beschrijving = bereken_leeftijdsklasse_ifaa(60, GESLACHT_VROUW)
        self.assertEqual(beschrijving, 'Veteranen Dames (55+)')

        # 65+ = Senioren
        beschrijving = bereken_leeftijdsklasse_ifaa(65, GESLACHT_MAN)
        self.assertEqual(beschrijving, 'Senioren Heren (65+)')

        # niet compatibel
        beschrijving = bereken_leeftijdsklasse_ifaa(50, GESLACHT_ANDERS)
        self.assertEqual(beschrijving, '?')

    def test_leeftijdsklassen_bondscompetities(self):
        # Onder 12
        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 9, GESLACHT_MAN, 2022, 7)
        self.assertEqual(tup,
                         (9,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 14 Jongens'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 10, GESLACHT_VROUW, 2022, 1)
        self.assertEqual(tup,
                         (9,
                          [{'seizoen': '2020/2021', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2021/2022', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 14 Meisjes'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 9, GESLACHT_ANDERS, 2022, 7)
        self.assertEqual(tup,
                         (9,
                          [{'seizoen': '2021/2022', 'tekst':'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 14 Jongens'}]))

        # Onder 14
        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 12, GESLACHT_MAN, 2022, 8)
        self.assertEqual(tup,
                         (12,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 18'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 18'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 12, GESLACHT_VROUW, 2022, 9)
        self.assertEqual(tup,
                         (12,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 14 Meisjes'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 14 Meisjes'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 18'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 18'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 12, GESLACHT_ANDERS, 2022, 1)
        self.assertEqual(tup,
                         (11,
                          [{'seizoen': '2020/2021', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2021/2022', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 18'}]))

        # 21+
        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 21, GESLACHT_MAN, 2022, 7)
        self.assertEqual(tup,
                         (21,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 21'},
                           {'seizoen': '2022/2023', 'tekst': 'Uniseks'},
                           {'seizoen': '2023/2024', 'tekst': 'Uniseks'},
                           {'seizoen': '2024/2025', 'tekst': 'Uniseks'},
                           {'seizoen': '2025/2026', 'tekst': 'Uniseks'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 50, GESLACHT_VROUW, 2022, 5)
        self.assertEqual(tup,
                         (49,
                          [{'seizoen': '2020/2021', 'tekst': 'Uniseks'},
                           {'seizoen': '2021/2022', 'tekst': 'Uniseks'},
                           {'seizoen': '2022/2023', 'tekst': 'Uniseks'},
                           {'seizoen': '2023/2024', 'tekst': 'Uniseks'},
                           {'seizoen': '2024/2025', 'tekst': 'Uniseks'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 100, GESLACHT_VROUW, 2022, 8)
        self.assertEqual(tup,
                         (100,
                          [{'seizoen': '2021/2022', 'tekst': 'Uniseks'},
                           {'seizoen': '2022/2023', 'tekst': 'Uniseks'},
                           {'seizoen': '2023/2024', 'tekst': 'Uniseks'},
                           {'seizoen': '2024/2025', 'tekst': 'Uniseks'},
                           {'seizoen': '2025/2026', 'tekst': 'Uniseks'}]))

    def test_persoonlijk(self):
        # zonder login
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assert403(resp)

        # inlog, geen NHB lid
        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assert403(resp)

        # sporter
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/jouw_leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        # met voorkeuren
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/jouw_leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        # met geslacht X, geen keuze gemaakt
        self.sporter1.geslacht = GESLACHT_ANDERS
        self.sporter1.save(update_fields=['geslacht'])
        voorkeur = self.sporter1.sportervoorkeuren_set.all()[0]
        voorkeur.wedstrijd_geslacht_gekozen = False
        voorkeur.save(update_fields=['wedstrijd_geslacht_gekozen'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/jouw_leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_leeftijdsklassen)

        # redirect oud naar nieuw
        resp = self.client.get('/sporter/leeftijdsklassen/')
        self.assert_is_redirect(resp, '/sporter/leeftijden/persoonlijk/')

    def test_groepen(self):
        # anon
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsgroepen)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsgroepen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_leeftijdsgroepen)

        # manager
        self.account_normaal.is_BB = True
        self.account_normaal.save(update_fields=['is_BB'])
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        # sporter
        self.e2e_wisselnaarrol_sporter()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsgroepen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsgroepen.dtl', 'plein/site_layout.dtl'))


# end of file
