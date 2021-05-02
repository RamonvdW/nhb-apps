# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Schutter.models import SchutterBoog
from NhbStructuur.models import NhbLid
from .models import (Score, ScoreHist, wanneer_ag_vastgesteld,
                     score_indiv_ag_opslaan, score_teams_ag_opslaan,
                     SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG, SCORE_TYPE_SCORE)
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestScoreOpslaan(E2EHelpers, TestCase):
    """ unit tests voor de Score applicatie, functie Opslaan """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.save()

        # maak een schutterboog aan
        schutterboog = self.schutterboog = SchutterBoog()
        schutterboog.boogtype = BoogType.objects.get(afkorting='R')
        schutterboog.nhblid = lid
        schutterboog.save()

    def test_opslaan(self):
        self.assertEqual(Score.objects.count(), 0)
        self.assertEqual(ScoreHist.objects.count(), 0)

        afstand = 18
        gemiddelde = 9.876
        waarde = int(gemiddelde * 1000)
        account = self.account_normaal
        notitie = "Dit is een notities"

        # de eerste keer wordt het Score object aangemaakt
        res = score_indiv_ag_opslaan(self.schutterboog, afstand, gemiddelde, account, notitie)
        self.assertEqual(res, True)

        self.assertEqual(Score.objects.count(), 1)
        score = Score.objects.all()[0]
        self.assertEqual(score.afstand_meter, afstand)
        self.assertEqual(score.waarde, waarde)
        self.assertEqual(score.schutterboog, self.schutterboog)
        self.assertTrue(str(score) != "")

        score.type = SCORE_TYPE_INDIV_AG
        self.assertTrue("(indiv AG)" in str(score))

        score.type = SCORE_TYPE_TEAM_AG
        self.assertTrue("(team AG)" in str(score))

        score.type = SCORE_TYPE_SCORE
        self.assertTrue(str(score) != "")

        self.assertEqual(ScoreHist.objects.count(), 1)
        scorehist = ScoreHist.objects.all()[0]
        self.assertEqual(scorehist.oude_waarde, 0)
        self.assertEqual(scorehist.nieuwe_waarde, waarde)
        self.assertEqual(scorehist.door_account, account)
        self.assertEqual(scorehist.notitie, notitie)
        self.assertTrue(str(scorehist) != "")

        # dezelfde score nog een keer opslaan resulteert in een reject
        res = score_indiv_ag_opslaan(self.schutterboog, afstand, gemiddelde, account, notitie)
        self.assertEqual(res, False)

        # tweede keer wordt er alleen een ScoreHist object aangemaakt
        gemiddelde2 = 8.765
        waarde2 = int(gemiddelde2 * 1000)
        notitie2 = "Dit is de tweede notitie"

        res = score_indiv_ag_opslaan(self.schutterboog, afstand, gemiddelde2, account, notitie2)
        self.assertEqual(res, True)

        self.assertEqual(Score.objects.count(), 1)
        score = Score.objects.all()[0]
        self.assertEqual(score.afstand_meter, afstand)
        self.assertEqual(score.waarde, waarde2)
        self.assertEqual(score.schutterboog, self.schutterboog)

        self.assertEqual(ScoreHist.objects.count(), 2)
        scorehist = ScoreHist.objects.exclude(pk=scorehist.pk).all()[0]
        self.assertEqual(scorehist.oude_waarde, waarde)
        self.assertEqual(scorehist.nieuwe_waarde, waarde2)
        self.assertEqual(scorehist.door_account, account)
        self.assertEqual(scorehist.notitie, notitie2)

        gemiddelde = 8.345
        res = score_teams_ag_opslaan(self.schutterboog, afstand, gemiddelde, account, notitie)
        self.assertEqual(res, True)

        self.assertEqual(ScoreHist.objects.count(), 3)
        scorehist = ScoreHist.objects.get(score__waarde=8345)
        score = scorehist.score
        self.assertTrue('(team AG)' in str(score))

    def test_wanneer(self):
        res = wanneer_ag_vastgesteld()
        self.assertIsNone(res)

        score_indiv_ag_opslaan(self.schutterboog, 18, 9.123, None, "test")

        res = wanneer_ag_vastgesteld()
        self.assertIsNotNone(res)

# end of file
