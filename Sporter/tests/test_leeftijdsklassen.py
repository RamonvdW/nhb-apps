# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import (GESLACHT_ANDERS, GESLACHT_MAN, GESLACHT_VROUW,
                                   ORGANISATIE_IFAA, ORGANISATIE_KHSN, ORGANISATIE_WA)
from Geo.models import Regio
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Registreer.models import GastRegistratie
from Sporter.leeftijdsklassen import (bereken_leeftijdsklassen_wa,
                                      bereken_leeftijdsklassen_khsn,
                                      bereken_leeftijdsklassen_ifaa,
                                      bereken_leeftijdsklassen_bondscompetitie,
                                      bereken_leeftijdsklasse_wa,
                                      bereken_leeftijdsklasse_khsn,
                                      bereken_leeftijdsklasse_ifaa)
from Sporter.models import Sporter
from Sporter.operations import get_sporter_voorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestSporterLeeftijdsklassen(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Leeftijdsklassen """

    url_leeftijdsklassen = '/sporter/leeftijden/persoonlijk/'
    url_leeftijdsgroepen = '/sporter/leeftijden/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geen_lid = self.e2e_create_account('geen_lid', 'geenlid@test.com', 'Geen')

        now = timezone.now()  # is in UTC
        now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
        self.huidige_jaar = now.year

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100001,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Tester",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_normaal,
                        email=self.account_normaal.email)
        sporter.save()
        self.sporter1 = sporter

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100002,
                        geslacht="V",
                        voornaam="Ramona",
                        achternaam="de Testerin",
                        email="",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver)
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

        # WA en KHSN hanteren kijken het hele jaar naar de leeftijd die je bereikt
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)

        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_KHSN)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_KHSN)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_KHSN)
        self.assertEqual(n, 50)

    def test_leeftijdsklassen_wa(self):
        # Onder 12
        tup = bereken_leeftijdsklassen_wa(2022 - 9, GESLACHT_MAN, 2022)
        self.assertEqual(tup,
                         (2022, 9,
                          'Onder 18 Heren',
                          ['Onder 18 Heren', 'Onder 18 Heren', 'Onder 18 Heren', 'Onder 18 Heren', 'Onder 18 Heren']))

        # Onder 18
        tup = bereken_leeftijdsklassen_wa(2022 - 17, GESLACHT_MAN, 2022)
        self.assertEqual(tup,
                         (2022, 17,
                          'Onder 18 Heren',
                          ['Onder 18 Heren', 'Onder 18 Heren', 'Onder 21 Heren', 'Onder 21 Heren', 'Onder 21 Heren']))

        # Onder 21
        tup = bereken_leeftijdsklassen_wa(2022 - 20, GESLACHT_MAN, 2022)
        self.assertEqual(tup,
                         (2022, 20,
                          'Onder 21 Heren',
                          ['Onder 21 Heren', 'Onder 21 Heren', 'Heren', 'Heren', 'Heren']))

        # 21+
        tup = bereken_leeftijdsklassen_wa(2022 - 21, GESLACHT_MAN, 2022)
        self.assertEqual(tup,
                         (2022, 21,
                          'Heren',
                          ['Onder 21 Heren', 'Heren', 'Heren', 'Heren', 'Heren']))

        tup = bereken_leeftijdsklassen_wa(2022 - 49, GESLACHT_MAN, 2022)
        self.assertEqual(tup,
                         (2022, 49,
                          'Heren',
                          ['Heren', 'Heren', '50+ Heren', '50+ Heren', '50+ Heren']))

        # 50+
        tup = bereken_leeftijdsklassen_wa(2022 - 50, GESLACHT_MAN, 2022)
        self.assertEqual(tup,
                         (2022, 50,
                          '50+ Heren',
                          ['Heren', '50+ Heren', '50+ Heren', '50+ Heren', '50+ Heren']))

        # 50+
        tup = bereken_leeftijdsklassen_wa(2022 - 100, GESLACHT_MAN, 2022)
        self.assertEqual(tup,
                         (2022, 100,
                          '50+ Heren',
                          ['50+ Heren', '50+ Heren', '50+ Heren', '50+ Heren', '50+ Heren']))

        # niet compatibel
        tup = bereken_leeftijdsklassen_wa(2022 - 50, GESLACHT_ANDERS, 2022)
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
        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 9, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 9,
                          'Onder 12 Gemengd of Onder 12 Jongens',
                          ['Onder 12 Gemengd of Onder 12 Jongens', 'Onder 12 Gemengd of Onder 12 Jongens',
                           'Onder 12 Gemengd of Onder 12 Jongens', 'Onder 12 Gemengd of Onder 12 Jongens',
                           'Onder 14 Gemengd of Onder 14 Jongens']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 9, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 9,
                          'Onder 12 Gemengd of Onder 12 Meisjes',
                          ['Onder 12 Gemengd of Onder 12 Meisjes', 'Onder 12 Gemengd of Onder 12 Meisjes',
                           'Onder 12 Gemengd of Onder 12 Meisjes', 'Onder 12 Gemengd of Onder 12 Meisjes',
                           'Onder 14 Gemengd of Onder 14 Meisjes']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 9, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 9,
                          'Onder 12 Gemengd',
                          ['Onder 12 Gemengd', 'Onder 12 Gemengd', 'Onder 12 Gemengd',
                           'Onder 12 Gemengd', 'Onder 14 Gemengd']))

        # Onder 14
        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 13, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 13,
                          'Onder 14 Gemengd of Onder 14 Jongens',
                          ['Onder 14 Gemengd of Onder 14 Jongens', 'Onder 14 Gemengd of Onder 14 Jongens',
                           'Onder 18 Gemengd of Onder 18 Heren', 'Onder 18 Gemengd of Onder 18 Heren',
                           'Onder 18 Gemengd of Onder 18 Heren']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 13, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 13,
                          'Onder 14 Gemengd of Onder 14 Meisjes',
                          ['Onder 14 Gemengd of Onder 14 Meisjes', 'Onder 14 Gemengd of Onder 14 Meisjes',
                           'Onder 18 Gemengd of Onder 18 Dames', 'Onder 18 Gemengd of Onder 18 Dames',
                           'Onder 18 Gemengd of Onder 18 Dames']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 13, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 13,
                          'Onder 14 Gemengd',
                          ['Onder 14 Gemengd', 'Onder 14 Gemengd', 'Onder 18 Gemengd',
                           'Onder 18 Gemengd', 'Onder 18 Gemengd']))

        # 21+
        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 21, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 21,
                          'Gemengd of Heren',
                          ['Onder 21 Gemengd of Onder 21 Heren', 'Gemengd of Heren', 'Gemengd of Heren',
                           'Gemengd of Heren', 'Gemengd of Heren']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 21, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 21,
                          'Gemengd of Dames',
                          ['Onder 21 Gemengd of Onder 21 Dames', 'Gemengd of Dames', 'Gemengd of Dames',
                           'Gemengd of Dames', 'Gemengd of Dames']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 21, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 21,
                          'Gemengd',
                          ['Onder 21 Gemengd', 'Gemengd', 'Gemengd', 'Gemengd', 'Gemengd']))

        # 50+
        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 50, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 50,
                          '50+ Gemengd of 50+ Heren',
                          ['Gemengd of Heren', '50+ Gemengd of 50+ Heren', '50+ Gemengd of 50+ Heren',
                           '50+ Gemengd of 50+ Heren', '50+ Gemengd of 50+ Heren']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 50, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 50,
                          '50+ Gemengd of 50+ Dames',
                          ['Gemengd of Dames', '50+ Gemengd of 50+ Dames', '50+ Gemengd of 50+ Dames',
                           '50+ Gemengd of 50+ Dames', '50+ Gemengd of 50+ Dames']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 50, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 50,
                          '50+ Gemengd',
                          ['Gemengd', '50+ Gemengd', '50+ Gemengd', '50+ Gemengd', '50+ Gemengd']))

        # 60+
        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 60, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 60,
                          '60+ Gemengd of 60+ Heren',
                          ['50+ Gemengd of 50+ Heren', '60+ Gemengd of 60+ Heren', '60+ Gemengd of 60+ Heren',
                           '60+ Gemengd of 60+ Heren', '60+ Gemengd of 60+ Heren']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 60, GESLACHT_VROUW, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 60,
                          '60+ Gemengd of 60+ Dames',
                          ['50+ Gemengd of 50+ Dames', '60+ Gemengd of 60+ Dames', '60+ Gemengd of 60+ Dames',
                           '60+ Gemengd of 60+ Dames', '60+ Gemengd of 60+ Dames']))

        tup = bereken_leeftijdsklassen_khsn(self.huidige_jaar - 60, GESLACHT_ANDERS, self.huidige_jaar)
        self.assertEqual(tup,
                         (self.huidige_jaar, 60,
                          '60+ Gemengd',
                          ['50+ Gemengd', '60+ Gemengd', '60+ Gemengd', '60+ Gemengd', '60+ Gemengd']))

    def test_leeftijdsklasse_nhb(self):
        # Onder 12
        tup = bereken_leeftijdsklasse_khsn(9, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 12 Jongens')

        tup = bereken_leeftijdsklasse_khsn(10, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 12 Meisjes')

        tup = bereken_leeftijdsklasse_khsn(11, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 12 Gemengd')

        # Onder 14
        tup = bereken_leeftijdsklasse_khsn(12, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 14 Jongens')

        tup = bereken_leeftijdsklasse_khsn(13, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 14 Meisjes')

        tup = bereken_leeftijdsklasse_khsn(13, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 14 Gemengd')

        # Onder 18
        tup = bereken_leeftijdsklasse_khsn(14, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 18 Heren')

        tup = bereken_leeftijdsklasse_khsn(15, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 18 Dames')

        tup = bereken_leeftijdsklasse_khsn(17, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 18 Gemengd')

        # Onder 21
        tup = bereken_leeftijdsklasse_khsn(18, GESLACHT_MAN)
        self.assertEqual(tup, 'Onder 21 Heren')

        tup = bereken_leeftijdsklasse_khsn(19, GESLACHT_VROUW)
        self.assertEqual(tup, 'Onder 21 Dames')

        tup = bereken_leeftijdsklasse_khsn(20, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Onder 21 Gemengd')

        # 21+
        tup = bereken_leeftijdsklasse_khsn(21, GESLACHT_MAN)
        self.assertEqual(tup, 'Heren')

        tup = bereken_leeftijdsklasse_khsn(30, GESLACHT_VROUW)
        self.assertEqual(tup, 'Dames')

        tup = bereken_leeftijdsklasse_khsn(40, GESLACHT_ANDERS)
        self.assertEqual(tup, 'Gemengd')

        # 50+
        tup = bereken_leeftijdsklasse_khsn(50, GESLACHT_MAN)
        self.assertEqual(tup, '50+ Heren')

        tup = bereken_leeftijdsklasse_khsn(50, GESLACHT_VROUW)
        self.assertEqual(tup, '50+ Dames')

        tup = bereken_leeftijdsklasse_khsn(50, GESLACHT_ANDERS)
        self.assertEqual(tup, '50+ Gemengd')

        # 60+
        tup = bereken_leeftijdsklasse_khsn(60, GESLACHT_MAN)
        self.assertEqual(tup, '60+ Heren')

        tup = bereken_leeftijdsklasse_khsn(60, GESLACHT_VROUW)
        self.assertEqual(tup, '60+ Dames')

        tup = bereken_leeftijdsklasse_khsn(60, GESLACHT_ANDERS)
        self.assertEqual(tup, '60+ Gemengd')

    def test_leeftijdsklassen_ifaa(self):
        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 9, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Welpen Jongens', 'Welpen Jongens'),
                               (self.huidige_jaar + 0, 'Welpen Jongens', 'Welpen Jongens'),
                               (self.huidige_jaar + 1, 'Welpen Jongens', 'Welpen Jongens'),
                               (self.huidige_jaar + 2, 'Welpen Jongens', 'Welpen Jongens'),
                               (self.huidige_jaar + 3, 'Welpen Jongens', 'Welpen Jongens')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 13, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Welpen Jongens', 'Welpen Jongens'),
                               (self.huidige_jaar + 0, 'Welpen Jongens', 'Junioren Jongens'),
                               (self.huidige_jaar + 1, 'Junioren Jongens', 'Junioren Jongens'),
                               (self.huidige_jaar + 2, 'Junioren Jongens', 'Junioren Jongens'),
                               (self.huidige_jaar + 3, 'Junioren Jongens', 'Junioren Jongens')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 16, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Junioren Jongens', 'Junioren Jongens'),
                               (self.huidige_jaar + 0, 'Junioren Jongens', 'Junioren Jongens'),
                               (self.huidige_jaar + 1, 'Junioren Jongens', 'Jongvolwassen Heren'),
                               (self.huidige_jaar + 2, 'Jongvolwassen Heren', 'Jongvolwassen Heren'),
                               (self.huidige_jaar + 3, 'Jongvolwassen Heren', 'Jongvolwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 20, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Jongvolwassen Heren', 'Jongvolwassen Heren'),
                               (self.huidige_jaar + 0, 'Jongvolwassen Heren', 'Jongvolwassen Heren'),
                               (self.huidige_jaar + 1, 'Jongvolwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 2, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 3, 'Volwassen Heren', 'Volwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 30, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 0, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 1, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 2, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 3, 'Volwassen Heren', 'Volwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 50, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 0, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 1, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 2, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 3, 'Volwassen Heren', 'Volwassen Heren')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 55, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Volwassen Heren', 'Volwassen Heren'),
                               (self.huidige_jaar + 0, 'Volwassen Heren', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 1, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 2, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 3, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 60, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 0, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 1, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 2, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 3, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)')])

        tup = bereken_leeftijdsklassen_ifaa(self.huidige_jaar - 65, GESLACHT_MAN, self.huidige_jaar)
        self.assertEqual(tup, [(self.huidige_jaar - 1, 'Veteranen Heren (55+)', 'Veteranen Heren (55+)'),
                               (self.huidige_jaar + 0, 'Veteranen Heren (55+)', 'Senioren Heren (65+)'),
                               (self.huidige_jaar + 1, 'Senioren Heren (65+)', 'Senioren Heren (65+)'),
                               (self.huidige_jaar + 2, 'Senioren Heren (65+)', 'Senioren Heren (65+)'),
                               (self.huidige_jaar + 3, 'Senioren Heren (65+)', 'Senioren Heren (65+)')])

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
        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 8, GESLACHT_MAN, 2022, 7)     # maand 7 = nieuwe seizoen
        self.assertEqual(tup,
                         (9,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 14 Jongens'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 9, GESLACHT_VROUW, 2022, 1)   # maand 1 = vorige seizoen
        self.assertEqual(tup,
                         (9,
                          [{'seizoen': '2020/2021', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2021/2022', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 14 Meisjes'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 8, GESLACHT_ANDERS, 2022, 7)
        self.assertEqual(tup,
                         (9,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 14 Jongens'}]))

        # Onder 14
        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 11, GESLACHT_MAN, 2022, 8)
        self.assertEqual(tup,
                         (12,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 18'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 18'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 11, GESLACHT_VROUW, 2022, 9)
        self.assertEqual(tup,
                         (12,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 12 Meisjes'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 14 Meisjes'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 14 Meisjes'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 18'},
                           {'seizoen': '2025/2026', 'tekst': 'Onder 18'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 11, GESLACHT_ANDERS, 2022, 1)  # maand 1 = vorige seizoen
        self.assertEqual(tup,
                         (11,
                          [{'seizoen': '2020/2021', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2021/2022', 'tekst': 'Onder 12 Jongens'},
                           {'seizoen': '2022/2023', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2023/2024', 'tekst': 'Onder 14 Jongens'},
                           {'seizoen': '2024/2025', 'tekst': 'Onder 18'}]))

        # 21+
        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 20, GESLACHT_MAN, 2022, 7)
        self.assertEqual(tup,
                         (21,
                          [{'seizoen': '2021/2022', 'tekst': 'Onder 21'},
                           {'seizoen': '2022/2023', 'tekst': 'Gemengd'},
                           {'seizoen': '2023/2024', 'tekst': 'Gemengd'},
                           {'seizoen': '2024/2025', 'tekst': 'Gemengd'},
                           {'seizoen': '2025/2026', 'tekst': 'Gemengd'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 49, GESLACHT_VROUW, 2022, 5)
        self.assertEqual(tup,
                         (49,
                          [{'seizoen': '2020/2021', 'tekst': 'Gemengd'},
                           {'seizoen': '2021/2022', 'tekst': 'Gemengd'},
                           {'seizoen': '2022/2023', 'tekst': 'Gemengd'},
                           {'seizoen': '2023/2024', 'tekst': 'Gemengd'},
                           {'seizoen': '2024/2025', 'tekst': 'Gemengd'}]))

        tup = bereken_leeftijdsklassen_bondscompetitie(2022 - 99, GESLACHT_VROUW, 2022, 8)
        self.assertEqual(tup,
                         (100,
                          [{'seizoen': '2021/2022', 'tekst': 'Gemengd'},
                           {'seizoen': '2022/2023', 'tekst': 'Gemengd'},
                           {'seizoen': '2023/2024', 'tekst': 'Gemengd'},
                           {'seizoen': '2024/2025', 'tekst': 'Gemengd'},
                           {'seizoen': '2025/2026', 'tekst': 'Gemengd'}]))

    def test_persoonlijk(self):
        # zonder login
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assert_is_redirect_login(resp, self.url_leeftijdsklassen)

        # inlog, geen lid
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

        get_sporter_voorkeuren(self.sporter1, mag_database_wijzigen=True)

        # met voorkeuren
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/jouw_leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        # met geslacht X, geen keuze gemaakt
        self.sporter1.geslacht = GESLACHT_ANDERS
        self.sporter1.save(update_fields=['geslacht'])
        voorkeur = self.sporter1.sportervoorkeuren_set.first()
        voorkeur.wedstrijd_geslacht_gekozen = False
        voorkeur.save(update_fields=['wedstrijd_geslacht_gekozen'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/jouw_leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_leeftijdsklassen)

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

    def test_gast(self):
        self.e2e_login(self.account_normaal)

        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        self.sporter1.is_gast = True
        self.sporter1.save(update_fields=['is_gast'])

        gast = GastRegistratie(
                    email='',
                    account=self.account_normaal,
                    sporter=self.sporter1,
                    fase=REGISTRATIE_FASE_COMPLEET,
                    voornaam='',
                    achternaam='')
        gast.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/jouw_leeftijdsklassen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je moet lid zijn bij de KHSN om deel te nemen aan de bondscompetities')


# end of file
