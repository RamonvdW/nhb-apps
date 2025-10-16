# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamType
from Competitie.definities import (DEEL_RK, DEEL_BK,
                                   TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_MODEL_FORMULE1, TEAM_PUNTEN_MODEL_SOM_SCORES)
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMutatie,
                               Regiocompetitie, RegiocompetitieSporterBoog,
                               RegiocompetitieTeam, RegiocompetitieTeamPoule, RegiocompetitieRondeTeam,
                               Kampioenschap)
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import (zet_competitie_fase_rk_wedstrijden, zet_competitie_fase_regio_inschrijven,
                                            zet_competitie_fase_regio_afsluiten)
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio, Cluster
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompLaagRegioTeamsRCL(E2EHelpers, TestCase):

    """ tests voor de CompLaagRegio applicatie, Teams functies voor de RCL """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_ag_controle = '/bondscompetities/regio/%s/ag-controle/regio-%s/'          # comp_pk, regio-nr
    url_regio_teams = '/bondscompetities/regio/%s/teams/'                         # deelcomp_pk
    url_regio_teams_alle = '/bondscompetities/regio/%s/teams/%s/'                 # comp_pk, subset=auto/alle/rayon_nr
    url_regio_teams_bestand = '/bondscompetities/regio/%s/teams/als-bestand/'     # deelcomp_pk
    url_team_ronde = '/bondscompetities/regio/%s/team-ronde/'                     # deelcomp_pk
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp_pk
    url_overzicht_beheer = '/bondscompetities/beheer/%s/'                                       # comp_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter(
                    lid_nr=lid_nr,
                    geslacht="M",
                    voornaam=voornaam,
                    achternaam="Tester",
                    email=voornaam.lower() + "@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver_101)
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = Rayon.objects.get(rayon_nr=1)
        self.rayon_2 = Rayon.objects.get(rayon_nr=2)
        self.regio_101 = Regio.objects.get(regio_nr=101)
        self.regio_105 = Regio.objects.get(regio_nr=105)
        self.regio_112 = Regio.objects.get(regio_nr=112)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Zuidelijke Club",
                    ver_nr=1111,
                    regio=self.regio_112)
        ver.save()
        self.ver_112 = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl1111 = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl1111.vereniging = ver
        self.functie_hwl1111.save()

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_101)
        ver.save()
        self.ver_101 = ver

        loc = WedstrijdLocatie(banen_18m=1,
                               banen_25m=1,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc = loc

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL Vereniging %s" % ver.ver_nr, "WL")
        self.functie_wl.vereniging = ver
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

        # creëer een competitie met regiocompetities
        competities_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # een parallel competitie is noodzakelijk om corner-cases te raken
        competities_aanmaken(jaar=2020)

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen_18 = self.url_klassengrenzen_vaststellen % self.comp_18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)  # check for success

        klasse = CompetitieTeamKlasse.objects.get(competitie=self.comp_18,
                                                  volgorde=15,        # Rec ERE
                                                  is_voor_teams_rk_bk=False)
        klasse.min_ag = 29.0
        klasse.save()

        klasse = CompetitieTeamKlasse.objects.get(competitie=self.comp_18,
                                                  volgorde=16,        # Rec A
                                                  is_voor_teams_rk_bk=False)
        klasse.min_ag = 25.0
        klasse.save()

        self.client.logout()

        self.klasse_recurve_onbekend = (CompetitieIndivKlasse
                                        .objects
                                        .filter(boogtype=self.boog_r,
                                                is_onbekend=True)
                                        .all())[0]

        self.deelcomp_bond_18 = Kampioenschap.objects.filter(competitie=self.comp_18, deel=DEEL_BK).first()
        self.deelcomp_rayon1_18 = Kampioenschap.objects.filter(competitie=self.comp_18,
                                                               deel=DEEL_RK, rayon=self.rayon_1).first()
        self.deelcomp_rayon2_18 = Kampioenschap.objects.filter(competitie=self.comp_18,
                                                               deel=DEEL_RK, rayon=self.rayon_2).first()
        self.deelcomp_regio101_18 = Regiocompetitie.objects.filter(competitie=self.comp_18, regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = Regiocompetitie.objects.filter(competitie=self.comp_25, regio=self.regio_101)[0]
        self.deelcomp_regio112_18 = Regiocompetitie.objects.filter(competitie=self.comp_18, regio=self.regio_112)[0]

        self.cluster_101a_18 = Cluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')
        self.cluster_101e_25 = Cluster.objects.get(regio=self.regio_101, letter='e', gebruik='25')

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
        ver = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver.save()
        ver.clusters.add(self.cluster_101e_25)

    def _maak_teams(self, deelcomp):
        """ schrijf een aantal teams in """

        teamtype_r = TeamType.objects.get(afkorting='R2')
        klasse_r_ere = CompetitieTeamKlasse.objects.get(
                                    competitie=deelcomp.competitie,
                                    volgorde=15,                      # Rec ERE
                                    is_voor_teams_rk_bk=False)        # zie WKL_TEAM in BasisTypen migrations

        team1 = RegiocompetitieTeam(
                    regiocompetitie=deelcomp,
                    vereniging=self.ver_112,
                    volg_nr=1,
                    team_type=teamtype_r,
                    team_naam='Test team 1',
                    aanvangsgemiddelde=20.0,
                    team_klasse=klasse_r_ere)
        team1.save()

        team2 = RegiocompetitieTeam(
                    regiocompetitie=deelcomp,
                    vereniging=self.ver_112,
                    volg_nr=2,
                    team_type=teamtype_r,
                    team_naam='Test team 2',
                    aanvangsgemiddelde=21.123,
                    team_klasse=klasse_r_ere)
        team2.save()

        team3 = RegiocompetitieTeam(
                    regiocompetitie=deelcomp,
                    vereniging=self.ver_112,
                    volg_nr=3,
                    team_type=teamtype_r,
                    team_naam='Test team 3',
                    aanvangsgemiddelde=18.042,
                    team_klasse=klasse_r_ere)
        team3.save()

        poule = RegiocompetitieTeamPoule(
                    regiocompetitie=deelcomp,
                    beschrijving='Test poule')
        poule.save()
        poule.teams.add(team1)
        poule.teams.add(team2)
        poule.teams.add(team3)
        # 3 teams zorgt voor een wedstrijd met een Bye

        return team1, poule

    def test_regio_teams(self):
        # RCL ziet teams
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        team_r = TeamType.objects.get(afkorting='R2')
        klasse_r_ere = CompetitieTeamKlasse.objects.get(
                                    competitie=self.comp_18,
                                    volgorde=15,      # Rec ERE
                                    is_voor_teams_rk_bk=False)
        # create two complete teams
        RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
                volg_nr=1,
                team_type=team_r,
                team_naam='Test team 1',
                aanvangsgemiddelde=25.0,
                team_klasse=klasse_r_ere).save()

        RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
                volg_nr=2,
                team_type=team_r,
                team_naam='Test team 2',
                aanvangsgemiddelde=24.5,
                team_klasse=klasse_r_ere).save()

        # create a partial team
        RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
                volg_nr=3,
                team_type=team_r,
                team_naam='Test team 2',
                aanvangsgemiddelde=0.0).save()

        temp_team = RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
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
        self.assert_template_used(resp, ('complaagregio/rcl-teams.dtl', 'design/site_layout.dtl'))

        # verkeerde deelcomp
        resp = self.client.get(self.url_regio_teams % self.deelcomp_regio101_18.pk)
        self.assert403(resp)

        # niet bestaande deelcomp
        resp = self.client.get(self.url_regio_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

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
        self.assert_template_used(resp, ('complaagregio/rcl-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_teams_alle % (self.comp_18.pk, 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_teams_alle % (self.comp_18.pk, '3')        # rayon_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-teams.dtl', 'design/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_regio_teams_alle % (self.comp_18.pk, 'auto')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_teams_alle % (999999, 'auto')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_regio_teams_alle % (self.comp_18.pk, '999999')        # rayon_nr
        resp = self.client.get(url)
        self.assert404(resp, 'Selectie wordt niet ondersteund')

        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        url = self.url_regio_teams_alle % (self.comp_18.pk, 'auto')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Selectie wordt niet ondersteund')

    def test_teams_bestand(self):
        # BB
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        # verkeerde rol
        url = self.url_regio_teams_bestand % self.deelcomp_regio101_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

        # RCL 18
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        team_r = TeamType.objects.get(afkorting='R2')
        klasse_r_ere = CompetitieTeamKlasse.objects.get(
                                    competitie=self.comp_18,
                                    volgorde=15,      # Rec ERE
                                    is_voor_teams_rk_bk=False)
        # create two complete teams
        RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
                volg_nr=1,
                team_type=team_r,
                team_naam='Test team 1',
                aanvangsgemiddelde=25.0,
                team_klasse=klasse_r_ere).save()

        RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
                volg_nr=2,
                team_type=team_r,
                team_naam='Test team 2',
                aanvangsgemiddelde=24.5,
                team_klasse=klasse_r_ere).save()

        # create a partial team
        RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
                volg_nr=3,
                team_type=team_r,
                team_naam='Test team 2',
                aanvangsgemiddelde=0.0).save()

        temp_team = RegiocompetitieTeam(
                regiocompetitie=self.deelcomp_regio112_18,
                vereniging=self.ver_112,
                volg_nr=3,
                team_type=team_r,
                team_naam='',
                aanvangsgemiddelde=0.0)
        self.assertTrue(temp_team.maak_team_naam_kort() != '')

        # als bestand
        url = self.url_regio_teams_bestand % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert200_is_bestand_csv(resp)

        # RCL 25
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)
        url = self.url_regio_teams_bestand % self.deelcomp_regio101_25.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert200_is_bestand_csv(resp)

        # niet bestaande deelcomp
        resp = self.client.get(self.url_regio_teams_bestand % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        # foute deelcomp
        url = self.url_regio_teams_bestand % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Verkeerde beheerder')

    def test_ag_controle(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        url = self.url_ag_controle % (self.comp_18.pk, 101)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-ag-controle.dtl', 'design/site_layout.dtl'))

        # maak een inschrijving met handmatig AG
        RegiocompetitieSporterBoog(
                sporterboog=self.sporterboog,
                bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                regiocompetitie=self.deelcomp_regio101_18,
                indiv_klasse=self.klasse_recurve_onbekend,
                inschrijf_voorkeur_team=True,
                ag_voor_team_mag_aangepast_worden=True,
                ag_voor_team=5.0).save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # verkeerde fase
        zet_competitie_fase_rk_wedstrijden(self.comp_18)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        # bad pk
        resp = self.client.get(self.url_ag_controle % (999999, 999999))
        self.assert404(resp, 'Competitie niet gevonden')

        # verkeerde regio
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_controle % (self.comp_18.pk, 110))
        self.assert403(resp)

    def test_team_ronde_2p(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 0)

        self.deelcomp_regio112_18.regio_team_punten_model = TEAM_PUNTEN_MODEL_TWEE
        self.deelcomp_regio112_18.save(update_fields=['regio_team_punten_model'])

        url = self.url_team_ronde % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie bestaat niet')

        resp = self.client.post(url)
        self.assert404(resp, 'Competitie bestaat niet')

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertTrue(len(urls) == 1)
        self.assertTrue(url in urls)

        # maak een paar teams aan
        team1, poule = self._maak_teams(self.deelcomp_regio112_18)

        # maak 1 team niet af
        old_klasse = team1.team_klasse
        team1.team_klasse = None
        team1.save(update_fields=['team_klasse'])
        # TODO: voorkom opstarten ronde1 zonder de team_klasse ingevuld

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertTrue(len(urls) == 0)

        team1.team_klasse = old_klasse
        team1.save(update_fields=['team_klasse'])

        # start de eerste ronde op
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)

        # nog een paar, om concurrency protection te testen
        self.client.post(url, {'snel': 1})
        self.client.post(url, {'snel': 1})

        self.verwerk_competitie_mutaties(show_warnings=False)

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # doorzetten zonder scores werkt niet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Te weinig scores')

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # voer een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten met scores werkt wel
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)
        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 2)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # nog een rondje, dan komen in het schema met head-to-head wedstrijden

        # voer weer een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)
        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 3)

    def test_team_ronde_f1(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 0)

        self.deelcomp_regio112_18.regio_team_punten_model = TEAM_PUNTEN_MODEL_FORMULE1
        self.deelcomp_regio112_18.save(update_fields=['regio_team_punten_model'])

        zet_competitie_fase_regio_inschrijven(self.comp_18)

        # maak een paar teams aan
        team1, poule = self._maak_teams(self.deelcomp_regio112_18)

        # verwijder 1 team uit de poule
        poule.teams.remove(team1)

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # herstel de poule
        poule.teams.add(team1)

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # start de eerste ronde op
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)

        self.assertEqual(0, Taak.objects.count())
        self.verwerk_competitie_mutaties()

        # controleer dat de HWLs een taak gekregen hebben
        self.assertTrue(Taak.objects.count() > 0)

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # doorzetten zonder scores werkt niet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Te weinig scores')

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # voer een paar scores in
        top_teams = list(RegiocompetitieRondeTeam.objects.values_list('pk', flat=True))
        top_teams = top_teams[-2:]
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            if ronde_team.pk in top_teams:
                ronde_team.team_score = 999
            else:
                ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten met scores werkt wel
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)
        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 2)

        # controleer de wp verdeling: de twee top teams hebben dezelfde score, dus dezelfde wp
        wps = list(RegiocompetitieRondeTeam.objects.filter(pk__in=top_teams).values_list('team_punten', flat=True))
        self.assertEqual(wps, [10, 10])

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
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # start de eerste ronde op
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)

        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # doorzetten zonder scores werkt niet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Te weinig scores')

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # voor een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.save(update_fields=['team_score'])
        # for

        # doorzetten met scores werkt wel
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)
        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 2)

    def test_laatste_ronde(self):
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
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # start de eerste ronde op
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)

        self.verwerk_competitie_mutaties()

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 1)

        # forceer ronde 7
        self.deelcomp_regio112_18.huidige_team_ronde = 7
        self.deelcomp_regio112_18.regio_heeft_vaste_teams = False
        self.deelcomp_regio112_18.save(update_fields=['huidige_team_ronde', 'regio_heeft_vaste_teams'])

        # voor een paar scores in
        for ronde_team in RegiocompetitieRondeTeam.objects.all():
            ronde_team.team_score = 100 + ronde_team.pk
            ronde_team.ronde_nr = 7
            ronde_team.save(update_fields=['team_score', 'ronde_nr'])
        # for

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # zet fase G waarin we geen taken meer aanmaken
        zet_competitie_fase_regio_afsluiten(self.comp_18)

        CompetitieMutatie.objects.all().delete()
        Taak.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)

        self.verwerk_competitie_mutaties()

        self.assertEqual(0, Taak.objects.count())

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 99)

        url = self.url_team_ronde % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-team-ronde.dtl', 'design/site_layout.dtl'))

        # nog een keer doorzetten doet niets
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht_beheer % self.deelcomp_regio112_18.competitie.pk)

        # laat de laatste mutatie (doorzetten ronde 7) nog een keer verwerken
        self.assertEqual(1, CompetitieMutatie.objects.count())
        mutatie = CompetitieMutatie.objects.first()
        mutatie.is_verwerkt = False
        mutatie.save(update_fields=['is_verwerkt'])
        # laat deze herstelde mutatie verwerken
        self.run_management_command('competitie_mutaties', '1', '--quick')

        self.deelcomp_regio112_18 = Regiocompetitie.objects.get(pk=self.deelcomp_regio112_18.pk)
        self.assertEqual(self.deelcomp_regio112_18.huidige_team_ronde, 99)


# end of file
