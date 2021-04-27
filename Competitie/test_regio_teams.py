# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamType
from Competitie.test_fase import zet_competitie_fase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Wedstrijden.models import WedstrijdLocatie
from Overig.e2ehelpers import E2EHelpers
from .models import (Competitie, DeelCompetitie, CompetitieKlasse,
                     competitie_aanmaken,
                     RegioCompetitieSchutterBoog,
                     RegiocompetitieTeam)
import datetime


class TestCompetitieRegioTeams(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    def _prep_beheerder_lid(self, voornaam):
        nhb_nr = self._next_nhbnr
        self._next_nhbnr += 1

        lid = NhbLid()
        lid.nhb_nr = nhb_nr
        lid.geslacht = "M"
        lid.voornaam = voornaam
        lid.achternaam = "Tester"
        lid.email = voornaam.lower() + "@nhb.test"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = self.nhbver_101
        lid.save()

        return self.e2e_create_account(nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.account_admin = self.e2e_create_account_admin()

        self._next_nhbnr = 100001

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

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL101')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL101-25')
        self.account_rcl112_18 = self._prep_beheerder_lid('RCL112')
        self.account_schutter = self._prep_beheerder_lid('Schutter')
        self.lid_schutter = NhbLid.objects.get(nhb_nr=self.account_schutter.username)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.schutterboog = SchutterBoog(nhblid=self.lid_schutter,
                                         boogtype=self.boog_r,
                                         voor_wedstrijd=True)
        self.schutterboog.save()

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # een parallel competitie is noodzakelijk om corner-cases te raken
        competitie_aanmaken(jaar=2020)

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.account_bb)
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

        self.deelcomp_bond_18 = DeelCompetitie.objects.filter(laag='BK', competitie=self.comp_18)[0]
        self.deelcomp_rayon1_18 = DeelCompetitie.objects.filter(laag='RK', competitie=self.comp_18, nhb_rayon=self.rayon_1)[0]
        self.deelcomp_rayon2_18 = DeelCompetitie.objects.filter(laag='RK', competitie=self.comp_18, nhb_rayon=self.rayon_2)[0]
        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_25, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio112_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_112)[0]

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

        self.url_afsluiten_regio = '/bondscompetities/planning/regio/%s/afsluiten/'     # deelcomp_pk
        self.url_regio_instellingen = '/bondscompetities/%s/instellingen/regio-%s/'     # comp_pk, regio-nr
        self.url_ag_controle = '/bondscompetities/%s/ag-controle/regio-%s/'             # comp_pk, regio-nr
        self.url_regio_teams = '/bondscompetities/regio/%s/teams/'                      # deelcomp_pk
        self.url_regio_poules = '/bondscompetities/regio/%s/poules/'                    # deelcomp_pk

    def _maak_inschrijving(self, deelcomp):
        RegioCompetitieSchutterBoog(schutterboog=self.schutterboog,
                                    bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                    deelcompetitie=deelcomp,
                                    klasse=self.klasse_recurve_onbekend).save()

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
            resp = self.client.post(url, {'teams': 'nee',
                                          'einde_teams_aanmaken': post_datum_bad})
        self.assert404(resp)  # 404 = Not allowed

        # bad date
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'einde_teams_aanmaken': 'xxx'})
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
                schutterboog=self.schutterboog,
                bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
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


# end of file
