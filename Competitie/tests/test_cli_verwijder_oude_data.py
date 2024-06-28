# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, CompetitieMatch, Kampioenschap
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Score.definities import SCORE_TYPE_GEEN
from Score.models import Score, ScoreHist
from Sporter.models import SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers


class TestCompetitieCliRegiocompVerwijderOudeData(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command verwijder_oude_data """

    def setUp(self):
        """ initialisatie van de test case """
        maak_competities_en_zet_fase_c()

    def test_basis(self):
        f1, f2 = self.run_management_command('verwijder_oude_data')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Searching' in f2.getvalue())
        self.assertTrue('Geen verwijderbare data gevonden' in f2.getvalue())

        # maak wat verwijderbare data aan
        boog_tr = BoogType.objects.get(afkorting='TR')
        sb = SporterBoog(
                sporter=None,
                boogtype=boog_tr)
        sb.save()

        comp = Competitie.objects.first()
        CompetitieMatch(
            competitie=comp,
            datum_wanneer='2000-01-01',
            tijd_begin_wedstrijd='00:00').save()

        match = CompetitieMatch(
                        competitie=comp,
                        datum_wanneer='2000-01-01',
                        tijd_begin_wedstrijd='00:00')
        match.save()
        deelkamp = Kampioenschap.objects.first()
        deelkamp.rk_bk_matches.add(match)

        Score(waarde=0, afstand_meter=18, type=SCORE_TYPE_GEEN).save()
        Score(waarde=123, afstand_meter=18).save()                      # geen sporterboog
        Score(waarde=123, afstand_meter=18, sporterboog=sb).save()      # 'dode' sporterboog

        # maak 501 scores aan
        bulk = list()
        for lp in range(501):
            hist = ScoreHist(
                        oude_waarde=0,
                        nieuwe_waarde=1,
                        notitie="Invoer uitslag wedstrijd\nDoor HWL ver 1000")
            bulk.append(hist)
        # for
        ScoreHist.objects.bulk_create(bulk)

        # alleen rapporteren
        f1, f2 = self.run_management_command('verwijder_oude_data')
        # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('Let op: gebruik --commit om de voorstellen echt te verwijderen' in f1.getvalue())
        self.assertTrue('Searching' in f2.getvalue())
        self.assertFalse('Geen verwijderbare data gevonden' in f2.getvalue())

        # nu echt verwijderen
        f1, f2 = self.run_management_command('verwijder_oude_data', '--commit')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Searching' in f2.getvalue())
        self.assertFalse('Geen verwijderbare data gevonden' in f2.getvalue())

        # nog een keer met een 'dode' sporterboog, maar geen scores om te verwijderen
        sb = SporterBoog(
                sporter=None,
                boogtype=boog_tr)
        sb.save()
        f1, f2 = self.run_management_command('verwijder_oude_data')
        # print("\nf1:\n%s\nf2:\n%s" % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('Searching' in f2.getvalue())
        self.assertFalse('Geen verwijderbare data gevonden' in f2.getvalue())

# end of file
