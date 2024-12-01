# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import TemplateCompetitieIndivKlasse, BoogType, TeamType, Leeftijdsklasse
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               Regiocompetitie, RegiocompetitieSporterBoog, RegiocompetitieTeam,
                               RegiocompetitieRondeTeam)
from Competitie.test_utils.tijdlijn import zet_competitie_fases, zet_competitie_fase_regio_inschrijven
from Functie.models import Functie
from Geo.models import Regio
from Score.definities import AG_DOEL_INDIV, SCORE_TYPE_SCORE, SCORE_TYPE_GEEN
from Score.models import Aanvangsgemiddelde, ScoreHist, Score
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestCompLaagRegioCli(E2EHelpers, TestCase):

    """ unittests voor de CompLaagRegio applicatie, management command check_klasse """

    def setUp(self):
        """ initialisatie van de test case """
        regio_111 = Regio.objects.get(pk=111)

        boog_r = BoogType.objects.get(afkorting='R')
        boog_bb = BoogType.objects.get(afkorting='BB')
        boog_tr = BoogType.objects.get(afkorting='TR')

        teamtype_r = TeamType.objects.get(afkorting='R2')

        comp = Competitie(
                    beschrijving='Test',
                    afstand='18',
                    begin_jaar=2000)
        comp.save()
        self.comp = Competitie.objects.get(pk=comp.pk)

        dummy_functie = Functie.objects.filter(rol='RCL', regio__regio_nr=111)[0]
        deelcomp = Regiocompetitie(
                            competitie=comp,
                            regio=regio_111,
                            functie=dummy_functie)
        deelcomp.save()

        indiv_r1 = TemplateCompetitieIndivKlasse.objects.filter(boogtype=boog_r)[1]
        indiv_r2 = TemplateCompetitieIndivKlasse.objects.filter(boogtype=boog_r)[2]
        indiv_tr = TemplateCompetitieIndivKlasse.objects.filter(boogtype=boog_tr)[0]
        indiv_bb = TemplateCompetitieIndivKlasse.objects.filter(boogtype=boog_bb)[0]

        lkl_sa = Leeftijdsklasse.objects.get(afkorting='SA')

        # TODO: leeftijdsklassen nodig?
        klasse_r1 = CompetitieIndivKlasse(
                        competitie=comp,
                        volgorde=indiv_r1.volgorde,
                        boogtype=indiv_r1.boogtype,
                        min_ag=2.0)
        klasse_r1.save()
        klasse_r1.leeftijdsklassen.add(lkl_sa)

        klasse_r2 = CompetitieIndivKlasse(
                        competitie=comp,
                        volgorde=indiv_r2.volgorde,
                        boogtype=indiv_r2.boogtype,
                        min_ag=1.0)
        klasse_r2.save()
        klasse_r2.leeftijdsklassen.add(lkl_sa)

        klasse_bb = CompetitieIndivKlasse(
                        competitie=comp,
                        volgorde=indiv_bb.volgorde,
                        boogtype=indiv_bb.boogtype,
                        min_ag=0.0)
        klasse_bb.save()
        klasse_bb.leeftijdsklassen.add(lkl_sa)

        klasse_tr = CompetitieIndivKlasse(
                        competitie=comp,
                        volgorde=indiv_tr.volgorde,
                        boogtype=indiv_tr.boogtype,
                        min_ag=0.0)
        klasse_tr.save()

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club met een naam langer dan 30 tekens",
                    ver_nr=1000,
                    regio=regio_111)
        ver.save()

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=123456,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=None,
                    email='')
        sporter.save()
        self.sporter = sporter

        sporterboog_r = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog_r.save()
        self.sporterboog_r = sporterboog_r

        sporterboog_tr = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_tr,
                            voor_wedstrijd=False)
        sporterboog_tr.save()
        self.sporterboog_tr = sporterboog_tr

        sporterboog_bb = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_bb,
                            voor_wedstrijd=False)
        sporterboog_bb.save()
        self.sporterboog_bb = sporterboog_bb

        deelnemer_r = RegiocompetitieSporterBoog(
                            regiocompetitie=deelcomp,
                            sporterboog=sporterboog_r,
                            bij_vereniging=ver,
                            indiv_klasse=klasse_r1,
                            aantal_scores=1)
        deelnemer_r.save()
        self.deelnemer_r = deelnemer_r

        deelnemer_tr = RegiocompetitieSporterBoog(
                            regiocompetitie=deelcomp,
                            sporterboog=sporterboog_tr,
                            bij_vereniging=ver,
                            indiv_klasse=klasse_tr,
                            aantal_scores=2)
        deelnemer_tr.save()
        self.deelnemer_tr = deelnemer_tr

        team_klasse_r = CompetitieTeamKlasse(
                            competitie=comp,
                            volgorde=42,
                            team_type=teamtype_r,
                            team_afkorting='R2',
                            min_ag=0.0)
        team_klasse_r.save()
        team_klasse_r.boog_typen.add(boog_r)

        team = RegiocompetitieTeam(
                            regiocompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=1,
                            team_type=teamtype_r,
                            team_klasse=team_klasse_r,
                            team_naam='Test')
        team.save()
        team.leden.add(deelnemer_tr)
        self.team1 = team

        team = RegiocompetitieTeam(
                            regiocompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=1,
                            team_type=teamtype_r,
                            team_klasse=team_klasse_r,
                            team_naam='Test 2')
        team.save()
        self.team2 = team

    def test_check_klasse(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('check_klasse')

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Let op: gebruik --commit' in f2.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('check_klasse', '--commit')

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(f2.getvalue() == '')

    def test_boogtype_check(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_check')

        # print("f1: %s" % f1.getvalue())
        self.assertTrue(f1.getvalue() == '')

        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[123456] Ramon' in f2.getvalue())
        self.assertTrue('TR -> R' in f2.getvalue())

        self.sporter.achternaam = "de Tester met speciale naam"
        #           [123456] Ramon de                    ^
        #           1234567890123456789012345678901234567890
        self.sporter.save()

        self.sporterboog_r.voor_wedstrijd = False
        self.sporterboog_r.save()

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_check')

        # print("f2: %s" % f2.getvalue())
        self.assertTrue('met speciale..' in f2.getvalue())
        self.assertTrue('TR -> ?' in f2.getvalue())

    def test_boogtype_transfer(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'X', '18')
        self.assertTrue('[ERROR] Onbekend boog type:' in f1.getvalue())

        # competitie is nog in fase A en heeft geen vastgestelde klassengrenzen
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'R', '18')
        self.assertTrue('[ERROR] Kan de competitie niet vinden' in f1.getvalue())

        zet_competitie_fase_regio_inschrijven(self.comp)
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '999999', 'R', '18')
        self.assertTrue('[ERROR] Sporter 999999 niet gevonden' in f1.getvalue())

        self.sporterboog_r.voor_wedstrijd = False
        self.sporterboog_r.save()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'BB', '18')
        self.assertTrue('[ERROR] Sporter heeft geen wedstrijd boog als voorkeur' in f1.getvalue())

        voorkeuren = SporterVoorkeuren(sporter=self.sporter)
        voorkeuren.wedstrijd_geslacht_gekozen = False
        voorkeuren.save()

        self.sporterboog_tr.voor_wedstrijd = True
        self.sporterboog_tr.save()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'TR', '18')
        self.assertTrue('[ERROR] Sporter is al ingeschreven met dat boog type' in f1.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'BB', '18')
        self.assertTrue('[ERROR] Sporter heeft boog BB niet als voorkeur. Wel: TR' in f1.getvalue())

        voorkeuren.wedstrijd_geslacht_gekozen = True
        voorkeuren.wedstrijd_geslacht = 'M'
        voorkeuren.save()

        # sporter is met R en TR ingeschreven
        self.sporterboog_bb.voor_wedstrijd = True
        self.sporterboog_bb.save()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'BB', '18')
        self.assertTrue('[ERROR] Sporter met meerdere inschrijvingen wordt niet ondersteund' in f1.getvalue())

        self.deelnemer_r.delete()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'BB', '18')
        self.assertTrue('[ERROR] Sporter is onderdeel van een team' in f1.getvalue())

        score = Score(
                    type=SCORE_TYPE_SCORE,
                    sporterboog=self.sporterboog_tr,        # TR = huidige inschrijving
                    waarde=42,
                    afstand_meter=42)
        score.save()
        hist = ScoreHist(
                    score=score,
                    oude_waarde=0,
                    nieuwe_waarde=42,
                    door_account=None,
                    notitie='Test')
        hist.save()

        score = Score(
                    type=SCORE_TYPE_GEEN,
                    sporterboog=self.sporterboog_tr,
                    waarde=0,
                    afstand_meter=42)
        score.save()
        hist = ScoreHist(
                    score=score,
                    oude_waarde=0,
                    nieuwe_waarde=0,
                    door_account=None,
                    notitie='Test geen')
        hist.save()

        score = Score(
                    type=SCORE_TYPE_SCORE,
                    sporterboog=self.sporterboog_tr,
                    waarde=0,
                    afstand_meter=42)
        score.save()
        hist = ScoreHist(
                    score=score,
                    oude_waarde=0,
                    nieuwe_waarde=0,
                    door_account=None,
                    notitie='Test dummy')
        hist.save()

        ag = Aanvangsgemiddelde(
                        doel=AG_DOEL_INDIV,
                        sporterboog=self.sporterboog_bb,
                        boogtype=self.sporterboog_bb.boogtype,
                        waarde="42.0",
                        afstand_meter=42)
        ag.save()

        self.team1.leden.clear()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '123456', 'BB', '18')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Gebruik --commit om' in f2.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('boogtype_transfer', '--commit', '123456', 'BB', '18')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(' is aangepast; scores zijn omgezet naar sporterboog ' in f2.getvalue())

    def test_regios_afsluiten(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('regios_afsluiten', '18', '101', '10x')

        self.assertTrue('[ERROR] Valide regio nummers: 101 tot 116' in f1.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('regios_afsluiten', '18', '116', '115')

        self.assertTrue('[ERROR] Valide regio nummers: 101 tot 116, oplopend' in f1.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('regios_afsluiten', '99', '115', '116')

        self.assertTrue('[ERROR] Kan competitie met afstand 99 niet vinden' in f1.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('regios_afsluiten', '18', '101', '102')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[ERROR] Competitie in fase_indiv A is niet ondersteund' in f1.getvalue())

        zet_competitie_fases(self.comp, 'G', 'G')

        # geen aangemaakte regios
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('regios_afsluiten', '18', '101', '102')

        self.assertTrue('' == f1.getvalue())
        self.assertTrue('' == f2.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('regios_afsluiten', '18', '111', '111')

        self.assertTrue('[INFO] Deelcompetitie Test - Regio 111 wordt afgesloten' in f2.getvalue())

        # nog een keer (terwijl al afgesloten)
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('regios_afsluiten', '18', '111', '111')

        self.assertTrue(f1.getvalue() == '')

    def test_fix_bad_ag(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('fix_bad_ag', '18')
        self.assertTrue('[ERROR] Competitie is in de verkeerde fase' in f1.getvalue())

        zet_competitie_fase_regio_inschrijven(self.comp)

        with self.assert_max_queries(20):
            self.run_management_command('fix_bad_ag', '18')

        Aanvangsgemiddelde(
                sporterboog=self.sporterboog_r,
                boogtype=self.sporterboog_r.boogtype,
                doel=AG_DOEL_INDIV,
                afstand_meter=18,
                waarde=8.000).save()

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('fix_bad_ag', '18')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Gebruik --commit om wijzigingen door te voeren' in f2.getvalue())

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('fix_bad_ag', '18', '--commit')

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')

        for comp in Competitie.objects.all():
            comp.is_afgesloten = True
            comp.save(update_fields=['is_afgesloten'])

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('fix_bad_ag', '18')

        self.assertTrue('[ERROR] Geen actieve competitie gevonden' in f1.getvalue())

    def test_check_wp_f1(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('check_wp_f1')

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')
        # zie test_poules voor nog een test van dit commando

    def test_ronde_teams_check(self):

        # maak de benodigde records aan
        RegiocompetitieRondeTeam(team=self.team1, ronde_nr=1).save()
        RegiocompetitieRondeTeam(team=self.team1, ronde_nr=2).save()

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('ronde_teams_check')
        self.assertEqual(f1.getvalue(), '')
        self.assertEqual(f2.getvalue().count('\n'), 2)

        RegiocompetitieRondeTeam(team=self.team2, ronde_nr=1).save()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('ronde_teams_check')
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue('regio 111 ronde counts' in f2.getvalue())

        self.assertTrue(f1.getvalue() == '')

    def test_verwijder_dupe_data(self):
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('verwijder_dupe_data')

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(f2.getvalue() == 'Geen duplicate data gevonden\n')

        # maak een echte dupe aan
        dupe = RegiocompetitieSporterBoog(
                    regiocompetitie=self.deelnemer_r.regiocompetitie,
                    sporterboog=self.deelnemer_r.sporterboog,
                    bij_vereniging=self.deelnemer_r.bij_vereniging,
                    indiv_klasse=self.deelnemer_r.indiv_klasse)
        dupe.save()

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('verwijder_dupe_data')

        self.assertTrue('Gebruik --commit om' in f1.getvalue())

        # maak nog een dupe aan, voor extra coverage
        dupe = RegiocompetitieSporterBoog(
                    regiocompetitie=self.deelnemer_r.regiocompetitie,
                    sporterboog=self.deelnemer_r.sporterboog,
                    bij_vereniging=self.deelnemer_r.bij_vereniging,
                    indiv_klasse=self.deelnemer_r.indiv_klasse)
        dupe.save()

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command('verwijder_dupe_data', '--commit')

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue('Verwijder alle data voor deelnemer 123456' in f2.getvalue())
        self.assertTrue(' 3 deelnemers' in f2.getvalue())

    def test_check_ag(self):
        deelnemer = RegiocompetitieSporterBoog.objects.first()
        deelnemer.ag_voor_team_mag_aangepast_worden = True
        deelnemer.inschrijf_voorkeur_team = True
        deelnemer.save(update_fields=['ag_voor_team_mag_aangepast_worden', 'inschrijf_voorkeur_team'])

        self.run_management_command('check_ag')

    def test_score_interval(self):
        score = Score(
                    type=SCORE_TYPE_SCORE,
                    sporterboog=self.sporterboog_tr,        # TR = huidige inschrijving
                    waarde=42,
                    afstand_meter=18)
        score.save()
        self.deelnemer_tr.scores.add(score)
        hist = ScoreHist(
                    score=score,
                    oude_waarde=0,
                    nieuwe_waarde=42,
                    door_account=None,
                    notitie='Test')
        hist.save()
        score = Score(
                    type=SCORE_TYPE_SCORE,
                    sporterboog=self.sporterboog_tr,        # TR = huidige inschrijving
                    waarde=43,
                    afstand_meter=18)
        score.save()
        self.deelnemer_tr.scores.add(score)
        hist = ScoreHist(
                    score=score,
                    oude_waarde=0,
                    nieuwe_waarde=43,
                    door_account=None,
                    notitie='Test')
        hist.save()

        self.run_management_command('report_score_interval', '18', '111')


# end of file
