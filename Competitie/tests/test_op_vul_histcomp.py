# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamType
from Competitie.definities import DEEL_RK, DEEL_BK, DEELNAME_NEE
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               Regiocompetitie, RegiocompetitieRonde,
                               Kampioenschap,
                               RegiocompetitieSporterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               KampioenschapSporterBoog)
from Competitie.operations.vul_histcomp import (uitslag_regio_indiv_naar_histcomp, uitslag_regio_teams_naar_histcomp,
                                                uitslag_rk_indiv_naar_histcomp, uitslag_rk_teams_naar_histcomp,
                                                uitslag_bk_indiv_naar_histcomp, uitslag_bk_teams_naar_histcomp)
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Rayon
from HistComp.models import HistCompSeizoen
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestCompetitieOperationsVulHistComp(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, functies voor de HWL """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio_111 = Regio.objects.get(regio_nr=111)
        rayon_3 = Rayon.objects.get(rayon_nr=3)
        self.cluster = None

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio_111)
        ver.save()
        self.ver1 = ver

        # maak de functies aan
        func_rcl = maak_functie("RCL 111", "RCL")
        func_rcl.regio = regio_111
        func_rcl.save()

        func_rko = maak_functie("RKO 3", "RKO")
        func_rko.rayon = rayon_3
        func_rko.save()

        self.comp = Competitie(
                    beschrijving='test',
                    afstand="18",
                    begin_jaar=2019)
        self.comp.save()

        boog_c = BoogType.objects.get(afkorting='C')
        self.comp.boogtypen.add(boog_c)

        team_c = TeamType.objects.get(afkorting='C')
        self.comp.teamtypen.add(team_c)

        self.indiv_klasse1 = CompetitieIndivKlasse(
                                competitie=self.comp,
                                beschrijving='Compound Klasse 1',
                                volgorde=1,
                                boogtype=boog_c,
                                min_ag=7.0,
                                is_ook_voor_rk_bk=True,
                                titel_bk='Bondskampioen')
        self.indiv_klasse1.save()

        self.indiv_klasse2 = CompetitieIndivKlasse(
                                competitie=self.comp,
                                beschrijving='Compound Klasse 2',
                                volgorde=1,
                                boogtype=boog_c,
                                min_ag=0,
                                is_ook_voor_rk_bk=True,
                                titel_bk='Nederlands Kampioen')
        self.indiv_klasse2.save()

        self.indiv_klasse3 = CompetitieIndivKlasse(
                                competitie=self.comp,
                                beschrijving='Compound Klasse 3',
                                volgorde=1,
                                boogtype=boog_c,
                                min_ag=0,
                                is_ook_voor_rk_bk=True,
                                titel_bk='Lantaarn')     # niet ondersteund
        self.indiv_klasse3.save()

        self.team_klasse1 = CompetitieTeamKlasse(
                                    competitie=self.comp,
                                    volgorde=1,
                                    beschrijving='Compound ERE',
                                    team_type=team_c,
                                    team_afkorting=team_c.afkorting,
                                    min_ag=0.1,
                                    is_voor_teams_rk_bk=True)
        self.team_klasse1.save()
        self.team_klasse1.boog_typen.add(boog_c)

        self.deelcomp = Regiocompetitie(
                            competitie=self.comp,
                            regio=regio_111,
                            functie=func_rcl)
        self.deelcomp.save()

        self.ronde = RegiocompetitieRonde(
                            regiocompetitie=self.deelcomp,
                            cluster=self.cluster,
                            week_nr=1,
                            beschrijving='test ronde 1')
        self.ronde.save()

        self.regio_team1 = RegiocompetitieTeam(
                                regiocompetitie=self.deelcomp,
                                vereniging=self.ver1,
                                volg_nr=1,
                                team_type=team_c,
                                team_naam="Eerste",
                                team_klasse=self.team_klasse1)
        self.regio_team1.save()

        self.regio_team2 = RegiocompetitieTeam(
                                regiocompetitie=self.deelcomp,
                                vereniging=self.ver1,
                                volg_nr=2,
                                team_type=team_c,
                                team_naam="Tweede",
                                team_klasse=self.team_klasse1)
        self.regio_team2.save()

        self.regio_team3 = RegiocompetitieTeam(
                                regiocompetitie=self.deelcomp,
                                vereniging=self.ver1,
                                volg_nr=3,
                                team_type=team_c,
                                team_naam="Derde",
                                team_klasse=self.team_klasse1)
        self.regio_team3.save()

        self.kamp_rk = Kampioenschap(
                            deel=DEEL_RK,
                            competitie=self.comp,
                            rayon=rayon_3,
                            functie=func_rko)
        self.kamp_rk.save()

        self.kamp_bk = Kampioenschap(
                            deel=DEEL_BK,
                            competitie=self.comp,
                            functie=func_rko)
        self.kamp_bk.save()

        self.sporter = Sporter(
                            lid_nr=100001,
                            geslacht="M",
                            voornaam="Ramon",
                            achternaam="de Tester",
                            email="rdetester@gmail.not",
                            geboorte_datum=datetime.date(year=1972, month=3, day=4),
                            sinds_datum=datetime.date(year=2010, month=11, day=12),
                            bij_vereniging=ver)
        self.sporter.save()

        self.sporterboog = SporterBoog(
                                sporter=self.sporter,
                                boogtype=boog_c,
                                voor_wedstrijd=True)
        self.sporterboog.save()

    def test_regio_indiv(self):
        uitslag_regio_indiv_naar_histcomp(self.comp)

        # verwijdert vorige uitslag
        uitslag_regio_indiv_naar_histcomp(self.comp)

        deelnemer = RegiocompetitieSporterBoog(
                        regiocompetitie=self.deelcomp,
                        sporterboog=self.sporterboog,
                        bij_vereniging=self.sporter.bij_vereniging,
                        indiv_klasse=self.indiv_klasse1,
                        score1=110,
                        score2=120,
                        score3=130,
                        score4=140,
                        score5=150,
                        score6=160,
                        score7=0,
                        totaal=750,
                        aantal_scores=6,            # moet >= 6 zijn
                        laagste_score_nr=0,
                        gemiddelde=6.0)
        deelnemer.save()

        deelnemer = RegiocompetitieSporterBoog(
                        regiocompetitie=self.deelcomp,
                        sporterboog=self.sporterboog,
                        bij_vereniging=self.sporter.bij_vereniging,
                        indiv_klasse=self.indiv_klasse1,
                        score1=110,
                        score2=120,
                        score3=130,
                        score4=140,
                        score5=150,
                        score6=160,
                        score7=0,
                        totaal=deelnemer.totaal,    # moet gelijk zijn aan vorige deelnemer
                        aantal_scores=6,            # moet >= 6 zijn
                        laagste_score_nr=0,
                        gemiddelde=6.0)
        deelnemer.save()

        deelnemer = RegiocompetitieSporterBoog(
                        regiocompetitie=self.deelcomp,
                        sporterboog=self.sporterboog,
                        bij_vereniging=self.sporter.bij_vereniging,
                        indiv_klasse=self.indiv_klasse2,
                        score1=110,
                        score2=120,
                        score3=130,
                        score4=140,
                        score5=150,
                        score6=0,
                        score7=0,
                        totaal=650,
                        aantal_scores=5,            # moet < 6 zijn
                        laagste_score_nr=0,
                        gemiddelde=5.0)
        deelnemer.save()

        deelnemer = RegiocompetitieSporterBoog(
                        regiocompetitie=self.deelcomp,
                        sporterboog=self.sporterboog,
                        bij_vereniging=self.sporter.bij_vereniging,
                        indiv_klasse=self.indiv_klasse2,
                        score1=110,
                        score2=120,
                        score3=130,
                        score4=140,
                        score5=150,
                        score6=0,
                        score7=0,
                        totaal=deelnemer.totaal,    # moet gelijk zijn aan vorige deelnemer
                        aantal_scores=5,            # moet < 6 zijn
                        laagste_score_nr=0,
                        gemiddelde=5.0)
        deelnemer.save()

        # repeat voor 25m1p
        self.comp.afstand = "25"
        self.comp.save(update_fields=['afstand'])
        uitslag_regio_indiv_naar_histcomp(self.comp)

    def test_rk_indiv(self):
        uitslag_rk_indiv_naar_histcomp(self.comp)       # geen seizoen
        uitslag_regio_indiv_naar_histcomp(self.comp)    # maakt het HistCompSeizoen aan

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_rk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse1,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_score_1=100,
                        result_score_2=200,
                        result_counts="5x10",
                        result_rank=0)      # 0 = niet meegedaan
        deelnemer.save()

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_rk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse1,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_score_1=100,
                        result_score_2=200,
                        result_counts="5x10",
                        result_rank=1)
        deelnemer.save()

        # schiet alleen in team
        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_rk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse1,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_rank=77,
                        deelname=DEELNAME_NEE)
        deelnemer.save()

        uitslag_rk_indiv_naar_histcomp(self.comp)

        hist_seizoen = HistCompSeizoen.objects.first()
        self.assertTrue(hist_seizoen.heeft_uitslag_rk_indiv)

    def test_bk_indiv(self):
        uitslag_bk_indiv_naar_histcomp(self.comp)       # geen seizoen
        uitslag_regio_indiv_naar_histcomp(self.comp)    # maakt het HistCompSeizoen aan

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_bk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse1,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_score_1=100,
                        result_score_2=200,
                        result_counts="5x10",
                        result_rank=0)      # 0 = niet meegedaan
        deelnemer.save()

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_bk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse1,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_score_1=100,
                        result_score_2=200,
                        result_counts="5x10",
                        result_rank=1)
        deelnemer.save()

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_bk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse2,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_score_1=100,
                        result_score_2=200,
                        result_counts="5x10",
                        result_rank=1)
        deelnemer.save()

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_bk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse3,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_score_1=100,
                        result_score_2=200,
                        result_counts="5x10",
                        result_rank=1)
        deelnemer.save()

        deelnemer = KampioenschapSporterBoog(
                        kampioenschap=self.kamp_bk,
                        sporterboog=self.sporterboog,
                        indiv_klasse=self.indiv_klasse2,
                        bij_vereniging=self.sporter.bij_vereniging,
                        result_score_1=100,
                        result_score_2=200,
                        result_counts="5x10",
                        result_rank=2)
        deelnemer.save()

        uitslag_bk_indiv_naar_histcomp(self.comp)

        hist_seizoen = HistCompSeizoen.objects.first()
        self.assertTrue(hist_seizoen.heeft_uitslag_bk_indiv)

    def test_regio_teams(self):
        uitslag_regio_teams_naar_histcomp(self.comp)    # geen seizoen
        uitslag_regio_indiv_naar_histcomp(self.comp)    # maakt het HistCompSeizoen aan

        # voor extra coverage
        team = RegiocompetitieRondeTeam(
                        team=self.regio_team1,
                        ronde_nr=0,             # rare ronde
                        team_score=0,           # geen score --> komt niet in uitslag
                        team_punten=0)
        team.save()

        for lp in range(7):
            team = RegiocompetitieRondeTeam(
                            team=self.regio_team2,
                            ronde_nr=1 + lp,
                            team_score=200,
                            team_punten=2)
            team.save()
        # for

        # voor extra coverage
        team = RegiocompetitieRondeTeam(
                        team=self.regio_team3,
                        ronde_nr=1,
                        team_score=0,           # geen score --> komt niet in uitslag
                        team_punten=0)
        team.save()

        uitslag_regio_teams_naar_histcomp(self.comp)

        hist_seizoen = HistCompSeizoen.objects.first()
        self.assertTrue(hist_seizoen.heeft_uitslag_regio_teams)

        # herhaal voor 25m1p zonder het derde team
        team.delete()
        self.comp.afstand = "25"
        self.comp.save(update_fields=['afstand'])

        uitslag_regio_indiv_naar_histcomp(self.comp)    # maakt het HistCompSeizoen aan
        uitslag_regio_teams_naar_histcomp(self.comp)

        # cornercase: helemaal geen teams
        RegiocompetitieRondeTeam.objects.all().delete()
        uitslag_regio_teams_naar_histcomp(self.comp)

    def test_rk_test(self):
        uitslag_rk_teams_naar_histcomp(self.comp)       # geen seizoen
        uitslag_regio_indiv_naar_histcomp(self.comp)    # maakt het HistCompSeizoen aan

        uitslag_rk_teams_naar_histcomp(self.comp)

        hist_seizoen = HistCompSeizoen.objects.first()
        self.assertTrue(hist_seizoen.heeft_uitslag_rk_teams)

    def test_bk_teams(self):
        uitslag_bk_teams_naar_histcomp(self.comp)       # geen seizoen
        uitslag_regio_indiv_naar_histcomp(self.comp)    # maakt het HistCompSeizoen aan

        uitslag_bk_teams_naar_histcomp(self.comp)

        hist_seizoen = HistCompSeizoen.objects.first()
        self.assertTrue(hist_seizoen.heeft_uitslag_bk_teams)

# end of file
