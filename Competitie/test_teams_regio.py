# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType, TeamType
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse, LAAG_BK, LAAG_RK, LAAG_REGIO,
                               RegioCompetitieSchutterBoog,
                               RegiocompetitieTeam, RegiocompetitieTeamPoule, RegiocompetitieRondeTeam,
                               TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_MODEL_FORMULE1, TEAM_PUNTEN_MODEL_SOM_SCORES)
from Competitie.operations import competities_aanmaken
from Competitie.test_fase import zet_competitie_fase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime
import io


class TestCompetitieRegioTeams(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    url_afsluiten_regio = '/bondscompetities/planning/regio/%s/afsluiten/'  # deelcomp_pk
    url_regio_instellingen = '/bondscompetities/%s/instellingen/regio-%s/'  # comp_pk, regio-nr
    url_regio_globaal = '/bondscompetities/%s/instellingen/globaal/'  # comp_pk
    url_ag_controle = '/bondscompetities/%s/ag-controle/regio-%s/'  # comp_pk, regio-nr
    url_regio_teams = '/bondscompetities/regio/%s/teams/'  # deelcomp_pk
    url_regio_teams_alle = '/bondscompetities/regio/%s/teams/%s/'  # comp_pk, subset = auto/alle/rayon_nr
    url_regio_poules = '/bondscompetities/regio/%s/poules/'  # deelcomp_pk
    url_wijzig_poule = '/bondscompetities/regio/poules/%s/wijzig/'  # poule_pk
    url_team_ronde = '/bondscompetities/regio/%s/team-ronde/'  # deelcomp_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter()
        sporter.lid_nr = lid_nr
        sporter.geslacht = "M"
        sporter.voornaam = voornaam
        sporter.achternaam = "Tester"
        sporter.email = voornaam.lower() + "@nhb.test"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = self.nhbver_101
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)
        self.regio_105 = NhbRegio.objects.get(regio_nr=105)
        self.regio_112 = NhbRegio.objects.get(regio_nr=112)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Zuidelijke Club"
        ver.ver_nr = 1111
        ver.regio = self.regio_112
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = 1000
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_101 = ver

        loc = WedstrijdLocatie(banen_18m=1,
                               banen_25m=1,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc = loc

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL Vereniging %s" % ver.ver_nr, "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL101')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL101-25')
        self.account_rcl112_18 = self._prep_beheerder_lid('RCL112')
        self.account_schutter = self._prep_beheerder_lid('Schutter')
        self.lid_sporter = Sporter.objects.get(lid_nr=self.account_schutter.username)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.sporterboog = SporterBoog(sporter=self.lid_sporter,
                                       boogtype=self.boog_r,
                                       voor_wedstrijd=True)
        self.sporterboog.save()

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # een parallel competitie is noodzakelijk om corner-cases te raken
        competities_aanmaken(jaar=2020)

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.url_klassegrenzen_vaststellen_18 = '/bondscompetities/%s/klassegrenzen/vaststellen/' % self.comp_18.pk
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)  # check for success

        klasse = CompetitieKlasse.objects.get(competitie=self.comp_18,
                                              team__volgorde=10)
        klasse.min_ag = 29.0
        klasse.save()

        klasse = CompetitieKlasse.objects.get(competitie=self.comp_18,
                                              team__volgorde=11)
        klasse.min_ag = 25.0
        klasse.save()

        self.client.logout()

        self.klasse_recurve_onbekend = (CompetitieKlasse
                                        .objects
                                        .filter(indiv__boogtype=self.boog_r,
                                                indiv__is_onbekend=True)
                                        .all())[0]

        self.deelcomp_bond_18 = DeelCompetitie.objects.filter(laag=LAAG_BK, competitie=self.comp_18)[0]
        self.deelcomp_rayon1_18 = DeelCompetitie.objects.filter(laag=LAAG_RK, competitie=self.comp_18, nhb_rayon=self.rayon_1)[0]
        self.deelcomp_rayon2_18 = DeelCompetitie.objects.filter(laag=LAAG_RK, competitie=self.comp_18, nhb_rayon=self.rayon_2)[0]
        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=self.comp_25, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio112_18 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=self.comp_18, nhb_regio=self.regio_112)[0]

        self.cluster_101a_18 = NhbCluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')
        self.cluster_101e_25 = NhbCluster.objects.get(regio=self.regio_101, letter='e', gebruik='25')

        self.functie_bko_18 = self.deelcomp_bond_18.functie
        self.functie_rko1_18 = self.deelcomp_rayon1_18.functie
        self.functie_rko2_18 = self.deelcomp_rayon2_18.functie
        self.functie_rcl101_18 = self.deelcomp_regio101_18.functie
        self.functie_rcl101_25 = self.deelcomp_regio101_25.functie
        self.functie_rcl112_18 = self.deelcomp_regio112_18.functie

        self.functie_bko_18.accounts.add(self.account_bko_18)
        self.functie_rko1_18.accounts.add(self.account_rko1_18)
        self.functie_rko2_18.accounts.add(self.account_rko2_18)
        self.functie_rcl101_18.accounts.add(self.account_rcl101_18)
        self.functie_rcl101_25.accounts.add(self.account_rcl101_25)
        self.functie_rcl112_18.accounts.add(self.account_rcl112_18)

        # maak nog een test vereniging, zonder HWL functie
        # stop deze in een cluster
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        ver.save()
        ver.clusters.add(self.cluster_101e_25)

    def _verwerk_mutaties(self, max_mutaties=20, show_warnings=True, show_all=False):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(max_mutaties):
            management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if show_all:                                    # pragma: no coverage
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):       # pragma: no coverage
                    print(line)
            # for

    def _maak_teams(self, deelcomp):
        """ schrijf een aantal teams in """

        teamtype_r = TeamType.objects.get(afkorting='R')
        klasse_r_ere = CompetitieKlasse.objects.get(
                                    competitie=deelcomp.competitie,
                                    team__volgorde=10)        # zie WKL_TEAM in BasisTypen migrations

        team1 = RegiocompetitieTeam(
                    deelcompetitie=deelcomp,
                    vereniging=self.nhbver_112,
                    volg_nr=1,
                    team_type=teamtype_r,
                    team_naam='Test team 1',
                    aanvangsgemiddelde=20.0,
                    klasse=klasse_r_ere)
        team1.save()

        team2 = RegiocompetitieTeam(
                    deelcompetitie=deelcomp,
                    vereniging=self.nhbver_112,
                    volg_nr=1,
                    team_type=teamtype_r,
                    team_naam='Test team 2',
                    aanvangsgemiddelde=21.123,
                    klasse=klasse_r_ere)
        team2.save()

        team3 = RegiocompetitieTeam(
                    deelcompetitie=deelcomp,
                    vereniging=self.nhbver_112,
                    volg_nr=1,
                    team_type=teamtype_r,
                    team_naam='Test team 3',
                    aanvangsgemiddelde=18.042,
                    klasse=klasse_r_ere)
        team3.save()

        # initiële schutters in het team
        # gekoppelde_schutters = models.ManyToManyField(RegioCompetitieSchutterBoog,
        #                                              blank=True)  # mag leeg zijn

        poule = RegiocompetitieTeamPoule(
                    deelcompetitie=deelcomp,
                    beschrijving='Test poule')
        poule.save()
        poule.teams.add(team1)
        poule.teams.add(team2)
        poule.teams.add(team3)
        # 3 teams zorgt voor een wedstrijd met een Bye

    def test_regio_instellingen(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        url = self.url_regio_instellingen % (self.comp_18.pk, 112)

        # fase A

        # tijdens competitie fase A mogen alle instellingen aangepast worden
        zet_competitie_fase(self.comp_18, 'A')

        # when the phase is set artificially, some dates are left behind
        # let's repair that here
        self.comp_18 = Competitie.objects.get(pk=self.comp_18.pk)
        self.comp_18.eerste_wedstrijd = self.comp_18.begin_aanmeldingen
        self.comp_18.eerste_wedstrijd += datetime.timedelta(days=1)
        self.comp_18.save()
        post_datum_ok = self.comp_18.begin_aanmeldingen.strftime('%Y-%m-%d')
        # print('begin_aanmeldingen: %s' % comp_datum1)
        post_datum_bad = self.comp_18.eerste_wedstrijd.strftime('%Y-%m-%d')
        # print('eerste_wedstrijd: %s' % comp_datum2)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-instellingen.dtl', 'plein/site_layout.dtl'))

        # all params missing
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # all params present
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'team_alloc': 'vast',
                                          'team_punten': 'F1',
                                          'einde_teams_aanmaken': post_datum_ok})
        self.assert_is_redirect_not_plein(resp)

        # late date
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'einde_teams_aanmaken': post_datum_bad})
        self.assert404(resp)  # 404 = Not allowed

        # late date - not checked when teams=nee
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'nee',
                                          'einde_teams_aanmaken': post_datum_bad})
        self.assert_is_redirect_not_plein(resp)
        # teamcompetitie staat nu op Nee
        # zet teamcompetitie weer op Ja
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'team_alloc': 'vast'})
        self.assert_is_redirect_not_plein(resp)

        # bad date
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'teams': 'ja',
                                          'einde_teams_aanmaken': 'xxx'})
        self.assert404(resp)  # 404 = Not allowed

        # fase B en C

        # tot en met fase C mogen de team punten en datum aanmaken teams aangepast worden
        oude_punten = 'F1'

        for fase in ('B', 'C'):
            zet_competitie_fase(self.comp_18, fase)

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('competitie/rcl-instellingen.dtl', 'plein/site_layout.dtl'))

            deelcomp_pre = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
            self.assertTrue(deelcomp_pre.regio_organiseert_teamcompetitie)
            self.assertTrue(deelcomp_pre.regio_heeft_vaste_teams)
            self.assertEqual(deelcomp_pre.regio_team_punten_model, oude_punten)
            if oude_punten == 'F1':
                nieuwe_punten = '2P'
            else:
                nieuwe_punten = 'SS'

            # all params present
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'teams': 'nee',
                                              'team_alloc': 'vsg',
                                              'team_punten': nieuwe_punten,
                                              'einde_teams_aanmaken': post_datum_ok})
            self.assert_is_redirect_not_plein(resp)

            deelcomp_post = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
            self.assertTrue(deelcomp_post.regio_organiseert_teamcompetitie)
            self.assertTrue(deelcomp_post.regio_heeft_vaste_teams)
            self.assertEqual(deelcomp_post.regio_team_punten_model, nieuwe_punten)
            oude_punten = nieuwe_punten

        # fase D

        zet_competitie_fase(self.comp_18, 'D')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-instellingen.dtl', 'plein/site_layout.dtl'))

    def test_regio_instellingen_bad(self):
        # bad cases
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        url = self.url_regio_instellingen % (self.comp_18.pk, 112)

        # na fase F zijn de instellingen niet meer in te zien
        zet_competitie_fase(self.comp_18, 'K')      # fase G is niet te zetten

        resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not found
        resp = self.client.post(url)
        self.assert404(resp)  # 404 = Not found

        # niet bestaande regio
        url = self.url_regio_instellingen % (self.comp_18.pk, 100)
        resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not found
        resp = self.client.post(url)
        self.assert404(resp)  # 404 = Not found

        # niet de regio van de RCL
        url = self.url_regio_instellingen % (self.comp_18.pk, 110)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        # logout

        url = self.url_regio_instellingen % (self.comp_18.pk, 112)
        self.client.logout()
        resp = self.client.get(url)
        self.assert403(resp)

    def test_regio_globaal(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        url = self.url_regio_globaal % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-instellingen-globaal.dtl', 'plein/site_layout.dtl'))

    def test_regio_teams(self):
        # RCL ziet teams
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        team_r = TeamType.objects.get(afkorting='R')
        klasse_r_ere = CompetitieKlasse.objects.get(
                                    competitie=self.comp_18,
                                    team__volgorde=10)
        # create two complete teams
        RegiocompetitieTeam(
                deelcompetitie=self.deelcomp_regio112_18,
                vereniging=self.nhbver_112,
                volg_nr=1,
                team_type=team_r,
                team_naam='Test team 1',
                aanvangsgemiddelde=25.0,
                klasse=klasse_r_ere).save()

        RegiocompetitieTeam(
                deelcompetitie=self.deelcomp_regio112_18,
                vereniging=self.nhbver_112,
                volg_nr=2,
                team_type=team_r,
                team_naam='Test team 2',
                aanvangsgemiddelde=24.5,
                klasse=klasse_r_ere).save()

        # create a partial team
        RegiocompetitieTeam(
                deelcompetitie=self.deelcomp_regio112_18,
                vereniging=self.nhbver_112,
                volg_nr=3,
                team_type=team_r,
                team_naam='Test team 2',
                aanvangsgemiddelde=0.0).save()

        temp_team = RegiocompetitieTeam(
                deelcompetitie=self.deelcomp_regio112_18,
                vereniging=self.nhbver_112,
                volg_nr=3,
                team_type=team_r,
                team_naam='',
                aanvangsgemiddelde=0.0)
        self.assertTrue(temp_team.maak_team_naam_kort() != '')

        url = self.url_regio_teams % self.deelcomp_regio112_18.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-teams.dtl', 'plein/site_layout.dtl'))

        # verkeerde deelcomp
        resp = self.client.get(self.url_regio_teams % self.deelcomp_regio101_18.pk)
        self.assert403(resp)

        # niet bestaande deelcomp
        resp = self.client.get(self.url_regio_teams % 999999)
        self.assert404(resp)  # 404 = Not allowed

        # logout

        self.client.logout()
        resp = self.client.get(url)
        self.assert403(resp)

        # 25m

        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        url = self.url_regio_teams % self.deelcomp_regio101_25.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # BB
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        url = self.url_regio_teams_alle % (self.comp_18.pk, 'auto')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_teams_alle % (self.comp_18.pk, 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_teams_alle % (self.comp_18.pk, '3')        # rayon_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-teams.dtl', 'plein/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_regio_teams_alle % (self.comp_18.pk, 'auto')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_teams_alle % (999999, 'auto')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_regio_teams_alle % (self.comp_18.pk, '999999')        # rayon_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Selectie wordt niet ondersteund')

        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        url = self.url_regio_teams_alle % (self.comp_18.pk, 'auto')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Selectie wordt niet ondersteund')

    def test_ag_controle(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        url = self.url_ag_controle % (self.comp_18.pk, 112)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-ag-controle.dtl', 'plein/site_layout.dtl'))

        # maak een inschrijving met handmatig AG
        RegioCompetitieSchutterBoog(
                sporterboog=self.sporterboog,
                bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                deelcompetitie=self.deelcomp_regio112_18,
                klasse=self.klasse_recurve_onbekend,
                inschrijf_voorkeur_team=True,
                ag_voor_team_mag_aangepast_worden=True,
                ag_voor_team=5.0).save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # verkeerde fase
        zet_competitie_fase(self.comp_18, 'K')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        # bad pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_controle % (999999, 999999))
        self.assert404(resp)

        # verkeerde regio
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_controle % (self.comp_18.pk, 110))
        self.assert403(resp)

    def test_poules_basic(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        deelcomp = DeelCompetitie.objects.get(competitie=self.comp_18, functie=self.functie_rcl112_18)

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-teams-poules.dtl', 'plein/site_layout.dtl'))

        # tot en met fase D mag alles nog
        comp = deelcomp.competitie
        zet_competitie_fase(comp, 'D')

        # maak een poule aan
        self.assertEqual(0, RegiocompetitieTeamPoule.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())
        poule = RegiocompetitieTeamPoule.objects.all()[0]

        # bad deelcomp
        bad_url = self.url_regio_poules % 999999
        resp = self.client.get(bad_url)
        self.assert404(resp)
        resp = self.client.post(bad_url)
        self.assert404(resp)

        # verkeerde beheerder
        bad_url = self.url_regio_poules % self.deelcomp_regio101_18.pk
        resp = self.client.get(bad_url)
        self.assert403(resp)
        resp = self.client.post(bad_url)
        self.assert403(resp)

        # wijzig de poule
        url = self.url_wijzig_poule % poule.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-poule.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'beschrijving': ' hoi test!'})
        self.assert_is_redirect_not_plein(resp)
        poule = RegiocompetitieTeamPoule.objects.get(pk=poule.pk)
        self.assertEqual(poule.beschrijving, 'hoi test!')

        # wijziging is geen wijziging
        resp = self.client.post(url, {'beschrijving': ' hoi test!'})
        self.assert_is_redirect_not_plein(resp)

        # bad poule
        bad_url = self.url_wijzig_poule % 999999
        resp = self.client.get(bad_url)
        self.assert404(resp)
        resp = self.client.post(bad_url)
        self.assert404(resp)

        # verkeerde beheerder
        poule.deelcompetitie = self.deelcomp_regio101_25
        poule.save(update_fields=['deelcompetitie'])
        bad_url = self.url_wijzig_poule % poule.pk
        resp = self.client.get(bad_url)
        self.assert403(resp)
        resp = self.client.post(bad_url)
        self.assert403(resp)
        poule.deelcompetitie = self.deelcomp_regio112_18
        poule.save(update_fields=['deelcompetitie'])

        # overzicht met een poule erin
        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # na fase D mag je nog kijken maar niet aanpassen
        comp = deelcomp.competitie
        zet_competitie_fase(comp, 'E')

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-teams-poules.dtl', 'plein/site_layout.dtl'))

        # maak een poule aan
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())

        # fase E: wijzig de poule
        url = self.url_wijzig_poule % poule.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-poule.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'beschrijving': 'nieuwe test'})
        self.assert_is_redirect_not_plein(resp)

        # TODO: controleer dat de teams gekoppeld aan de poule niet meer te wijzigen zijn

        # zet fase F, dan mag niets meer gewijzigd worden
        zet_competitie_fase(comp, 'F')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'beschrijving': 'nieuwe test'})
        self.assert404(resp)

        # terug naar fase D
        comp = deelcomp.competitie
        zet_competitie_fase(comp, 'D')

        # verwijder een poule
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())
        url = self.url_wijzig_poule % poule.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_poule': 'aj'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(0, RegiocompetitieTeamPoule.objects.count())

    def test_poules_teams(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        # maak een poule aan
        deelcomp = DeelCompetitie.objects.get(competitie=self.comp_18, functie=self.functie_rcl112_18)

        # tot en met fase D mag alles nog
        comp = deelcomp.competitie
        zet_competitie_fase(comp, 'B')

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())
        poule = RegiocompetitieTeamPoule.objects.all()[0]

        # maak 9 teams aan
        type_r = TeamType.objects.get(afkorting='R')
        klasse_r_ere = CompetitieKlasse.objects.filter(team__team_type=type_r).order_by('team__volgorde')[0]
        for lp in range(9):
            # team zonder sporters maar wel in een klasse is genoeg voor een poule
            RegiocompetitieTeam(
                    deelcompetitie=deelcomp,
                    vereniging=self.nhbver_112,
                    volg_nr=lp + 1,
                    team_type=type_r,
                    team_naam='Recurve Testers %s' % (lp + 1),
                    klasse=klasse_r_ere).save()
        # for
        team_pks = list(RegiocompetitieTeam.objects.values_list('pk', flat=True))

        # maak een compound team aan
        type_c = TeamType.objects.get(afkorting='C')
        klasse_c_ere = CompetitieKlasse.objects.filter(team__team_type=type_c).order_by('team__volgorde')[0]
        team_c = RegiocompetitieTeam(
                    deelcompetitie=deelcomp,
                    vereniging=self.nhbver_112,
                    volg_nr=1,
                    team_type=type_c,
                    team_naam='Compound Testers 9',
                    klasse=klasse_c_ere)
        team_c.save()

        # koppel 5 teams aan de poule
        url = self.url_wijzig_poule % poule.pk
        params = dict()
        for pk in team_pks[:5]:
            params['team_%s' % pk] = 1
        with self.assert_max_queries(20):
            resp = self.client.post(url, params)
        self.assert_is_redirect_not_plein(resp)
        poule = RegiocompetitieTeamPoule.objects.prefetch_related('teams').get(pk=poule.pk)
        self.assertEqual(5, poule.teams.count())

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-poule.dtl', 'plein/site_layout.dtl'))

        # compound team bij recurve-meerderheid wordt niet geaccepteerd (silently ignored)
        params['team_%s' % team_c.pk] = 1
        with self.assert_max_queries(20):
            resp = self.client.post(url, params)
        self.assert_is_redirect_not_plein(resp)
        poule = RegiocompetitieTeamPoule.objects.prefetch_related('teams').get(pk=poule.pk)
        self.assertEqual(5, poule.teams.count())

        # koppel 9 teams aan de poule
        self.assertEqual(9, len(team_pks))
        params = dict()
        for pk in team_pks:
            params['team_%s' % pk] = 1
        with self.assert_max_queries(20):
            resp = self.client.post(url, params)
        self.assert_is_redirect_not_plein(resp)
        poule = RegiocompetitieTeamPoule.objects.prefetch_related('teams').get(pk=poule.pk)
        self.assertEqual(8, poule.teams.count())

    def test_team_ronde_2p(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 0)

        self.deelcomp_regio112_18.regio_team_punten_model = TEAM_PUNTEN_MODEL_TWEE
        self.deelcomp_regio112_18.save(update_fields=['regio_team_punten_model'])

        url = self.url_team_ronde % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Competitie bestaat niet')

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Competitie bestaat niet')

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-team-ronde.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertTrue(len(urls) == 1)
        self.assertTrue(url in urls)

        # maak een paar teams aan
        self._maak_teams(self.deelcomp_regio112_18)

        # start de eerste ronde op
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.deelcomp_regio112_18.competitie.pk)

        # nog een paar om concurrency echt flink te testen
        self.client.post(url, {'snel': 1})
        self.client.post(url, {'snel': 1})

        self._verwerk_mutaties(51, show_warnings=False)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # doorzetten zonder scores werkt niet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Te weinig scores')

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        self._verwerk_mutaties(20)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # voer een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten met scores werkt wel
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.deelcomp_regio112_18.competitie.pk)
        self._verwerk_mutaties(39)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 2)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-team-ronde.dtl', 'plein/site_layout.dtl'))

        # nog een rondje, dan komen in het schema met head-to-head wedstrijden

        # voer weer een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.deelcomp_regio112_18.competitie.pk)
        self._verwerk_mutaties(39)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 3)

    def test_team_ronde_f1(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 0)

        self.deelcomp_regio112_18.regio_team_punten_model = TEAM_PUNTEN_MODEL_FORMULE1
        self.deelcomp_regio112_18.save(update_fields=['regio_team_punten_model'])
        # TEAM_PUNTEN_MODEL_SOM_SCORES

        # maak een paar teams aan
        self._maak_teams(self.deelcomp_regio112_18)

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-team-ronde.dtl', 'plein/site_layout.dtl'))

        # start de eerste ronde op
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.deelcomp_regio112_18.competitie.pk)

        self._verwerk_mutaties(39)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # doorzetten zonder scores werkt niet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Te weinig scores')

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        self._verwerk_mutaties(20)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # voor een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten met scores werkt wel
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.deelcomp_regio112_18.competitie.pk)
        self._verwerk_mutaties(39)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 2)

    def test_team_ronde_som(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 0)

        self.deelcomp_regio112_18.regio_team_punten_model = TEAM_PUNTEN_MODEL_SOM_SCORES
        self.deelcomp_regio112_18.save(update_fields=['regio_team_punten_model'])

        # maak een paar teams aan
        self._maak_teams(self.deelcomp_regio112_18)

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-team-ronde.dtl', 'plein/site_layout.dtl'))

        # start de eerste ronde op
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.deelcomp_regio112_18.competitie.pk)

        self._verwerk_mutaties(39)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # doorzetten zonder scores werkt niet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Te weinig scores')

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        self._verwerk_mutaties(20)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # voor een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten met scores werkt wel
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.deelcomp_regio112_18.competitie.pk)
        self._verwerk_mutaties(39)

        self.deelcomp_regio112_18 = DeelCompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 2)


# end of file
