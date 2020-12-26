# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamWedstrijdklasse
from Competitie.test_fase import zet_competitie_fase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Score.models import Score
from Taken.models import Taak
from Wedstrijden.models import WedstrijdLocatie, Wedstrijd
from Overig.e2ehelpers import E2EHelpers
from .models import (Competitie, DeelCompetitie, CompetitieKlasse,
                     DeelcompetitieRonde, competitie_aanmaken,
                     RegioCompetitieSchutterBoog, INSCHRIJF_METHODE_1)
from .views_planning_regio import competitie_week_nr_to_date
import datetime


class TestCompetitiePlanningRegio(E2EHelpers, TestCase):

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
        ver.nhb_nr = 1111
        ver.regio = self.regio_112
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = 1000
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
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.nhb_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

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

        # klassengrenzen vaststellen om de competitie voorbij fase A1 te krijgen
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
        self.client.logout()

        self.klasse_recurve_onbekend = (CompetitieKlasse
                                        .objects
                                        .filter(indiv__boogtype=self.boog_r,
                                                indiv__is_onbekend=True)
                                        .all())[0]

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')
        self.deelcomp_bond_18 = DeelCompetitie.objects.filter(laag='BK', competitie=self.comp_18)[0]
        self.deelcomp_rayon1_18 = DeelCompetitie.objects.filter(laag='RK', competitie=self.comp_18, nhb_rayon=self.rayon_1)[0]
        self.deelcomp_rayon2_18 = DeelCompetitie.objects.filter(laag='RK', competitie=self.comp_18, nhb_rayon=self.rayon_2)[0]
        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_25, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio112_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_112)[0]

        self.cluster_101a = NhbCluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')

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
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.url_planning_bond = '/competitie/planning/bk/%s/'                               # deelcomp_pk
        self.url_planning_rayon = '/competitie/planning/rk/%s/'                              # deelcomp_pk
        self.url_planning_regio = '/competitie/planning/regio/%s/'                           # deelcomp_pk
        self.url_planning_regio_cluster = '/competitie/planning/regio/cluster/%s/'           # cluster_pk
        self.url_planning_regio_ronde = '/competitie/planning/regio/ronde/%s/'               # ronde_pk
        self.url_wijzig_wedstrijd = '/competitie/planning/regio/wedstrijd/wijzig/%s/'        # wedstrijd_pk
        self.url_verwijder_wedstrijd = '/competitie/planning/regio/wedstrijd/verwijder/%s/'  # wedstrijd_pk
        self.url_score_invoeren = '/competitie/scores/uitslag-invoeren/%s/'                  # wedstrijd_pk
        self.url_afsluiten_regio = '/competitie/planning/regio/afsluiten/%s/'                # deelcomp_pk

    def _maak_inschrijving(self, deelcomp):
        RegioCompetitieSchutterBoog(schutterboog=self.schutterboog,
                                    bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                    deelcompetitie=deelcomp,
                                    klasse=self.klasse_recurve_onbekend).save()

    def test_overzicht_anon(self):
        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio_ronde % 0)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_wijzig_wedstrijd % 0)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.post(self.url_verwijder_wedstrijd % 0)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

    def test_overzicht_it(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_it()

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio_ronde % 0)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

    def test_overzicht_bb(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))
        # TODO: check geen knoppen 'wedstrijd toevoegen' of 'aanpassen wedstrijd'

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_bko(self):
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-landelijk.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))
        # TODO: check geen knoppen 'wedstrijd toevoegen' of 'aanpassen wedstrijd'

        # controleer dat de URL naar de bondscompetitie er in zit
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if url.startswith('/competitie/planning/bk/')]
        if len(urls2) != 1:     # pragma: no cover
            self.fail(msg='Link naar bondscompetitie planning ontbreekt. Urls on page: %s' % repr(urls))

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        # controleer dat de URL naar de rayoncompetitie er in zit
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if url.startswith('/competitie/planning/rk/')]
        if len(urls2) != 1:     # pragma: no cover
            self.fail(msg='Link naar rayoncompetitie planning ontbreekt. Urls on page: %s' % repr(urls))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

        # check dat de BKO geen wijzigingen mag maken
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_overzicht_rko(self):
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        # controleer dat de URL naar de rayoncompetitie er in zit
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if url.startswith('/competitie/planning/rk/')]
        if len(urls2) != 1:     # pragma: no cover
            self.fail(msg='Link naar rayoncompetitie planning ontbreekt. Urls on page: %s' % repr(urls))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

        # check dat de RKO geen wijzigingen mag maken
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_overzicht_rcl(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
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

    def test_wk53(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # pas het jaartal van de competitie aan zodat wk53 bestaat
        self.comp_18.begin_jaar = 2020
        self.comp_18.save()

        # maak een ronde aan
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success

        ronde = DeelcompetitieRonde.objects.filter(deelcompetitie=self.deelcomp_regio101_18)[0]
        resp = self.client.get(self.url_planning_regio_ronde % ronde.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # herhaal voor de 25m1p
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success

        ronde = DeelcompetitieRonde.objects.filter(deelcompetitie=self.deelcomp_regio101_25)[0]
        resp = self.client.get(self.url_planning_regio_ronde % ronde.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

    def test_overzicht_hwl(self):
        self.e2e_login_and_pass_otp(self.account_bb)        # geen account_hwl
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_planning_bond % self.deelcomp_bond_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon2_18.pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-cluster.dtl', 'plein/site_layout.dtl'))

        # check dat de HWL geen wijzigingen mag maken
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
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
        resp = self.client.get(self.url_planning_bond % self.deelcomp_rayon2_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_rayon % self.deelcomp_bond_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.get(self.url_planning_regio % self.deelcomp_bond_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        url = self.url_planning_bond % self.deelcomp_bond_18.pk
        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # wissel naar RCL voor meer rechten
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        resp = self.client.post(self.url_planning_regio % 99999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio_ronde % 99999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_planning_regio % self.deelcomp_bond_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # illegaal cluster nummer
        resp = self.client.post(self.url_planning_regio_cluster % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_rcl_maakt_planning_18(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # schrijf 1 schutter in
        self._maak_inschrijving(self.deelcomp_regio101_18)

        # maak een ronde aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)

        ronde = DeelcompetitieRonde.objects.all()[0]
        ronde_pk = ronde.pk
        self.assertTrue(str(ronde) != '')

        # haal de ronde planning op
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # pas de instellingen aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51,
                                 'ronde_naam': 'eerste rondje is gratis'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_18.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # TODO: check dat ronde settings in de database geland zijn

        # nog een post met dezelfde resultaten
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51,
                                 'ronde_naam': 'eerste rondje is gratis'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_18.pk
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

        # wijziging van week --> wijzigt wedstrijd datums met hetzelfde aantal dagen
        wedstrijd_datum = Wedstrijd.objects.get(pk=wedstrijd_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-12-16")
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 40,
                                 'ronde_naam': 'tweede rondje gaat snel'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_18.pk
        self.assert_is_redirect(resp, url_regio_planning)
        wedstrijd_datum = Wedstrijd.objects.get(pk=wedstrijd_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2019-09-30")

        # haal de wedstrijd op
        resp = self.client.get(self.url_wijzig_wedstrijd % wedstrijd_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_wijzig_wedstrijd % 99999)
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # wissel naar HWL en haal planning op
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # probeer een wijziging te doen als HWL
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51, 'ronde_naam': 'eerste rondje is gratis'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

    def test_rcl_maakt_planning_25(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        # zet deze deelcompetitie op inschrijfmethode 1
        self.deelcomp_regio101_25.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio101_25.save()

        # maak een ronde aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)

        # maak de planning voor de tweede week aan
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
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
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_25.pk
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
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_25.pk
        self.assert_is_redirect(resp, url_regio_planning)
        wedstrijd_datum = Wedstrijd.objects.get(pk=wedstrijd_pk).datum_wanneer
        self.assertEqual(str(wedstrijd_datum), "2020-01-27")

        # haal de ronde planning op inclusief knoppen om de wedstrijden te wijzigen
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

    def test_maak_10_rondes(self):
        # er moeten 10 rondes aangemaakt worden
        # de geïmporteerde rondes niet meegerekend
        # maak de rondes aan voor de import van het oude programma
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        self._maak_import(7)        # logt in als BB en wisselt naar RCL 18m
        self.assertEqual(DeelcompetitieRonde.objects.count(), 7)

        # maak nu 10 'handmatige' rondes aan
        for _ in range(10):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
            self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        # for
        self.assertEqual(DeelcompetitieRonde.objects.count(), 7 + 10)

        # controleer dat de 11e ronde niet aangemaakt mag worden
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 7 + 10)

    def test_rcl_maakt_cluster_planning(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

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
        self.nhbver_101.clusters.add(self.cluster_101a)

        # haal de regioplanning op, inclusief de clusterplanning
        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # haal de cluster planning op, inclusief telling wedstrijden in een ronde
        resp = self.client.get(self.url_planning_regio_cluster % self.cluster_101a.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_wijzig_wedstrijd_18(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        self._maak_inschrijving(self.deelcomp_regio101_18)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
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
        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': self.nhbver_101.pk, 'aanvang': '12:34',
                                 'wkl_indiv_%s' % self.klasse_recurve_onbekend.indiv.pk: 'on'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        # nog een keer hetzelfde
        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': self.nhbver_101.pk, 'aanvang': '12:34',
                                 'wkl_indiv_%s' % self.klasse_recurve_onbekend.indiv.pk: 'on'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        # verwijder de wedstrijd weer
        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': self.nhbver_101.pk, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(wedstrijd.vereniging.nhb_nr, self.nhbver_101.nhb_nr)

        resp = self.client.get(self.url_wijzig_wedstrijd % wedstrijd_pk)
        self.assertEqual(resp.status_code, 200)

        # pas een niet-bestaande wedstrijd aan
        resp = self.client.post(self.url_wijzig_wedstrijd % 999999)
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # lever slechte argumenten
        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': '', 'nhbver_pk': 'x', 'aanvang': 'xx:xx'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': '', 'aanvang': 'xx:xx'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': 'x', 'aanvang': 'xx:x'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': 'x', 'aanvang': 'xxxxx'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 'x', 'nhbver_pk': 'x', 'aanvang': '10:20'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': '9', 'nhbver_pk': '0', 'aanvang': '10:20'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '07:59'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '22:01'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '12:60'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': '0', 'nhbver_pk': '0', 'aanvang': '12:-1'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': 9999999, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': self.nhbver_101.pk, 'aanvang': '12:34',
                                 'wkl_indiv_999999': 'on'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 1, 'nhbver_pk': self.nhbver_101.pk, 'aanvang': '12:34',
                                 'wkl_indiv_x': 'on'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # probeer een wijziging te doen als HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk)
        self.assert_is_redirect(resp, '/plein/')

        # probeer te wijzigen als RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        resp = self.client.get(self.url_wijzig_wedstrijd % wedstrijd_pk)
        self.assert_is_redirect(resp, '/plein/')

        # probeer te wijzigen als BKO
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        resp = self.client.get(self.url_wijzig_wedstrijd % wedstrijd_pk)
        self.assert_is_redirect(resp, '/plein/')

    def test_wijzig_wedstrijd_25(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        # haal de vereniging uit de locatie
        self.loc.verenigingen.remove(self.nhbver_101)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

        # pas de instellingen van de ronde aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 5, 'ronde_naam': 'laatste inhaalronde'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_25.pk
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
        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 0, 'nhbver_pk': self.nhbver_101.pk, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-27')

        # pas de weekdag aan
        resp = self.client.post(self.url_wijzig_wedstrijd % wedstrijd_pk,
                                {'weekdag': 2, 'nhbver_pk': self.nhbver_101.pk, 'aanvang': '12:34'})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = Accepted

        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        self.assertEqual(str(wedstrijd.tijd_begin_wedstrijd), "12:34:00")
        self.assertEqual(str(wedstrijd.datum_wanneer), '2020-01-29')

    def test_verwijder_wedstrijd(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # maak een regioplanning aan
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 1)
        ronde_pk = DeelcompetitieRonde.objects.all()[0].pk

        # pas de instellingen van de ronde aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 5, 'ronde_naam': 'laatste inhaalronde'})
        url_regio_planning = self.url_planning_regio % self.deelcomp_regio101_18.pk
        self.assert_is_redirect(resp, url_regio_planning)

        # maak een wedstrijd aan
        self.assertEqual(Wedstrijd.objects.count(), 0)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(Wedstrijd.objects.count(), 1)
        wedstrijd_pk = Wedstrijd.objects.all()[0].pk

        # haal de wijzig-wedstrijd pagina op
        url = self.url_wijzig_wedstrijd % wedstrijd_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp, skip_menu=True)
        verwijder_url = self.url_verwijder_wedstrijd % wedstrijd_pk
        self.assertIn(verwijder_url, urls)

        # verwijder de wedstrijd
        url = self.url_verwijder_wedstrijd % wedstrijd_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)     # GET bestaat niet
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = succes

        # maak een wedstrijd aan
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
        wedstrijd_pk = Wedstrijd.objects.latest('pk').pk

        url = self.url_score_invoeren % wedstrijd_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # hang er een score aan
        wed = Wedstrijd.objects.get(pk=wedstrijd_pk)
        wed.uitslag.is_bevroren = True
        wed.uitslag.save()

        # haal de wijzig-wedstrijd pagina op
        url = self.url_wijzig_wedstrijd % wedstrijd_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp, skip_menu=True)
        verwijder_url = self.url_verwijder_wedstrijd % wedstrijd_pk
        self.assertNotIn(verwijder_url, urls)

        # probeer de wedstrijd met uitslag te verwijderen (mag niet)
        url = self.url_verwijder_wedstrijd % wedstrijd_pk
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Niet toegestaan

        wed.uitslag.is_bevroren = False
        wed.uitslag.save()

        # probeer te verwijderen als RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        resp = self.client.post(url)
        self.assert_is_redirect(resp, '/plein/')

        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # verwijder een niet bestaande wedstrijd
        resp = self.client.post(self.url_verwijder_wedstrijd % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)     # redirect naar regioplanning

    def test_max_rondes(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # maak het maximum aantal rondes aan plus een beetje meer
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        for lp in range(13):
            resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
            self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        # for
        self.assertEqual(DeelcompetitieRonde.objects.count(), 10)

        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

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
        self.assertEqual(when1, when)

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
        self.assertEqual(DeelcompetitieRonde.objects.count(), 0)
        self.client.post(url)
        self.client.post(url)
        self.client.post(url)
        self.client.post(url)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        self.assertEqual(DeelcompetitieRonde.objects.count(), 5)

        pks = [obj.pk for obj in DeelcompetitieRonde.objects.all()]

        ronde = DeelcompetitieRonde.objects.get(pk=pks[0])
        ronde.week_nr = 8
        ronde.beschrijving = 'Vierde'
        ronde.save()

        ronde = DeelcompetitieRonde.objects.get(pk=pks[1])
        ronde.week_nr = 40
        ronde.beschrijving = 'Eerste'
        ronde.save()

        ronde = DeelcompetitieRonde.objects.get(pk=pks[2])
        ronde.week_nr = 50
        ronde.beschrijving = 'Tweede een'
        ronde.save()

        # stop er ook meteen eenzelfde weeknummer in
        ronde = DeelcompetitieRonde.objects.get(pk=pks[4])
        ronde.week_nr = 50
        ronde.beschrijving = 'Tweede twee'
        ronde.save()

        ronde = DeelcompetitieRonde.objects.get(pk=pks[3])
        ronde.week_nr = 2
        ronde.beschrijving = 'Derde'
        ronde.save()

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        parts = list()
        html = str(resp.content)
        while len(html):
            pos = html.find('<tr><td>')
            if pos < 0:
                html = ''
            else:
                html = html[pos+8:]
                pos = html.find('</td>')
                part = html[:pos]
                parts.append(part)
        # while

        self.assertEqual(parts, ['40', '50', '50', '2', '8'])

    def test_inschrijving_team(self):
        # ivm coverage

        wkl = TeamWedstrijdklasse.objects.all()[0]

        klasse = CompetitieKlasse(competitie=self.deelcomp_regio101_18.competitie,
                                  team=wkl,
                                  min_ag=0.42)
        klasse.save()

        boog_bb = BoogType.objects.get(afkorting='BB')
        schutterboog = SchutterBoog(nhblid=self.lid_schutter,
                                    boogtype=boog_bb,
                                    voor_wedstrijd=True)
        schutterboog.save()

        inschrijving = RegioCompetitieSchutterBoog()
        inschrijving.schutterboog = schutterboog
        inschrijving.bij_vereniging = schutterboog.nhblid.bij_vereniging
        inschrijving.deelcompetitie = self.deelcomp_regio101_18
        inschrijving.klasse = klasse
        inschrijving.save()

        self.assertTrue(str(inschrijving) != "")

    def _maak_import(self, aantal):
        # wissel naar RCL functie
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.deelcomp_regio101_18.functie)
        self.e2e_check_rol('RCL')

        # maak er een paar rondes bij voor geïmporteerde uitslagen, elk met 1 wedstrijd
        for ronde in range(aantal):
            self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)

        top_pk = DeelcompetitieRonde.objects.latest('pk').pk - aantal

        for nr in range(aantal):
            top_pk += 1

            # maak een wedstrijd aan (doen voordat de beschrijving aangepast wordt)
            resp = self.client.post(self.url_planning_regio_ronde % top_pk, {})
            self.assertTrue(resp.status_code < 400)

            ronde = DeelcompetitieRonde.objects.get(pk=top_pk)

            # wedstrijduitslag aanmaken
            wedstrijd = ronde.plan.wedstrijden.all()[0]
            resp = self.client.get(self.url_score_invoeren % wedstrijd.pk)
            self.assertTrue(resp.status_code < 400)

            ronde.beschrijving = 'Ronde %s oude programma' % (nr + 1)
            ronde.save()

            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
            # self.uitslagen.append(wedstrijd.uitslag)

            score = Score(is_ag=False,
                          afstand_meter=18,
                          schutterboog=self.schutterboog,
                          waarde=123)
            score.save()

            wedstrijd.uitslag.scores.add(score)
        # for

    def test_met_import(self):
        # maak een paar rondes + wedstrijd aan voor de geïmporteerde uitslag
        self._maak_import(3)

        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        # haal de rayon planning op
        resp = self.client.get(self.url_planning_rayon % self.deelcomp_rayon1_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))

        # haal de regio planning op
        resp = self.client.get(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio.dtl', 'plein/site_layout.dtl'))

        # haal de ronde planning op
        ronde_import = DeelcompetitieRonde.objects.filter(deelcompetitie=self.deelcomp_regio101_18).all()[0]
        ronde_pk = ronde_import.pk
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # wissel naar RCL rol
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # haal de ronde planning op
        ronde_pk = ronde_import.pk
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # ronde naam veranderen (mag niet)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51, 'ronde_naam': 'maak niet uit'})
        self.assertEqual(resp.status_code, 302)

        # maak een ronde aan
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
        ronde = DeelcompetitieRonde.objects.latest('pk')

        # haal de ronde planning op
        ronde_pk = ronde.pk
        resp = self.client.get(self.url_planning_regio_ronde % ronde_pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-regio-ronde.dtl', 'plein/site_layout.dtl'))

        # ronde naam veranderen in import-ronde (mag niet)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk,
                                {'ronde_week_nr': 51, 'ronde_naam': 'Ronde 9 oude programma'})
        self.assertEqual(resp.status_code, 302)

        # wedstrijd toevoegen aan import-ronde (mag niet)
        resp = self.client.post(self.url_planning_regio_ronde % ronde_import.pk, {})
        self.assertEqual(resp.status_code, 404)

        # wijzig een geïmporteerde wedstrijd (mag niet)
        wedstrijd = ronde_import.plan.wedstrijden.all()[0]
        resp = self.client.get(self.url_wijzig_wedstrijd % wedstrijd.pk)
        self.assertEqual(resp.status_code, 404)

    def test_buiten_eigen_regio(self):
        # RCL probeert wedstrijd toe te voegen en wijzigen buiten eigen regio
        self.e2e_login_and_pass_otp(self.account_rcl112_18)
        self.e2e_wissel_naar_functie(self.functie_rcl112_18)

        # maak een regioplanning aan in een andere regio
        url = self.url_planning_regio % self.deelcomp_regio101_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        # controleer dat er geen 'ronde toevoegen' knop is
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(url, urls)     # url wordt gebruikt voor POST

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # maak de eigen regioplanning aan
        resp = self.client.post(self.url_planning_regio % self.deelcomp_regio112_18.pk)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        ronde_pk = DeelcompetitieRonde.objects.get(deelcompetitie=self.deelcomp_regio112_18).pk

        # maak een wedstrijd aan in de eigen regio
        resp = self.client.post(self.url_planning_regio_ronde % ronde_pk, {})
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success
        plan = DeelcompetitieRonde.objects.get(deelcompetitie=self.deelcomp_regio112_18).plan
        wedstrijd112_pk = plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_wedstrijd % wedstrijd112_pk

        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # pas de instellingen van de wedstrijd aan
        resp = self.client.post(url, {'weekdag': 0,
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_101.pk})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

    def test_afsluiten_regio(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)
        url = self.url_afsluiten_regio % self.deelcomp_regio101_18.pk

        # nog niet afsluitbaar
        zet_competitie_fase(self.comp_18, 'E')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-afsluiten-regiocomp.dtl', 'plein/site_layout.dtl'))
        hrefs = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(hrefs, ['/competitie/'])  # alleen de terug knop

        # probeer afsluiten
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed
        self.assertEqual(Taak.objects.count(), 0)

        # wel afsluitbaar
        zet_competitie_fase(self.comp_18, 'F')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-afsluiten-regiocomp.dtl', 'plein/site_layout.dtl'))
        hrefs = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(hrefs[0], url)

        # echt afsluiten
        self.assertEqual(Taak.objects.count(), 0)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes
        deelcomp = DeelCompetitie.objects.get(pk=self.deelcomp_regio101_18.pk)
        self.assertTrue(deelcomp.is_afgesloten)
        self.assertEqual(Taak.objects.count(), 2)       # RKO + BKO

        # get terwijl al afgesloten
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/rcl-afsluiten-regiocomp.dtl', 'plein/site_layout.dtl'))
        hrefs = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(hrefs, ['/competitie/'])  # alleen de terug knop

        # nogmaals afsluiten doet niets
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes
        self.assertEqual(Taak.objects.count(), 2)

    def test_bad_afsluiten_regio(self):
        self.client.logout()
        url = self.url_afsluiten_regio % 999999
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # verkeerde rol
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # verkeerde regio
        url = self.url_afsluiten_regio % self.deelcomp_regio112_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # niet bestaande pk
        url = self.url_afsluiten_regio % 999999
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

# end of file
