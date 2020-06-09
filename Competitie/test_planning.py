# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Wedstrijden.models import Wedstrijd
from Overig.e2ehelpers import E2EHelpers
from .models import Competitie, DeelCompetitie, DeelcompetitieRonde, competitie_aanmaken
import datetime


class TestCompetitiePlanning(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

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

        # maak CWZ functie aan voor deze vereniging
        self.functie_cwz = maak_functie("CWZ Vereniging %s" % ver.nhb_nr, "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')
        self.deelcomp_bond = DeelCompetitie.objects.filter(laag='BK', competitie=self.comp_18)[0]
        self.deelcomp_rayon = DeelCompetitie.objects.filter(laag='RK', competitie=self.comp_18, nhb_rayon=self.rayon_2)[0]
        self.deelcomp_regio_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio_25 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_25, nhb_regio=self.regio_101)[0]

        self.cluster_101a = NhbCluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')

        self.functie_bko = self.deelcomp_bond.functie
        self.functie_rko = self.deelcomp_rayon.functie
        self.functie_rcl = self.deelcomp_regio_18.functie

        self.functie_bko.accounts.add(self.account_bko)
        self.functie_rko.accounts.add(self.account_rko)
        self.functie_rcl.accounts.add(self.account_rcl)

        # maak nog een test vereniging, zonder CWZ functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.url_planning_bond = '/competitie/planning/bondscompetitie/%s/'     # deelcomp_pk
        self.url_planning_rayon = '/competitie/planning/rayoncompetitie/%s/'     # deelcomp_pk
        self.url_planning_regio = '/competitie/planning/regiocompetitie/%s/'    # deelcomp_pk
        self.url_planning_regio_cluster = '/competitie/planning/regiocompetitie/cluster/%s/'    # cluster_pk
        self.url_planning_regio_ronde = '/competitie/planning/regiocompetitie/ronde/%s/'        # ronde_pk
        self.url_planning_wedstrijd = '/competitie/planning/wedstrijd/%s/'      # wedstrijd_pk

    def test_overzicht_anon(self):
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

        resp = self.client.get(self.url_planning_wedstrijd % 0)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

    def test_overzicht_it(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_beheerder()

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

    def test_overzicht_bb(self):
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

    def test_overzicht_bko(self):
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_bko)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))

        # controleer dat de URL naar de bondscompetitie er in zit
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if url.startswith('/competitie/planning/bondscompetitie/')]
        if len(urls2) != 1:
            self.fail(msg='Link naar bondscompetitie planning ontbreekt. Urls on page: %s' % repr(urls))

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        # controleer dat de URL naar de rayoncompetitie er in zit
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if url.startswith('/competitie/planning/rayoncompetitie/')]
        if len(urls2) != 1:
            self.fail(msg='Link naar rayoncompetitie planning ontbreekt. Urls on page: %s' % repr(urls))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

        # check dat de BKO geen wijzigingen mag maken
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_overzicht_rko(self):
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(self.functie_rko)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        # controleer dat de URL naar de rayoncompetitie er in zit
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if url.startswith('/competitie/planning/rayoncompetitie/')]
        if len(urls2) != 1:
            self.fail(msg='Link naar rayoncompetitie planning ontbreekt. Urls on page: %s' % repr(urls))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

        # check dat de RKO geen wijzigingen mag maken
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_overzicht_rcl(self):
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

    def test_overzicht_cwz(self):
        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_cwz
        self.e2e_wissel_naar_functie(self.functie_cwz)

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

        # check dat de CWZ geen wijzigingen mag maken
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_protection(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        # niet bestaande pk's
        resp = self.client.get(self.url_planning_bond % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_rayon % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_regio % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_regio_cluster % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_regio_ronde % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(self.url_planning_regio_ronde % 99999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # verkeerde laag
        resp = self.client.get(self.url_planning_bond % self.deelcomp_rayon.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_bond.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_regio % self.deelcomp_bond.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_planning_bond % self.deelcomp_bond.pk
        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # wissel naar RCL voor meer rechten
        self.e2e_wissel_naar_functie(self.functie_rcl)

        resp = self.client.post(self.url_planning_regio % 99999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_ronde % 99999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio % self.deelcomp_bond.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # illegaal cluster nummer
        resp = self.client.post(self.url_planning_regio_cluster % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_rcl_maakt_planning_18(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

        # haal de ronde planning op
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # pas de instellingen aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51, 'ronde_naam': 'eerste rondje is gratis'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio_18.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # TODO: check dat ronde settings in de database geland zijn

        # nog een post met dezelfde resultaten
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51, 'ronde_naam': 'eerste rondje is gratis'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio_18.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # illegale week nummers
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 'x'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 0})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 99})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # weken tussen de competitie blokken
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 12})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 26})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {'ronde_week_nr': 36})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # maak een wedstrijd aan
        self.assertEqual(Wedstrijd.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(Wedstrijd.objects.count(), 1)
        wedstrijd_pk = Wedstrijd.objects.all()[0].pk

        # wijziging van week wijziging ook wedstrijden met hetzelfde aantal dagen
        wedstrijd_datum = Wedstrijd.objects.get(pk=wedstrijd_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-12-16")
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 40, 'ronde_naam': 'tweede rondje gaat snel'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio_18.pk
        self.assert_is_redirect(resp, url_regio_planning)
        wedstrijd_datum = Wedstrijd.objects.get(pk=wedstrijd_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-09-30")

        # haal de wedstrijd op
        resp = self.client.get(self.url_planning_wedstrijd % wedstrijd_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_planning_wedstrijd % 99999)
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # wissel naar CWZ en haal planning op
        self.e2e_wissel_naar_functie(self.functie_cwz)
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # probeer een wijziging te doen als CWZ
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51, 'ronde_naam': 'eerste rondje is gratis'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

    def test_rcl_maakt_planning_25(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_25.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

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
        resp = self.client.get(self.url_planning_wedstrijd % wedstrijd_pk)
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

    def test_rcl_maakt_cluster_planning(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een eerste ronde-planning aan voor een cluster
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

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
        resp = self.client.get(self.url_planning_wedstrijd % wedstrijd_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

    def test_wijzig_wedstrijd_18(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_18.pk)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

        # maak een wedstrijd aan
        self.assertEqual(Wedstrijd.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(Wedstrijd.objects.count(), 1)
        wedstrijd_pk = Wedstrijd.objects.all()[0].pk

        # pas de instellingen van de wedstrijd aan
        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': self.nhbver.pk, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")

        # pas een niet-bestaande wedstrijd aan
        resp = self.client.post(self.url_planning_wedstrijd % 999999)
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # lever slechte argumenten
        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': '', 'nhbver_pk': 'x', 'aanvang': 'xx:xx'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': '', 'aanvang': 'xx:xx'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': 'x', 'aanvang': 'xx:x'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': 'x', 'aanvang': 'xxxxx'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': 'x', 'aanvang': '10:20'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': '9', 'nhbver_pk': '0', 'aanvang': '10:20'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '07:59'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '22:01'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '12:60'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '12:-1'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': 9999999, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # probeer een wijziging te doen als CWZ
        self.e2e_wissel_naar_functie(self.functie_cwz)
        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk)
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

    def test_wijzig_wedstrijd_25(self):
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio_25.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

        # pas de instellingen van de ronde aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 5, 'ronde_naam': 'laatste inhaalronde'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio_25.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # maak een wedstrijd aan
        self.assertEqual(Wedstrijd.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(Wedstrijd.objects.count(), 1)
        wedstrijd_pk = Wedstrijd.objects.all()[0].pk

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-27')

        # pas de instellingen van de wedstrijd aan
        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 0, 'nhbver_pk': self.nhbver.pk, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-27')

        # pas de weekdag aan
        resp = self.client.post(self.url_planning_wedstrijd % wedstrijd_pk,
                                {'weekdag': 2, 'nhbver_pk': self.nhbver.pk, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-29')

# end of file
