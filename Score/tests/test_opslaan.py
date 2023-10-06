# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Sporter.models import Sporter, SporterBoog
from Score.models import Score, ScoreHist, Aanvangsgemiddelde, AanvangsgemiddeldeHist
from Score.operations import score_indiv_ag_opslaan, score_teams_ag_opslaan, wanneer_ag_vastgesteld
from TestHelpers.e2ehelpers import E2EHelpers
from decimal import Decimal
import datetime


class TestScoreOpslaan(E2EHelpers, TestCase):

    """ tests voor de Score applicatie, functie Opslaan """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12))
        sporter.save()

        # maak een sporterboog aan
        self.sporterboog = SporterBoog(
                                boogtype=BoogType.objects.get(afkorting='R'),
                                sporter=sporter)
        self.sporterboog.save()

    def test_opslaan(self):
        self.assertEqual(Score.objects.count(), 0)
        self.assertEqual(ScoreHist.objects.count(), 0)

        afstand = 18
        gemiddelde = Decimal('9.876')
        account = self.account_normaal
        notitie = "Dit is een notities"

        # de eerste keer wordt het Score object aangemaakt
        res = score_indiv_ag_opslaan(self.sporterboog, afstand, gemiddelde, account, notitie)
        self.assertEqual(res, True)

        self.assertEqual(Aanvangsgemiddelde.objects.count(), 1)
        ag = Aanvangsgemiddelde.objects.first()
        self.assertEqual(ag.afstand_meter, afstand)
        self.assertEqual(ag.waarde, gemiddelde)
        self.assertEqual(ag.sporterboog, self.sporterboog)
        self.assertTrue(str(ag) != "")

        self.assertEqual(AanvangsgemiddeldeHist.objects.count(), 1)
        ag_hist = AanvangsgemiddeldeHist.objects.first()
        self.assertEqual(ag_hist.oude_waarde, 0)
        self.assertEqual(ag_hist.nieuwe_waarde, gemiddelde)
        self.assertEqual(ag_hist.door_account, account)
        self.assertEqual(ag_hist.notitie, notitie)
        self.assertTrue(str(ag_hist) != "")

        # dezelfde score nog een keer opslaan leidt tot een reject
        res = score_indiv_ag_opslaan(self.sporterboog, afstand, gemiddelde, account, notitie)
        self.assertEqual(res, False)

        # tweede keer wordt er alleen een ScoreHist object aangemaakt
        gemiddelde2 = Decimal('8.765')
        notitie2 = "Dit is de tweede notitie"

        res = score_indiv_ag_opslaan(self.sporterboog, afstand, gemiddelde2, account, notitie2)
        self.assertEqual(res, True)

        self.assertEqual(Aanvangsgemiddelde.objects.count(), 1)
        ag = Aanvangsgemiddelde.objects.first()
        self.assertEqual(ag.afstand_meter, afstand)
        self.assertEqual(ag.waarde, gemiddelde2)
        self.assertEqual(ag.sporterboog, self.sporterboog)

        self.assertEqual(AanvangsgemiddeldeHist.objects.count(), 2)
        ag_hist = AanvangsgemiddeldeHist.objects.exclude(pk=ag_hist.pk).first()
        self.assertEqual(ag_hist.oude_waarde, gemiddelde)
        self.assertEqual(ag_hist.nieuwe_waarde, gemiddelde2)
        self.assertEqual(ag_hist.door_account, account)
        self.assertEqual(ag_hist.notitie, notitie2)

        gemiddelde = Decimal('8.345')
        res = score_teams_ag_opslaan(self.sporterboog, afstand, gemiddelde, account, notitie)
        self.assertEqual(res, True)

        self.assertEqual(AanvangsgemiddeldeHist.objects.count(), 3)
        ag_hist = AanvangsgemiddeldeHist.objects.get(ag__waarde=gemiddelde)
        ag = ag_hist.ag
        self.assertTrue('(team)' in str(ag))

        ag_hist.door_account = None
        self.assertTrue('systeem' in str(ag_hist))

    def test_wanneer(self):
        res = wanneer_ag_vastgesteld(18)
        self.assertIsNone(res)

        score_indiv_ag_opslaan(self.sporterboog, 18, 9.123, None, "test")

        res = wanneer_ag_vastgesteld(18)
        self.assertIsNotNone(res)

# end of file
