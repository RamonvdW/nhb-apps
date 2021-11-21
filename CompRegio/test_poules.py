# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType, TeamType
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse, LAAG_BK, LAAG_RK, LAAG_REGIO,
                               RegiocompetitieTeam, RegiocompetitieTeamPoule)
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


class TestCompRegioPoules(E2EHelpers, TestCase):

    """ tests voor de CompRegio applicatie, Poules functie """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    url_regio_poules = '/bondscompetities/regio/poules/%s/'         # deelcomp_pk
    url_wijzig_poule = '/bondscompetities/regio/poules/wijzig/%s/'  # poule_pk

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
                                              team__volgorde=10,
                                              is_voor_teams_rk_bk=False)
        klasse.min_ag = 29.0
        klasse.save()

        klasse = CompetitieKlasse.objects.get(competitie=self.comp_18,
                                              team__volgorde=11,
                                              is_voor_teams_rk_bk=False)
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

    def test_poules_basic(self):
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        deelcomp = DeelCompetitie.objects.get(competitie=self.comp_18, functie=self.functie_rcl112_18)

        url = self.url_regio_poules % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compregio/rcl-teams-poules.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('compregio/wijzig-poule.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('compregio/rcl-teams-poules.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('compregio/wijzig-poule.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('compregio/wijzig-poule.dtl', 'plein/site_layout.dtl'))

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

# end of file
