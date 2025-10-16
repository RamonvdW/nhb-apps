# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType, TeamType
from Competitie.definities import DEEL_RK, DEEL_BK, TEAM_PUNTEN_MODEL_FORMULE1
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               Regiocompetitie, RegiocompetitieTeam, RegiocompetitieTeamPoule,
                               RegiocompetitieRondeTeam,
                               Kampioenschap)
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import (evaluatie_datum, zet_competitie_fases,
                                            zet_competitie_fase_regio_wedstrijden,
                                            zet_competitie_fase_regio_inschrijven,
                                            zet_competitie_fase_regio_afsluiten)
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio, Cluster
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime
import io


class TestCompLaagRegioPoules(E2EHelpers, TestCase):

    """ tests voor de CompLaagRegio applicatie, Poules functie """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_regio_poules = '/bondscompetities/regio/poules/%s/'         # deelcomp_pk
    url_wijzig_poule = '/bondscompetities/regio/poules/wijzig/%s/'  # poule_pk
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp_pk

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
        evaluatie_datum.zet_test_datum('2019-09-01')

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
        self.deelcomp_regio101_18 = Regiocompetitie.objects.filter(competitie=self.comp_18,
                                                                   regio=self.regio_101).first()
        self.deelcomp_regio101_25 = Regiocompetitie.objects.filter(competitie=self.comp_25,
                                                                   regio=self.regio_101).first()
        self.deelcomp_regio112_18 = Regiocompetitie.objects.filter(competitie=self.comp_18,
                                                                   regio=self.regio_112).first()

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

    def test_poules_basic(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        deelcomp = Regiocompetitie.objects.get(competitie=self.comp_18, functie=self.functie_rcl112_18)

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-teams-poules.dtl', 'design/site_layout.dtl'))

        # tot en met fase D mag alles nog
        comp = deelcomp.competitie
        zet_competitie_fases(comp, 'C', 'D')

        # maak een poule aan
        self.assertEqual(0, RegiocompetitieTeamPoule.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())
        poule = RegiocompetitieTeamPoule.objects.first()

        # coverage
        self.assertTrue(str(poule) != "")

        # bad deelcomp
        bad_url = self.url_regio_poules % 999999
        resp = self.client.get(bad_url)
        self.assert404(resp, 'Competitie niet gevonden')
        resp = self.client.post(bad_url)
        self.assert404(resp, 'Competitie niet gevonden')

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
        self.assert_template_used(resp, ('complaagregio/wijzig-poule.dtl', 'design/site_layout.dtl'))

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
        self.assert404(resp, 'Poule bestaat niet')
        resp = self.client.post(bad_url)
        self.assert404(resp, 'Poule bestaat niet')

        # verkeerde beheerder
        poule.regiocompetitie = self.deelcomp_regio101_25
        poule.save(update_fields=['regiocompetitie'])
        bad_url = self.url_wijzig_poule % poule.pk
        resp = self.client.get(bad_url)
        self.assert403(resp)
        resp = self.client.post(bad_url)
        self.assert403(resp)
        poule.regiocompetitie = self.deelcomp_regio112_18
        poule.save(update_fields=['regiocompetitie'])

        # overzicht poules
        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # vanaf fase F mag je nog steeds wijzigen zolang ronde 1 niet opgestart is
        comp = deelcomp.competitie
        zet_competitie_fase_regio_wedstrijden(comp)         # fase F

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-teams-poules.dtl', 'design/site_layout.dtl'))

        # bad: maak een poule aan
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(2, RegiocompetitieTeamPoule.objects.count())

        # wijzig de poule
        url = self.url_wijzig_poule % poule.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-poule.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'beschrijving': 'test'})
        self.assert_is_redirect_not_plein(resp)

        # vanaf ronde 1 actief mag je niet meer wijzigen
        deelcomp.huidige_team_ronde = 1
        deelcomp.save(update_fields=['huidige_team_ronde'])

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-teams-poules.dtl', 'design/site_layout.dtl'))

        # bad: maak een poule aan
        self.assertEqual(2, RegiocompetitieTeamPoule.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Poules kunnen niet meer aangepast worden')
        self.assertEqual(2, RegiocompetitieTeamPoule.objects.count())

        # poule details (wijzig scherm, read-only)
        url = self.url_wijzig_poule % poule.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-poule.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'beschrijving': 'nieuwe test'})
        self.assert_is_redirect_not_plein(resp)

        # TODO: controleer dat de teams gekoppeld aan de poule niet meer te wijzigen zijn

        # zet fase G, dan mag niets meer gewijzigd worden
        zet_competitie_fase_regio_afsluiten(comp)

        # kijken mag altijd nog
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-poule.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'beschrijving': 'nieuwe test'})
        self.assert_is_redirect_not_plein(resp)

        # terug naar fase D
        comp = deelcomp.competitie
        zet_competitie_fases(comp, 'C', 'D')

        # verwijder een poule
        self.assertEqual(2, RegiocompetitieTeamPoule.objects.count())
        url = self.url_wijzig_poule % poule.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_poule': 'aj'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())

    def test_poules_teams(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        # maak een poule aan
        deelcomp = Regiocompetitie.objects.get(competitie=self.comp_18, functie=self.functie_rcl112_18)

        # tot en met fase D mag alles nog
        comp = deelcomp.competitie
        zet_competitie_fase_regio_inschrijven(comp)

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, RegiocompetitieTeamPoule.objects.count())
        poule = RegiocompetitieTeamPoule.objects.first()

        # maak 9 teams aan
        type_r = TeamType.objects.get(afkorting='R2')
        klasse_r_ere = CompetitieTeamKlasse.objects.filter(team_type=type_r).order_by('volgorde')[0]
        for lp in range(9):
            # team zonder sporters maar wel in een klasse is genoeg voor een poule
            RegiocompetitieTeam(
                    regiocompetitie=deelcomp,
                    vereniging=self.ver_112,
                    volg_nr=lp + 1,
                    team_type=type_r,
                    team_naam='Recurve Testers %s' % (lp + 1),
                    team_klasse=klasse_r_ere).save()
        # for
        team_pks = list(RegiocompetitieTeam.objects.values_list('pk', flat=True))

        # maak een compound team aan
        type_c = TeamType.objects.get(afkorting='C')
        klasse_c_ere = CompetitieTeamKlasse.objects.filter(team_type=type_c).order_by('volgorde')[0]
        team_c = RegiocompetitieTeam(
                        regiocompetitie=deelcomp,
                        vereniging=self.ver_112,
                        volg_nr=1,
                        team_type=type_c,
                        team_naam='Compound Testers 9',
                        team_klasse=klasse_c_ere)
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
        self.assert_template_used(resp, ('complaagregio/wijzig-poule.dtl', 'design/site_layout.dtl'))

        # compound team heeft prio indien bij recurve team gestopt
        params['team_%s' % team_c.pk] = 1
        with self.assert_max_queries(20):
            resp = self.client.post(url, params)
        self.assert_is_redirect_not_plein(resp)
        poule = RegiocompetitieTeamPoule.objects.prefetch_related('teams').get(pk=poule.pk)
        self.assertEqual(1, poule.teams.count())

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

        # CLI test: Formule1 wedstrijdpunten
        deelcomp.regio_team_punten_model = TEAM_PUNTEN_MODEL_FORMULE1
        deelcomp.save(update_fields=['regio_team_punten_model'])

        # maak een RegiocompetitieRondeTeam aan
        teams = poule.teams.all()
        bulk = list()
        for team in teams:
            bulk.extend([
                RegiocompetitieRondeTeam(team=team, ronde_nr=1, team_score=5, team_punten=5),  # triggert melding
                RegiocompetitieRondeTeam(team=team, ronde_nr=2, team_score=5, team_punten=team.pk),
                RegiocompetitieRondeTeam(team=team, ronde_nr=3)])
        # for
        RegiocompetitieRondeTeam.objects.bulk_create(bulk)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(22):
            management.call_command('check_wp_f1', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('[WARNING] ' in f2.getvalue())

# end of file
