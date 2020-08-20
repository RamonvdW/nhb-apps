# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Competitie.models import Competitie, competitie_aanmaken
from Wedstrijden.models import Wedstrijd
from Overig.e2ehelpers import E2EHelpers
from .models import Competitie, DeelCompetitie, DeelcompetitieRonde, competitie_aanmaken
import datetime


class TestCompetitieUitslagen(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, module Informatie over de Competitie """

    test_after = ('Competitie.test_planning',)

    def _prep_beheerder_lid(self, voornaam):
        nhb_nr = self._next_nhbnr
        self._next_nhbnr += 1

        lid = NhbLid()
        lid.nhb_nr = nhb_nr
        lid.geslacht = "M"
        lid.voornaam = voornaam
        lid.achternaam = "Tester"
        lid.email = voornaam.replace(' ', '_').lower() + "@nhb.test"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = self.nhbver
        lid.save()

        return self.e2e_create_account(nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.account_admin = self.e2e_create_account_admin()

        self._next_nhbnr = 100001

        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.nhb_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_rcl101 = self._prep_beheerder_lid('RCL 101')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')
        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_25, nhb_regio=self.regio_101)[0]

        self.cluster_101a = NhbCluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')

        self.functie_rcl101 = self.deelcomp_regio101_18.functie
        self.functie_rcl101.accounts.add(self.account_rcl101)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.url_planning_regio = '/competitie/planning/regiocompetitie/%s/'    # deelcomp_pk
        self.url_planning_regio_cluster = '/competitie/planning/regiocompetitie/cluster/%s/'    # cluster_pk
        self.url_planning_regio_ronde = '/competitie/planning/regiocompetitie/ronde/%s/'        # ronde_pk

        self.url_uitslag_invoeren = '/competitie/uitslagen-invoeren/wedstrijd/%s/'  # wedstrijd_pk
        self.url_uitslag_deelnemers = '/competitie/dynamic/deelnemers-ophalen/'
        self.url_uitslag_zoeken = '/competitie/dynamic/check-nhbnr/'
        self.url_uitslag_opslaan = '/competitie/dynamic/scores-opslaan/'

        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # maak een regioplanning aan
        self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        ronde18 = DeelcompetitieRonde.objects.all()[0]
        ronde25 = DeelcompetitieRonde.objects.all()[1]

        # maak een wedstrijd aan
        self.client.post(self.url_planning_regio_ronde % ronde18.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde25.pk, {})
        self.wedstrijd18_pk = Wedstrijd.objects.all()[0].pk
        self.wedstrijd25_pk = Wedstrijd.objects.all()[1].pk

    def test_anon(self):
        self.client.logout()
        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        # deelnemers
        resp = self.client.get(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        resp = self.client.post(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # zoeken
        resp = self.client.get(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        resp = self.client.post(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # opslaan
        resp = self.client.get(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        resp = self.client.post(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_get(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslag-invoeren-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # andere tak: max_score/afstand
        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd25_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslag-invoeren-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # nog een keer, dan bestaat de WedstrijdUitslag al
        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslag-invoeren-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_uitslag_invoeren % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = not found

    def test_rcl_deelnemers(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # get (bestaat niet)
        resp = self.client.get(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 405)       # 405 = method not allowed

        # post zonder data
        resp = self.client.post(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_zoeken(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # get (bestaat niet)
        resp = self.client.get(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        resp = self.client.post(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_opslaan(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # get (bestaat niet)
        resp = self.client.get(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        resp = self.client.post(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed


    def NOT_test_overzicht_it(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_it()

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio_ronde % 0)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

    def NOT_test_overzicht_bb(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

    def NOT_test_overzicht_rcl(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

        # mess up the cluster
        self.cluster_101a.gebruik = 42
        self.cluster_101a.save()
        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def NOT_test_overzicht_hwl(self):
        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

        # check dat de HWL geen wijzigingen mag maken
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def _setup_planning_18(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_18.pk)
        ronde = DeelcompetitieRonde.objects.all()[0]
        ronde_pk = ronde.pk
        # maak een wedstrijd aan
        self.assertEqual(Wedstrijd.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        wedstrijd_pk = Wedstrijd.objects.all()[0].pk


    def _setup_planning_25(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_25.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

        # maak de planning voor de tweede week aan
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_25.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 2)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk      # maakt uit welke

        # haal de ronde planning op
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # pas de instellingen aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 1, 'ronde_naam': 'tweede rondje gaat snel'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio_25.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # maak een wedstrijd aan
        self.assertEqual(Wedstrijd.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(Wedstrijd.objects.count(), 1)
        wedstrijd_pk = Wedstrijd.objects.all()[0].pk

        # haal de wedstrijd op
        resp = self.client.get(self.url_wijzig_wedstrijd % wedstrijd_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # wijziging van week wijziging ook wedstrijden met hetzelfde aantal dagen
        wedstrijd_datum = Wedstrijd.objects.get(pk=wedstrijd_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-12-30")        # week 1 begon op maandag 2019-12-30
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 5, 'ronde_naam': 'tweede rondje gaat snel'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio_25.pk
        self.assert_is_redirect(resp, url_regio_planning)
        wedstrijd_datum = Wedstrijd.objects.get(pk=wedstrijd_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2020-01-27")

        # haal de ronde planning op inclusief knoppen om de wedstrijden te wijzigen
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

    def NOT_test_rcl_maakt_cluster_planning(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een eerste ronde-planning aan voor een cluster
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)

        ronde = DeelcompetitieRonde.objects.all()[0]
        ronde_pk = ronde.pk
        self.assertTrue(str(ronde) != '')

        # haal de ronde planning op
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # pas de instellingen van de ronde (van een cluster) aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51, 'ronde_naam': 'eerste rondje is gratis'})
        url_cluster_planning = self.url_planning_regio_cluster % self.cluster_101a.pk
        self.assert_is_redirect(resp, url_cluster_planning)

        # maak een wedstrijd aan
        self.assertEqual(Wedstrijd.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(Wedstrijd.objects.count(), 1)
        wedstrijd_pk = Wedstrijd.objects.all()[0].pk

        # haal informatie over de wedstrijd (binnen het cluster) op
        # haal de wedstrijd op
        resp = self.client.get(self.url_wijzig_wedstrijd % wedstrijd_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # stop een vereniging in het cluster
        self.nhbver.clusters.add(self.cluster_101a)

        # haal de regioplanning op, inclusief de clusterplanning
        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # haal de cluster planning op, inclusief telling wedstrijden in een ronde
        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

# end of file
