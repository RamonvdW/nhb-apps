# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import IndivWedstrijdklasse, BoogType, TeamType
from Competitie.models import (Competitie, CompetitieKlasse,
                               DeelCompetitie, LAAG_REGIO,
                               RegioCompetitieSchutterBoog, RegiocompetitieTeam)
from Competitie.test_fase import zet_competitie_fase
from NhbStructuur.models import NhbVereniging, NhbRegio
from Score.models import Score, SCORE_TYPE_INDIV_AG
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


class TestCompRegioCli(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command check_klasse """

    def setUp(self):
        """ initialisatie van de test case """
        regio_111 = NhbRegio.objects.get(pk=111)

        boog_r = BoogType.objects.get(afkorting='R')
        boog_bb = BoogType.objects.get(afkorting='BB')
        boog_ib = BoogType.objects.get(afkorting='IB')

        teamtype_r = TeamType.objects.get(afkorting='R')

        datum = datetime.date(year=2000, month=1, day=1)

        comp = Competitie(
                    beschrijving='Test',
                    afstand='18',
                    begin_jaar=2000,
                    uiterste_datum_lid=datum,
                    begin_aanmeldingen=datum,
                    einde_aanmeldingen=datum,
                    einde_teamvorming=datum,
                    eerste_wedstrijd=datum,
                    laatst_mogelijke_wedstrijd=datum,
                    datum_klassengrenzen_rk_bk_teams=datum,
                    rk_eerste_wedstrijd=datum,
                    rk_laatste_wedstrijd=datum,
                    bk_eerste_wedstrijd=datum,
                    bk_laatste_wedstrijd=datum)
        comp.save()
        self.comp = comp

        deelcomp = DeelCompetitie(
                            competitie=comp,
                            laag=LAAG_REGIO,
                            nhb_regio=regio_111)
        deelcomp.save()

        indiv_r1 = IndivWedstrijdklasse.objects.filter(boogtype=boog_r)[1]
        indiv_r2 = IndivWedstrijdklasse.objects.filter(boogtype=boog_r)[2]
        indiv_ib = IndivWedstrijdklasse.objects.filter(boogtype=boog_ib)[0]
        indiv_bb = IndivWedstrijdklasse.objects.filter(boogtype=boog_bb)[0]

        klasse_r1 = CompetitieKlasse(
                        competitie=comp,
                        indiv=indiv_r1,
                        min_ag=2.0)
        klasse_r1.save()

        CompetitieKlasse(
                competitie=comp,
                indiv=indiv_r2,
                min_ag=1.0).save()

        CompetitieKlasse(
                competitie=comp,
                indiv=indiv_bb,
                min_ag=0.0).save()

        klasse_ib = CompetitieKlasse(
                        competitie=comp,
                        indiv=indiv_ib,
                        min_ag=0.0)
        klasse_ib.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club met een naam langer dan 30 tekens"
        ver.ver_nr = "1000"
        ver.regio = regio_111
        ver.save()

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 123456
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = None
        sporter.email = ''
        sporter.save()
        self.sporter = sporter

        sporterboog_r = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog_r.save()
        self.sporterboog_r = sporterboog_r

        sporterboog_ib = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_ib,
                            voor_wedstrijd=False)
        sporterboog_ib.save()
        self.sporterboog_ib = sporterboog_ib

        sporterboog_bb = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_bb,
                            voor_wedstrijd=False)
        sporterboog_bb.save()
        self.sporterboog_bb = sporterboog_bb

        deelnemer_r = RegioCompetitieSchutterBoog(
                            deelcompetitie=deelcomp,
                            sporterboog=sporterboog_r,
                            bij_vereniging=ver,
                            klasse=klasse_r1,
                            aantal_scores=1)
        deelnemer_r.save()
        self.deelnemer_r = deelnemer_r

        deelnemer_ib = RegioCompetitieSchutterBoog(
                            deelcompetitie=deelcomp,
                            sporterboog=sporterboog_ib,
                            bij_vereniging=ver,
                            klasse=klasse_ib,
                            aantal_scores=2)
        deelnemer_ib.save()
        self.deelnemer_ib = deelnemer_ib

        team = RegiocompetitieTeam(
                            deelcompetitie=deelcomp,
                            vereniging=ver,
                            volg_nr=1,
                            team_type=teamtype_r,
                            team_naam='Test')
        team.save()
        self.team = team

        team.gekoppelde_schutters.add(deelnemer_ib)

    def test_check_klasse(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_klasse', stderr=f1, stdout=f2)

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Let op: gebruik --commit' in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_klasse', '--commit', stderr=f1, stdout=f2)

        print("f1: %s" % f1.getvalue())
        print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(f2.getvalue() == '')

    def test_boogtype_check(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_check', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        self.assertTrue(f1.getvalue() == '')

        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[123456] Ramon' in f2.getvalue())
        self.assertTrue('IB -> R' in f2.getvalue())

        self.sporter.achternaam = "de Tester met speciale naam"
        #           [123456] Ramon de                    ^
        #           1234567890123456789012345678901234567890
        self.sporter.save()

        self.sporterboog_r.voor_wedstrijd = False
        self.sporterboog_r.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_check', stderr=f1, stdout=f2)

        # print("f2: %s" % f2.getvalue())
        self.assertTrue('met speciale..' in f2.getvalue())
        self.assertTrue('IB -> ?' in f2.getvalue())

    def test_boogtype_transfer(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'X', '18', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Onbekend boog type:' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'R', '18', stderr=f1, stdout=f2)

        # competitie is nog in fase A en heeft geen vastgestelde klassegrenzen
        self.assertTrue('[ERROR] Kan de competitie niet vinden' in f1.getvalue())

        zet_competitie_fase(self.comp, 'C')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '999999', 'R', '18', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Sporter 999999 niet gevonden' in f1.getvalue())

        self.sporterboog_r.voor_wedstrijd = False
        self.sporterboog_r.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'BB', '18', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Sporter heeft geen wedstrijd boog als voorkeur' in f1.getvalue())

        self.sporterboog_ib.voor_wedstrijd = True
        self.sporterboog_ib.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'IB', '18', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Sporter is al ingeschreven met dat boog type' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'BB', '18', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Sporter heeft boog BB niet als voorkeur. Wel: IB' in f1.getvalue())

        self.sporterboog_bb.voor_wedstrijd = True
        self.sporterboog_bb.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'BB', '18', stderr=f1, stdout=f2)

        # sporter is met R en IB ingeschreven
        self.assertTrue('[ERROR] Sporter met meerdere inschrijvingen wordt niet ondersteund' in f1.getvalue())

        self.deelnemer_r.delete()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'BB', '18', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Sporter is onderdeel van een team' in f1.getvalue())

        self.team.gekoppelde_schutters.clear()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '123456', 'BB', '18', stderr=f1, stdout=f2)

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Gebruik --commit om' in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('boogtype_transfer', '--commit', '123456', 'BB', '18', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(' is aangepast; scores zijn omgezet naar sporterboog ' in f2.getvalue())

    def test_regios_afsluiten(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regios_afsluiten', '18', '101', '10x', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Valide regio nummers: 101 tot 116' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regios_afsluiten', '18', '116', '115', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Valide regio nummers: 101 tot 116, oplopend' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regios_afsluiten', '99', '115', '116', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Kan competitie met afstand 99 niet vinden' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regios_afsluiten', '18', '101', '102', stderr=f1, stdout=f2)

        self.assertTrue('[ERROR] Competitie in fase A is niet ondersteund' in f1.getvalue())

        zet_competitie_fase(self.comp, 'F')

        # geen aangemaakte regios
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regios_afsluiten', '18', '101', '102', stderr=f1, stdout=f2)

        self.assertTrue('' == f1.getvalue())
        self.assertTrue('' == f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regios_afsluiten', '18', '111', '111', stderr=f1, stdout=f2)

        self.assertTrue('[INFO] Deelcompetitie Test - Regio 111 wordt afgesloten' in f2.getvalue())

        # nog een keer (terwijl al afgesloten)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regios_afsluiten', '18', '111', '111', stderr=f1, stdout=f2)

        self.assertTrue(f1.getvalue() == '')

    def test_fix_bad_ag(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('fix_bad_ag', stderr=f1, stdout=f2)

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(f2.getvalue() == '')

        Score(
            sporterboog=self.sporterboog_r,
            type=SCORE_TYPE_INDIV_AG,
            afstand_meter=18,
            waarde=8000).save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('fix_bad_ag', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')

    def test_check_wp_f1(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('check_wp_f1', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')

    def test_ronde_teams_check(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('ronde_teams_check', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue(f1.getvalue() == '')

    def test_verwijder_dupe_data(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('verwijder_dupe_data', stderr=f1, stdout=f2)

        self.assertTrue(f1.getvalue() == '')
        self.assertTrue(f2.getvalue() == '')

        # maak een echte dupe aan
        dupe = RegioCompetitieSchutterBoog(
                    deelcompetitie=self.deelnemer_r.deelcompetitie,
                    sporterboog=self.deelnemer_r.sporterboog,
                    bij_vereniging=self.deelnemer_r.bij_vereniging,
                    klasse=self.deelnemer_r.klasse)
        dupe.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('verwijder_dupe_data', stderr=f1, stdout=f2)

        self.assertTrue('Gebruik --commit om' in f1.getvalue())

        # maak nog een dupe aan, voor extra coverage
        dupe = RegioCompetitieSchutterBoog(
                    deelcompetitie=self.deelnemer_r.deelcompetitie,
                    sporterboog=self.deelnemer_r.sporterboog,
                    bij_vereniging=self.deelnemer_r.bij_vereniging,
                    klasse=self.deelnemer_r.klasse)
        dupe.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('verwijder_dupe_data', '--commit', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue('Verwijder alle data voor deelnemer 123456' in f2.getvalue())
        self.assertTrue(' 3 deelnemers' in f2.getvalue())


# end of file
