# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Wedstrijden.models import WedstrijdLocatie
from Overig.e2ehelpers import E2EHelpers
from .models import (Competitie, DeelCompetitie, LAAG_REGIO, competitie_aanmaken)
import datetime


class TestCompetitiePlanningRayon(E2EHelpers, TestCase):

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
        ver.nhb_nr = "1111"
        ver.regio = self.regio_112
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
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

        self.url_planning_rayon = '/competitie/planning/rayoncompetitie/%s/'               # deelcomp_pk
        self.url_wijzig_rk_wedstrijd = '/competitie/planning/wedstrijd-rayon/wijzig/%s/'   # wedstrijd_pk
        self.url_doorzetten_rk = '/competitie/planning/doorzetten/%s/rk/'                  # comp_pk
        self.url_lijst_rk = '/competitie/lijst-rayonkampioenschappen/%s/'                  # deelcomp_pk
        self.url_wijzig_status = '/competitie/lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/%s/'  # deelnemer_pk

    def competitie_sluit_alle_regiocompetities(self, comp):
        # deze functie sluit alle regiocompetities af zodat de competitie in fase G komt
        comp.zet_fase()
        # print(comp.fase)
        self.assertTrue('B' < comp.fase < 'G')
        for deelcomp in DeelCompetitie.objects.filter(competitie=comp, laag=LAAG_REGIO):
            if not deelcomp.is_afgesloten:
                deelcomp.is_afgesloten = True
                deelcomp.save()
        # for

        comp.zet_fase()
        self.assertEqual(comp.fase, 'G')

    def test_buiten_eigen_rayon(self):
        # RKO probeert RK wedstrijd toe te voegen en wijzigen buiten eigen rayon
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # maak een RK wedstrijd aan in een ander rayon
        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        # controleer dat er geen 'ronde toevoegen' knop is
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(url, urls)     # url wordt gebruikt voor POST

        # coverage: nog een keer ophalen, want dan is het plan er al
        resp = self.client.get(url)

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success

        wedstrijd_r1_pk = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk).plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r1_pk

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

    def test_planning_rayon(self):
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success

        # nog een wedstrijd
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success

        # haal het overzicht op met deze nieuwe wedstrijden
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))

        # haal de wedstrijd op
        wedstrijd_r1_pk = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk).plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r1_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd-rk.dtl', 'plein/site_layout.dtl'))

        # nog een keer ophalen, want dan zijn wedstrijd.vereniging en wedstrijd.locatie al gezet
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # wijzig de wedstrijd
        resp = self.client.post(url, {'weekdag': 1,
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_101.nhb_nr})
        self.assertEqual(resp.status_code, 302)  # 302 = redirect == success

    def test_planning_rayon_geen_ver(self):
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success

        # haal de wedstrijd op
        # hierbij lukt het niet om de wedstrijd.vereniging in te vullen
        wedstrijd_r2_pk = DeelCompetitie.objects.get(pk=self.deelcomp_rayon2_18.pk).plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r2_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd-rk.dtl', 'plein/site_layout.dtl'))

        # nu met een vereniging zonder accommodatie
        ver = self.nhbver_112       # heeft geen locatie
        ver.regio = self.regio_105  # verhuis naar rayon 2
        ver.save()

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # wijzig de wedstrijd - hierbij wordt de wedstrijd.locatie op None gezet
        resp = self.client.post(url, {'weekdag': 1,
                                      'aanvang': '12:34',
                                      'nhbver_pk': ver.nhb_nr})
        self.assertEqual(resp.status_code, 302)  # 302 = redirect == success

    def test_planning_rayon_bad(self):
        # anon
        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # probeer als BKO (RCL kom niet door de user-passes-test-mixin)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # slechte deelcompetitie
        url = self.url_planning_rayon % 999999
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # probeer een wedstrijd te wijzigen als BKO
        url = self.url_wijzig_rk_wedstrijd % 999999
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # nogmaals, als RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_wijzig_rk_wedstrijd % 999999
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        url = self.url_wijzig_rk_wedstrijd % "BAD"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        url = self.url_wijzig_rk_wedstrijd % "##"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        url = self.url_wijzig_rk_wedstrijd % "1(2)"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = success

        wedstrijd_r1_pk = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk).plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r1_pk

        # wijzig de wedstrijd
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # slechte weekdag
        resp = self.client.post(url, {'weekdag': "XX",
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_112.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # slechte weekdag
        resp = self.client.post(url, {'weekdag': 99,
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_112.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # slechte weekdag
        resp = self.client.post(url, {'weekdag': "-1",
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_112.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # weekdag buiten RK range (is 1 week lang)
        resp = self.client.post(url, {'weekdag': 30,
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_112.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # slecht tijdstip
        resp = self.client.post(url, {'weekdag': 1,
                                      'aanvang': '(*:#)',
                                      'nhbver_pk': self.nhbver_112.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # slecht tijdstip
        resp = self.client.post(url, {'weekdag': 1,
                                      'aanvang': '12:60',
                                      'nhbver_pk': self.nhbver_112.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # bad vereniging nummer
        resp = self.client.post(url, {'weekdag': 1,
                                      'aanvang': '12:34',
                                      'nhbver_pk': 999999})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # niet toegestane vereniging
        resp = self.client.post(url, {'weekdag': 1,
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_112.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # probeer wedstrijd van ander rayon te wijzigen
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        resp = self.client.post(url, {'weekdag': 1,
                                      'aanvang': '12:34',
                                      'nhbver_pk': self.nhbver_101.nhb_nr})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

    def test_lijst_rk(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_lijst_rk % self.deelcomp_rayon1_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-rk.dtl', 'plein/site_layout.dtl'))

        # nu doorzetten naar RK fase
        self.competitie_sluit_alle_regiocompetities(self.comp_18)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        resp = self.client.post(self.url_doorzetten_rk % self.comp_18.pk)
        self.assertEqual(resp.status_code, 302)     # 302 = redirect = success

        # nu nog een keer, met een RK deelnemerslijst
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-rk.dtl', 'plein/site_layout.dtl'))

    def test_bad_lijst_rk(self):
        # anon
        url = self.url_lijst_rk % self.deelcomp_rayon1_18.pk
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # regio deelcomp
        url = self.url_lijst_rk % self.deelcomp_regio101_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

        # verkeerde rayon deelcomp
        url = self.url_lijst_rk % self.deelcomp_rayon2_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

# end of file
