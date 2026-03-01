# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import INSCHRIJF_METHODE_1
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMatch,
                               Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog)
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_wedstrijden, zet_competitie_fase_regio_afsluiten
from CompLaagBond.models import KampBK
from CompLaagRayon.models import KampRK
from CompLaagRegio.view_planning import competitie_week_nr_to_date
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio, Cluster
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Taken.models import Taak
from Vereniging.models import Vereniging
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime
import json


class TestCompLaagRegioPlanning(E2EHelpers, TestCase):

    """ tests voor de CompLaagRegio applicatie, Planning functie """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_planning_bond = '/bondscompetities/bk/planning/%s/'                                 # deelkamp_pk
    url_planning_rayon = '/bondscompetities/rk/planning/%s/'                                # deelkamp_pk
    url_planning_regio = '/bondscompetities/regio/planning/%s/'                             # deelcomp_pk
    url_planning_regio_cluster = '/bondscompetities/regio/planning/%s/cluster/%s/'          # deelcomp_pk, cluster_pk
    url_planning_regio_ronde = '/bondscompetities/regio/planning/ronde/%s/'                 # ronde_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/regio/planning/regio-wedstrijden/%s/'  # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/wijzig/%s/'          # match_pk
    url_verwijder_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/verwijder/%s/'    # match_pk
    url_score_invoeren = '/bondscompetities/scores/uitslag-invoeren/%s/'                    # match_pk
    url_uitslag_opslaan = '/bondscompetities/scores/dynamic/scores-opslaan/'
    url_afsluiten_regio = '/bondscompetities/regio/planning/%s/afsluiten/'                  # deelcomp_pk
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

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # een parallelle competitie is noodzakelijk om corner-cases te raken
        competities_aanmaken(jaar=2020)

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen_18 = self.url_klassengrenzen_vaststellen % self.comp_18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)  # check for success

        klasse = CompetitieTeamKlasse.objects.get(competitie=self.comp_18,
                                                  volgorde=15,                  # Rec ERE
                                                  is_voor_teams_rk_bk=False)
        klasse.min_ag = 29.0
        klasse.save()

        klasse = CompetitieTeamKlasse.objects.get(competitie=self.comp_18,
                                                  volgorde=16,                  # Rec A
                                                  is_voor_teams_rk_bk=False)
        klasse.min_ag = 25.0
        klasse.save()

        self.client.logout()

        self.klasse_recurve_onbekend = (CompetitieIndivKlasse
                                        .objects
                                        .filter(competitie=self.comp_18,
                                                boogtype=self.boog_r,
                                                is_onbekend=True)
                                        .all())[0]

        self.deelcomp_bond_18 = KampBK.objects.filter(competitie=self.comp_18).first()
        self.deelcomp_rayon1_18 = KampRK.objects.filter(competitie=self.comp_18, rayon=self.rayon_1).first()
        self.deelcomp_rayon2_18 = KampRK.objects.filter(competitie=self.comp_18, rayon=self.rayon_2).first()
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

    def _maak_inschrijving(self, deelcomp):
        RegiocompetitieSporterBoog(sporterboog=self.sporterboog,
                                   bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                   regiocompetitie=deelcomp,
                                   indiv_klasse=self.klasse_recurve_onbekend).save()

    def test_overzicht_anon(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                      self.cluster_101a_18.pk))
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % 0)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_wedstrijd % 0)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_verwijder_wedstrijd % 0)
        self.assert403(resp)      # not allowed

    def test_overzicht_bb(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/planning-landelijk.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/planning-rayon.dtl', 'design/site_layout.dtl'))
        # TODO: check geen knoppen 'wedstrijd toevoegen' of 'aanpassen wedstrijd'

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                      self.cluster_101a_18.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-cluster.dtl', 'design/site_layout.dtl'))

    def test_overzicht_bko(self):
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/planning-landelijk.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/planning-rayon.dtl', 'design/site_layout.dtl'))
        # TODO: check geen knoppen 'wedstrijd toevoegen' of 'aanpassen wedstrijd'

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                      self.cluster_101a_18.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-cluster.dtl', 'design/site_layout.dtl'))

        # check dat de BKO geen wijzigingen mag maken
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                       self.cluster_101a_18.pk))
        self.assert403(resp)

    def test_overzicht_rko(self):
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/planning-rayon.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                      self.cluster_101a_18.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-cluster.dtl', 'design/site_layout.dtl'))

        # check dat de RKO geen wijzigingen mag maken
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                       self.cluster_101a_18.pk))
        self.assert403(resp)

    def test_overzicht_rcl(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio.dtl', 'design/site_layout.dtl'))

        url = self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk, self.cluster_101a_18.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-cluster.dtl', 'design/site_layout.dtl'))

        # maak een planning aan
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

    def test_wk53(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # pas het jaartal van de competitie aan zodat wk53 bestaat
        self.comp_18.begin_jaar = 2020
        self.comp_18.save()

        # maak een ronde aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success

        ronde = RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_18)[0]
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # herhaal voor de 25m1p
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success

        ronde = RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_25)[0]
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

    def test_overzicht_hwl(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assert403(resp)      # not allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                      self.cluster_101a_18.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-cluster.dtl', 'design/site_layout.dtl'))

        # check dat de HWL geen wijzigingen mag maken
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                       self.cluster_101a_18.pk))
        self.assert403(resp)

    def test_protection(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # niet bestaande pk's
        resp = self.client.get(self.url_planning_bond % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_planning_rayon % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_planning_regio % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk, 999999))
        self.assert404(resp, 'Cluster niet gevonden')

        resp = self.client.get(self.url_planning_regio_cluster % (999999, self.cluster_101a_18.pk))
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_planning_regio_ronde % 999999)
        self.assert404(resp, 'Ronde niet gevonden')

        resp = self.client.post(self.url_planning_regio_ronde % 99999)
        self.assert404(resp, 'Ronde niet gevonden')

        # verkeerde laag
        resp = self.client.get(self.url_planning_bond % self.deelcomp_rayon2_18.pk)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_bond_18.pk)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_planning_regio % self.deelcomp_bond_18.pk)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_planning_bond % self.deelcomp_bond_18.pk
        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # wissel naar RCL voor meer rechten
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        resp = self.client.post(self.url_planning_regio % 99999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_planning_regio_ronde % 99999)
        self.assert404(resp, 'Ronde niet gevonden')

        resp = self.client.post(self.url_planning_regio % self.deelcomp_bond_18.pk)
        self.assert404(resp, 'Competitie niet gevonden')

        # illegaal cluster nummer
        resp = self.client.post(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk, 999999))
        self.assert404(resp, 'Cluster niet gevonden')

        # illegale regiocompetitie
        resp = self.client.post(self.url_planning_regio_cluster % (999999, self.cluster_101a_18.pk))
        self.assert404(resp, 'Competitie niet gevonden')

    def test_rcl_maakt_planning_18(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # schrijf 1 schutter in
        self._maak_inschrijving(self.deelcomp_regio101_18)

        # maak een ronde aan
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 1)

        # verwijder de ronde weer
        ronde = RegiocompetitieRonde.objects.first()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde.pk,
                                    {'verwijder_ronde': 1})
        self.assert_is_redirect(resp, self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)

        # maak een ronde aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 1)
        ronde = RegiocompetitieRonde.objects.first()
        ronde_pk = ronde.pk
        self.assertTrue(str(ronde) != '')

        # haal de ronde planning op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-ronde.dtl', 'design/site_layout.dtl'))

        # pas de instellingen aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 50,
                                     'ronde_naam': 'eerste rondje is gratis'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_18.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # check dat ronde settings in de database geland zijn
        ronde = RegiocompetitieRonde.objects.get(pk=ronde_pk)
        self.assertEqual(ronde.regiocompetitie, self.deelcomp_regio101_18)
        self.assertEqual(ronde.week_nr, 50)
        self.assertEqual(ronde.beschrijving, 'eerste rondje is gratis')

        # nog een post met dezelfde resultaten
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 50,
                                     'ronde_naam': 'eerste rondje is gratis'})
        self.assert_is_redirect(resp, url_regio_planning)

        # illegale week nummers
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 'x'})
        self.assert404(resp, 'Geen valide week nummer')

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 0})
        self.assert404(resp, 'Geen valide week nummer')

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 99})
        self.assert404(resp, 'Geen valide week nummer')

        # weken tussen de competitie blokken
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': settings.COMPETITIE_18M_LAATSTE_WEEK})
        self.assert_is_redirect_not_plein(resp)  # check for success

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': settings.COMPETITIE_18M_LAATSTE_WEEK + 1})
        self.assert404(resp, 'Geen valide week nummer')

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': settings.COMPETITIES_START_WEEK - 1})
        self.assert404(resp, 'Geen valide week nummer')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': settings.COMPETITIES_START_WEEK})
        self.assert_is_redirect_not_plein(resp)  # check for success

        # terug naar de standaard week voor de rest van de tests
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 50,
                                     'ronde_naam': 'eerste rondje is gratis'})
        self.assert_is_redirect(resp, url_regio_planning)

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(CompetitieMatch.objects.count(), 1)
        match_pk = CompetitieMatch.objects.first().pk

        # probeer de ronde te verwijderen terwijl er wedstrijden aan hangen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'verwijder_ronde': 1})
        self.assert404(resp, 'Wedstrijden aanwezig')

        # wijziging van week --> wijzigt wedstrijd datums met hetzelfde aantal dagen
        wedstrijd_datum = CompetitieMatch.objects.get(pk=match_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-12-09")
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 40,
                                     'ronde_naam': 'tweede rondje gaat snel'})
        self.assert_is_redirect(resp, url_regio_planning)
        wedstrijd_datum = CompetitieMatch.objects.get(pk=match_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-09-30")

        # haal de wedstrijd op
        with self.assert_max_queries(26):
            resp = self.client.get(self.url_wijzig_wedstrijd % match_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-wedstrijd.dtl', 'design/site_layout.dtl'))

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_wedstrijd % 99999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # haal de planning op, met de 'wijzig' knoppen voor de wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # wissel naar HWL en haal planning op
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-ronde.dtl', 'design/site_layout.dtl'))

        # probeer een wijziging te doen als HWL
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 51, 'ronde_naam': 'eerste rondje is gratis'})
        self.assert403(resp)

    def test_rcl_maakt_planning_25(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        # schrijf 1 schutter in
        self._maak_inschrijving(self.deelcomp_regio101_25)

        # maak een ronde aan
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 1)

        ronde = RegiocompetitieRonde.objects.first()
        ronde_pk = ronde.pk
        self.assertTrue(str(ronde) != '')

        # haal de ronde planning op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-ronde.dtl', 'design/site_layout.dtl'))

        # pas de instellingen aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 50,
                                     'ronde_naam': 'eerste rondje is gratis'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_25.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # check dat ronde settings in de database geland zijn
        ronde = RegiocompetitieRonde.objects.get(pk=ronde_pk)
        self.assertEqual(ronde.regiocompetitie, self.deelcomp_regio101_25)
        self.assertEqual(ronde.week_nr, 50)
        self.assertEqual(ronde.beschrijving, 'eerste rondje is gratis')

        # nog een post met dezelfde resultaten
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 50,
                                     'ronde_naam': 'eerste rondje is gratis'})
        self.assert_is_redirect(resp, url_regio_planning)

        # weken tussen de competitie blokken
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': settings.COMPETITIE_25M_LAATSTE_WEEK})
        self.assert_is_redirect_not_plein(resp)  # check for success

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': settings.COMPETITIE_25M_LAATSTE_WEEK + 1})
        self.assert404(resp, 'Geen valide week nummer')

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': settings.COMPETITIES_START_WEEK - 1})
        self.assert404(resp, 'Geen valide week nummer')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': settings.COMPETITIES_START_WEEK})
        self.assert_is_redirect_not_plein(resp)  # check for success

        # terug naar de standaard week voor de rest van de tests
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 50,
                                     'ronde_naam': 'eerste rondje is gratis'})
        self.assert_is_redirect(resp, url_regio_planning)

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(CompetitieMatch.objects.count(), 1)
        match_pk = CompetitieMatch.objects.first().pk

        # wijziging van week --> wijzigt wedstrijd datums met hetzelfde aantal dagen
        wedstrijd_datum = CompetitieMatch.objects.get(pk=match_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-12-09")
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 7,
                                     'ronde_naam': 'tweede rondje gaat snel'})
        self.assert_is_redirect(resp, url_regio_planning)
        wedstrijd_datum = CompetitieMatch.objects.get(pk=match_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2020-02-10")

        # haal de wedstrijd op
        with self.assert_max_queries(26):
            resp = self.client.get(self.url_wijzig_wedstrijd % match_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-wedstrijd.dtl', 'design/site_layout.dtl'))

    def test_rcl_maakt_planning_25_methode1(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        # zet deze regiocompetitie op inschrijfmethode 1
        self.deelcomp_regio101_25.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio101_25.save()

        url = self.url_planning_regio % self.deelcomp_regio101_25.pk

        # haal de (lege) planning op
        self.assertEqual(RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_25).count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-methode1.dtl', 'design/site_layout.dtl'))
        self.assertEqual(RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_25).count(), 0)

        # doe een POST om de eerste ronde aan te maken
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(RegiocompetitieRonde.objects.count(), 2)

        # probeer nog een ronde aan te maken
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(RegiocompetitieRonde.objects.count(), 2)

        # haal de planning op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-methode1.dtl', 'design/site_layout.dtl'))

        ronde_pk = RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_25)[0].pk

        # haal de planning op (nu is de ronde er al)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-methode1.dtl', 'design/site_layout.dtl'))

        # haal de ronde planning op
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url_ronde)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-ronde-methode1.dtl', 'design/site_layout.dtl'))

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)
        self.assertTrue(self.url_wijzig_wedstrijd[:-3] in resp.url)     # [:-3] cuts off %s/
        self.assertEqual(CompetitieMatch.objects.count(), 1)

        match_pk = CompetitieMatch.objects.first().pk

        # haal de planning op MET een wedstrijd erin
        with self.assert_max_queries(20):
            resp = self.client.get(url_ronde)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # haal de wedstrijd op
        url_wed = self.url_wijzig_wedstrijd % match_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url_wed)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-wedstrijd.dtl', 'design/site_layout.dtl'))

        # wijzig de datum van deze wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.post(url_wed)
        self.assert404(resp, 'Geen valide verzoek')

        with self.assert_max_queries(20):
            resp = self.client.post(url_wed, {'ver_pk': self.ver_101.pk,
                                              'wanneer': 'garbage', 'aanvang': '12:34'})
        self.assert404(resp, 'Geen valide datum')

        with self.assert_max_queries(20):
            resp = self.client.post(url_wed, {'ver_pk': self.ver_101.pk,
                                              'aanvang': '12:34'})
        self.assert404(resp, 'Verzoek is niet compleet')

        with self.assert_max_queries(20):
            resp = self.client.post(url_wed, {'ver_pk': self.ver_101.pk,
                                              'wanneer': '2013-12-11', 'aanvang': '12:34'})
        self.assert_is_redirect(resp, url_ronde)

        match = CompetitieMatch.objects.get(pk=match_pk)
        real = (match.datum_wanneer.year, match.datum_wanneer.month, match.datum_wanneer.day)
        self.assertEqual(real, (2013, 12, 11))

        # verwijder een wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_verwijder_wedstrijd % match_pk, {})
        self.assert_is_redirect_not_plein(resp)

        # haal de ronde planning op met een andere rol
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(url_ronde)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

    def test_rcl_maakt_planning_18_methode1(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # zet deze regiocompetitie op inschrijfmethode 1
        self.deelcomp_regio101_18.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio101_18.save()

        url = self.url_planning_regio % self.deelcomp_regio101_18.pk

        # haal de (lege) planning op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-methode1.dtl', 'design/site_layout.dtl'))

        # doe een POST om de eerste ronde aan te maken
        self.assertEqual(0, RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_18).count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

        ronde_pk = RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_18).first().pk
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)
        self.assertTrue(self.url_wijzig_wedstrijd[:-3] in resp.url)     # [:-3] cuts off %s/
        self.assertEqual(CompetitieMatch.objects.count(), 1)

        match_pk = CompetitieMatch.objects.first().pk

        # haal de wedstrijd op
        url_wed = self.url_wijzig_wedstrijd % match_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url_wed)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-wedstrijd.dtl', 'design/site_layout.dtl'))

    def test_methode1_bad(self):
        # anon
        self.client.logout()
        url = self.url_planning_regio % self.deelcomp_regio101_25.pk
        resp = self.client.get(url)
        self.assert403(resp)

        # zet deze regiocompetitie op inschrijfmethode 1
        self.deelcomp_regio101_25.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio101_25.save()

        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        # haal de (lege) planning op.
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # doe een POST om de eerste ronde aan te maken
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(RegiocompetitieRonde.objects.count(), 2)

        url_ronde = self.url_planning_regio_ronde_methode1 % 999999
        resp = self.client.get(url_ronde)
        self.assert404(resp, 'Ronde niet gevonden')

        resp = self.client.post(url_ronde)
        self.assert404(resp, 'Ronde niet gevonden')

        # als niet-RCL een wedstrijd aan proberen te maken
        self.e2e_wissel_naar_functie(self.functie_hwl)
        ronde_pk = RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio101_25)[0].pk
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk
        resp = self.client.post(url_ronde)
        self.assert403(resp)

        self.e2e_wissel_naar_functie(self.functie_wl)
        resp = self.client.get(url_ronde)
        self.assert403(resp)

    def test_maak_max_rondes(self):
        # wissel naar RCL functie
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.deelcomp_regio101_18.functie)
        self.e2e_check_rol('RCL')

        # maak 16 'handmatige' rondes aan
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        for _ in range(16):
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
            self.assert_is_redirect_not_plein(resp)  # check for success
        # for
        self.assertEqual(RegiocompetitieRonde.objects.count(), 16)

        # controleer dat de 11e ronde niet aangemaakt mag worden
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert404(resp, 'Limiet bereikt')
        self.assertEqual(RegiocompetitieRonde.objects.count(), 16)

    def test_rcl_maakt_cluster_planning(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # maak een eerste ronde-planning aan voor een cluster
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                       self.cluster_101a_18.pk))
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 1)

        ronde = RegiocompetitieRonde.objects.first()
        ronde_pk = ronde.pk
        self.assertTrue(str(ronde) != '')

        # haal de ronde planning op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-ronde.dtl', 'design/site_layout.dtl'))

        # pas de instellingen van de ronde (van een cluster) aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 50,
                                     'ronde_naam': 'eerste rondje is gratis'})
        url_cluster_planning = self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                  self.cluster_101a_18.pk)
        self.assert_is_redirect(resp, url_cluster_planning)

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(CompetitieMatch.objects.count(), 1)
        match_pk = CompetitieMatch.objects.first().pk

        # haal informatie over de wedstrijd (binnen het cluster) op
        # haal de wedstrijd op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_wedstrijd % match_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wijzig-wedstrijd.dtl', 'design/site_layout.dtl'))

        # stop een vereniging in het cluster
        self.ver_101.clusters.add(self.cluster_101a_18)

        # haal de regioplanning op, inclusief de clusterplanning
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # haal de cluster planning op, inclusief telling wedstrijden in een ronde
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_cluster % (self.deelcomp_regio101_18.pk,
                                                                      self.cluster_101a_18.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_wijzig_wedstrijd_18(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        self._maak_inschrijving(self.deelcomp_regio101_18)

        # maak een regioplanning aan
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 1)
        ronde_pk = RegiocompetitieRonde.objects.first().pk

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(CompetitieMatch.objects.count(), 1)
        match_pk = CompetitieMatch.objects.first().pk

        # pas de instellingen van de wedstrijd aan
        with self.assert_max_queries(21):
            resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                    {'weekdag': 1, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34',
                                     'wkl_indiv_%s' % self.klasse_recurve_onbekend.pk: 'on'})
        self.assert_is_redirect_not_plein(resp)  # check for success

        # nog een keer hetzelfde
        with self.assert_max_queries(21):
            resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                    {'weekdag': 1, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34',
                                     'wkl_indiv_%s' % self.klasse_recurve_onbekend.pk: 'on'})
        self.assert_is_redirect_not_plein(resp)  # check for success

        # haal het ronde overzicht op met daarin de wedstrijdklassen genoemd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # koppel de wedstrijdklasse weer los
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                    {'weekdag': 1, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34'})
        self.assert_is_redirect_not_plein(resp)  # check for success

        wedstrijd = CompetitieMatch.objects.get(pk=match_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(wedstrijd.vereniging.ver_nr, self.ver_101.ver_nr)

        with self.assert_max_queries(24):
            resp = self.client.get(self.url_wijzig_wedstrijd % match_pk)
        self.assertEqual(resp.status_code, 200)

        # pas een niet-bestaande wedstrijd aan
        resp = self.client.post(self.url_wijzig_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # lever slechte argumenten
        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': '', 'ver_pk': 'x', 'aanvang': 'xx:xx'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 'x', 'ver_pk': '', 'aanvang': 'xx:xx'})
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 'x', 'ver_pk': 'x', 'aanvang': 'xx:x'})
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 'x', 'ver_pk': 'x', 'aanvang': 'xxxxx'})        # noqa
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 'x', 'ver_pk': 'x', 'aanvang': '10:20'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': '9', 'ver_pk': '0', 'aanvang': '10:20'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': '0', 'ver_pk': '0', 'aanvang': '07:59'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': '0', 'ver_pk': '0', 'aanvang': '22:01'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': '0', 'ver_pk': '0', 'aanvang': '12:60'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': '0', 'ver_pk': '0', 'aanvang': '12:-1'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 1, 'ver_pk': 9999999, 'aanvang': '12:34'})
        self.assert404(resp, 'Vereniging niet gevonden')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 1, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34',
                                 'wkl_indiv_999999': 'on'})
        self.assert404(resp, 'Geen valide individuele klasse')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 1, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34',
                                 'wkl_indiv_x': 'on'})
        self.assert404(resp, 'Geen valide individuele klasse')

        # probeer een wijziging te doen als HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_wedstrijd % match_pk)
        self.assert403(resp)

        # probeer te wijzigen als RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_wedstrijd % match_pk)
        self.assert403(resp)

        # probeer te wijzigen als BKO
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_wedstrijd % match_pk)
        self.assert403(resp)

    def test_wijzig_wedstrijd_25(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        # haal de vereniging uit de locatie
        self.loc.verenigingen.remove(self.ver_101)

        # maak een regioplanning aan
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 1)
        ronde_pk = RegiocompetitieRonde.objects.first().pk

        # pas de instellingen van de ronde aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 5, 'ronde_naam': 'laatste inhaalronde'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_25.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(CompetitieMatch.objects.count(), 1)
        match_pk = CompetitieMatch.objects.first().pk

        wedstrijd = CompetitieMatch.objects.get(pk=match_pk)
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-27')

        # pas de instellingen van de wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                    {'weekdag': 0, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34'})
        self.assert_is_redirect_not_plein(resp)  # check for success

        wedstrijd = CompetitieMatch.objects.get(pk=match_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-27')

        # pas de weekdag aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                    {'weekdag': 2, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34'})
        self.assert_is_redirect_not_plein(resp)  # check for success

        wedstrijd = CompetitieMatch.objects.get(pk=match_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-29')

        # probeer met een slecht tijdstip
        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 2, 'ver_pk': self.ver_101.pk, 'aanvang': 'AB:CD'})
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 2, 'ver_pk': self.ver_101.pk, 'aanvang': '14:60'})
        self.assert404(resp, 'Geen valide tijdstip')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 2, 'ver_pk': self.ver_101.pk, 'aanvang': '-1:00'})
        self.assert404(resp, 'Geen valide tijdstip')

        # probeer met een slechte weekdag
        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'ver_pk': self.ver_101.pk, 'aanvang': '12:34'})
        self.assert404(resp, 'Geen valide weekdag')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': '#', 'ver_pk': self.ver_101.pk, 'aanvang': '12:34'})
        self.assert404(resp, 'Geen valide weekdag')

        resp = self.client.post(self.url_wijzig_wedstrijd % match_pk,
                                {'weekdag': 7, 'ver_pk': self.ver_101.pk, 'aanvang': '12:34'})
        self.assert404(resp, 'Geen valide weekdag')

    def test_verwijder_wedstrijd(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # maak een regioplanning aan
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 1)
        ronde_pk = RegiocompetitieRonde.objects.first().pk

        # pas de instellingen van de ronde aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                    {'ronde_week_nr': 45, 'ronde_naam': 'laatste inhaalronde'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_18.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(CompetitieMatch.objects.count(), 1)
        match_pk = CompetitieMatch.objects.first().pk

        # haal de wijzig-wedstrijd pagina op
        url = self.url_wijzig_wedstrijd % match_pk
        with self.assert_max_queries(25):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp, skip_menu=True)
        verwijder_url = self.url_verwijder_wedstrijd % match_pk
        self.assertIn(verwijder_url, urls)

        # verwijder de wedstrijd
        url = self.url_verwijder_wedstrijd % match_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert405(resp)     # GET bestaat niet
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # maak een wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        match_pk = CompetitieMatch.objects.latest('pk').pk

        # maak de data set
        json_data = {'wedstrijd_pk': match_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        json_data = self.assert200_json(resp)
        self.assertEqual(json_data['done'], 1)

        # hang er een score aan
        wed = CompetitieMatch.objects.get(pk=match_pk)
        wed.uitslag.is_bevroren = True
        wed.uitslag.save()

        # haal de wijzig-wedstrijd pagina op
        url = self.url_wijzig_wedstrijd % match_pk
        with self.assert_max_queries(26):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp, skip_menu=True)
        verwijder_url = self.url_verwijder_wedstrijd % match_pk
        self.assertNotIn(verwijder_url, urls)

        # probeer de wedstrijd met uitslag te verwijderen (mag niet)
        url = self.url_verwijder_wedstrijd % match_pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Uitslag mag niet meer gewijzigd worden')

        wed.uitslag.is_bevroren = False
        wed.uitslag.save()

        # probeer te verwijderen als RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # verwijder een niet bestaande wedstrijd
        resp = self.client.post(self.url_verwijder_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # verwijder als 'verkeerde' RCL
        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # verwijder de wedstrijd die niet meer bevroren is
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # redirect naar regioplanning

    def test_competitie_week_nr_to_date(self):
        # test een paar corner-cases

        # 2019wk52 = 2019-12-23
        when = competitie_week_nr_to_date(2019, 52)
        self.assertEqual(when.year, 2019)
        self.assertEqual(when.month, 12)
        self.assertEqual(when.day, 23)

        # 2020wk1 = 2019-12-30
        when = competitie_week_nr_to_date(2019, 1)
        self.assertEqual(when.year, 2019)
        self.assertEqual(when.month, 12)
        self.assertEqual(when.day, 30)

        # 2019wk53 bestaat niet, dus gelijk aan 2020wk1
        when1 = competitie_week_nr_to_date(2019, 53)
        self.assertEqual(when1, None)

        # 2020wk2 = 2020-01-06
        when = competitie_week_nr_to_date(2019, 2)
        self.assertEqual(when.year, 2020)
        self.assertEqual(when.month, 1)
        self.assertEqual(when.day, 6)

        # 2020 kent wel een wk53
        when1 = competitie_week_nr_to_date(2020, 53)
        when2 = competitie_week_nr_to_date(2020, 1)
        self.assertNotEqual(when1, when2)

    def test_sortering_week_nummers(self):
        # log in als RCL
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        url = self.url_planning_regio % self.deelcomp_regio101_25.pk

        # maak 4 rondes aan
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        self.client.post(url)
        self.client.post(url)
        self.client.post(url)
        self.client.post(url)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(RegiocompetitieRonde.objects.count(), 5)

        pks = [obj.pk for obj in RegiocompetitieRonde.objects.all()]

        ronde = RegiocompetitieRonde.objects.get(pk=pks[0])
        ronde.week_nr = 8
        ronde.beschrijving = 'Vierde'
        ronde.save()

        ronde = RegiocompetitieRonde.objects.get(pk=pks[1])
        ronde.week_nr = 40
        ronde.beschrijving = 'Eerste'
        ronde.save()

        ronde = RegiocompetitieRonde.objects.get(pk=pks[2])
        ronde.week_nr = 50
        ronde.beschrijving = 'Tweede een'
        ronde.save()

        # stop er ook meteen eenzelfde weeknummer in
        ronde = RegiocompetitieRonde.objects.get(pk=pks[4])
        ronde.week_nr = 50
        ronde.beschrijving = 'Tweede twee'
        ronde.save()

        ronde = RegiocompetitieRonde.objects.get(pk=pks[3])
        ronde.week_nr = 2
        ronde.beschrijving = 'Derde'
        ronde.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        html = self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio.dtl', 'design/site_layout.dtl'))

        # zoek alle weeknummers op
        parts = list()
        # zoek de tabel met de weeknummers
        html = html[html.find('<h4>Wedstrijd blokken</h4>'):]
        html = html[:html.find('<form>')]
        while len(html):
            pos = html.find('<tr><td class="center">')
            if pos < 0:
                html = ''
            else:
                html = html[pos+23:]
                pos = html.find('</td>')
                part = html[:pos]
                parts.append(part)
        # while

        self.assertEqual(parts, ['40', '50', '50', '2', '8'])

    def test_inschrijving_team(self):
        # ivm coverage
        boog_bb = BoogType.objects.get(afkorting='BB')
        sporterboog = SporterBoog(sporter=self.lid_sporter,
                                  boogtype=boog_bb,
                                  voor_wedstrijd=True)
        sporterboog.save()

        inschrijving = RegiocompetitieSporterBoog(
                            sporterboog=sporterboog,
                            bij_vereniging=sporterboog.sporter.bij_vereniging,
                            regiocompetitie=self.deelcomp_regio101_18,
                            indiv_klasse=self.klasse_recurve_onbekend)
        # inschrijving.save()

        self.assertTrue(str(inschrijving) != "")

    def test_buiten_eigen_regio(self):
        # RCL probeert wedstrijd toe te voegen en wijzigen buiten eigen regio
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        # maak een regioplanning aan in een andere regio
        url = self.url_planning_regio % self.deelcomp_regio101_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        # controleer dat er geen 'ronde toevoegen' knop is
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(url, urls)     # url wordt gebruikt voor POST

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # maak de eigen regioplanning aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio112_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        ronde_pk = RegiocompetitieRonde.objects.get(regiocompetitie=self.deelcomp_regio112_18).pk

        # maak een wedstrijd aan in de eigen regio
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assert_is_redirect_not_plein(resp)  # check for success
        ronde = RegiocompetitieRonde.objects.get(regiocompetitie=self.deelcomp_regio112_18)
        wedstrijd112_pk = ronde.matches.first().pk
        url = self.url_wijzig_wedstrijd % wedstrijd112_pk

        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # pas de instellingen van de wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 0,
                                          'aanvang': '12:34',
                                          'ver_pk': self.ver_101.pk})
        self.assert403(resp)

    def test_afsluiten_regio(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)
        url = self.url_afsluiten_regio % self.deelcomp_regio101_18.pk

        # nog niet afsluitbaar
        zet_competitie_fase_regio_wedstrijden(self.comp_18)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-afsluiten-regiocomp.dtl', 'design/site_layout.dtl'))

        # probeer afsluiten
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Verkeerde competitie fase')
        self.assertEqual(Taak.objects.count(), 0)

        # wel afsluitbaar
        zet_competitie_fase_regio_afsluiten(self.comp_18)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-afsluiten-regiocomp.dtl', 'design/site_layout.dtl'))
        hrefs = self.extract_all_urls(resp, skip_menu=True)
        self.assertGreater(len(hrefs), 0)
        self.assertEqual(hrefs[0], url)

        # echt afsluiten
        self.assertEqual(Taak.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success
        deelcomp = Regiocompetitie.objects.get(pk=self.deelcomp_regio101_18.pk)
        self.assertTrue(deelcomp.is_afgesloten)
        self.assertEqual(Taak.objects.count(), 1)       # RKO

        # get terwijl al afgesloten
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/rcl-afsluiten-regiocomp.dtl', 'design/site_layout.dtl'))

        # nogmaals afsluiten doet niets
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(Taak.objects.count(), 1)

    def test_bad_afsluiten_regio(self):
        self.client.logout()
        url = self.url_afsluiten_regio % 999999
        resp = self.client.get(url)
        self.assert403(resp)

        # verkeerde rol
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # verkeerde regio
        url = self.url_afsluiten_regio % self.deelcomp_regio112_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # niet bestaande pk
        url = self.url_afsluiten_regio % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')


# end of file
