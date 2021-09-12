# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Schutter.models import SchutterBoog
from Score.models import Score
from Wedstrijden.models import WedstrijdLocatie, CompetitieWedstrijdUitslag
from .models import (Competitie, DeelCompetitie, LAAG_REGIO, LAAG_RK, LAAG_BK,
                     KampioenschapSchutterBoog, CompetitieKlasse, DeelcompetitieKlasseLimiet,
                     CompetitieMutatie, DEELNAME_NEE, DEELNAME_JA, INSCHRIJF_METHODE_1,
                     RegioCompetitieSchutterBoog)
from .operations import competities_aanmaken
import datetime
import time
import io

sleep_oud = time.sleep


class TestCompetitiePlanningRayon(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    url_planning_rayon = '/bondscompetities/planning/rk/%s/'  # deelcomp_pk
    url_wijzig_rk_wedstrijd = '/bondscompetities/planning/rk/wedstrijd/wijzig/%s/'  # wedstrijd_pk
    url_verwijder_rk_wedstrijd = '/bondscompetities/planning/rk/wedstrijd/verwijder/%s/'  # wedstrijd_pk
    url_doorzetten_rk = '/bondscompetities/%s/doorzetten/rk/'  # comp_pk
    url_lijst_rk = '/bondscompetities/lijst-rayonkampioenschappen/%s/'  # deelcomp_pk
    url_lijst_bestand = '/bondscompetities/lijst-rayonkampioenschappen/%s/bestand/'  # deelcomp_pk
    url_wijzig_status = '/bondscompetities/lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/%s/'  # deelnemer_pk
    url_wijzig_limiet = '/bondscompetities/planning/rk/%s/limieten/'  # deelcomp_pk

    def _dummy_sleep(self, duration):
        pass

    def _verwerk_mutaties(self, show=False):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if show:                    # pragma: no coverage
            print(f1.getvalue())
            print(f2.getvalue())

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
        ver.ver_nr = "1111"
        ver.regio = self.regio_112
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
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
        competities_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.url_klassegrenzen_vaststellen_18 = '/bondscompetities/%s/klassegrenzen/vaststellen/' % self.comp_18.pk
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)                 # redirect = success
        self.comp_18 = Competitie.objects.get(afstand='18')     # refresh met nieuwe status

        self.client.logout()

        self.deelcomp_bond_18 = DeelCompetitie.objects.filter(laag=LAAG_BK, competitie=self.comp_18)[0]
        self.deelcomp_rayon1_18 = DeelCompetitie.objects.filter(laag=LAAG_RK, competitie=self.comp_18, nhb_rayon=self.rayon_1)[0]
        self.deelcomp_rayon2_18 = DeelCompetitie.objects.filter(laag=LAAG_RK, competitie=self.comp_18, nhb_rayon=self.rayon_2)[0]
        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=self.comp_25, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio112_18 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=self.comp_18, nhb_regio=self.regio_112)[0]

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

        self.klasse_r = CompetitieKlasse.objects.filter(competitie=self.comp_18,
                                                        indiv__is_onbekend=False,
                                                        indiv__niet_voor_rk_bk=False,
                                                        indiv__volgorde=100,            # Recurve klasse 1
                                                        indiv__boogtype__afkorting='R')[0]
        self.klasse_c = CompetitieKlasse.objects.filter(competitie=self.comp_18,
                                                        indiv__is_onbekend=False,
                                                        indiv__niet_voor_rk_bk=False,
                                                        indiv__volgorde=201,            # Compound klasse 2
                                                        indiv__boogtype__afkorting='C')[0]
        self.klasse_ib = CompetitieKlasse.objects.filter(competitie=self.comp_18,
                                                         indiv__is_onbekend=False,
                                                         indiv__niet_voor_rk_bk=False,
                                                         indiv__volgorde=400,           # IB klasse 1
                                                         indiv__boogtype__afkorting='IB')[0]

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.ver_1100 = ver

    def competitie_sluit_alle_regiocompetities(self, comp):
        # deze functie sluit alle regiocompetities af zodat de competitie in fase G komt
        comp.bepaal_fase()
        # print('comp: %s --> fase=%s' % (comp, comp.fase))
        self.assertTrue('B' < comp.fase < 'G')
        for deelcomp in DeelCompetitie.objects.filter(competitie=comp, laag=LAAG_REGIO):
            if not deelcomp.is_afgesloten:          # pragma: no branch
                deelcomp.is_afgesloten = True
                deelcomp.save()
        # for

        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'G')

    def _deelnemers_aanmaken(self):
        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                  schutterboog=self.schutterboog,
                                  klasse=self.klasse_r,
                                  bij_vereniging=self.schutterboog.nhblid.bij_vereniging).save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                  schutterboog=self.schutterboog,
                                  klasse=self.klasse_r,
                                  bij_vereniging=self.schutterboog.nhblid.bij_vereniging).save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                  schutterboog=self.schutterboog,
                                  klasse=self.klasse_r,
                                  bij_vereniging=self.schutterboog.nhblid.bij_vereniging).save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                  schutterboog=self.schutterboog,
                                  klasse=self.klasse_c,
                                  bij_vereniging=self.schutterboog.nhblid.bij_vereniging).save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                  schutterboog=self.schutterboog,
                                  klasse=self.klasse_c,
                                  bij_vereniging=self.schutterboog.nhblid.bij_vereniging).save()

    def test_buiten_eigen_rayon(self):
        # RKO probeert RK wedstrijd toe te voegen en wijzigen buiten eigen rayon
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # maak een RK wedstrijd aan in een ander rayon
        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        with self.assert_max_queries(23):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        # controleer dat er geen 'ronde toevoegen' knop is
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(url, urls)     # url wordt gebruikt voor POST

        # coverage: nog een keer ophalen, want dan is het plan er al
        with self.assert_max_queries(21):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)  # 404 = Not allowed

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success

        wedstrijd_r1_pk = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk).plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r1_pk

        with self.assert_max_queries(35):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_planning_rayon(self):
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        self._deelnemers_aanmaken()

        # maak een regiowedstrijd aan, zodat deze geteld kan worden
        deelcomp = DeelCompetitie.objects.get(competitie=self.comp_18,
                                              laag=LAAG_REGIO,
                                              nhb_regio=self.regio_101)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success

        # nog een wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success

        # haal het overzicht op met deze nieuwe wedstrijden
        with self.assert_max_queries(24):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/planning-rayon.dtl', 'plein/site_layout.dtl'))

        # haal de wedstrijd op
        wedstrijd_r1 = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk).plan.wedstrijden.all()[0]
        url_w = self.url_wijzig_rk_wedstrijd % wedstrijd_r1.pk
        with self.assert_max_queries(40):
            resp = self.client.get(url_w)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd-rk.dtl', 'plein/site_layout.dtl'))

        # nog een keer ophalen, want dan zijn wedstrijd.vereniging en wedstrijd.locatie al gezet
        with self.assert_max_queries(40):
            resp = self.client.get(url_w)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # wijzig de wedstrijd en zet een aantal wedstrijdklassen
        sel_indiv_1 = "wkl_indiv_%s" % self.klasse_r.indiv.pk
        sel_indiv_2 = "wkl_indiv_%s" % self.klasse_c.indiv.pk
        sel_indiv_3 = "wkl_indiv_%s" % self.klasse_ib.indiv.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url_w, {'weekdag': 1,
                                            'aanvang': '12:34',
                                            'nhbver_pk': self.nhbver_101.ver_nr,
                                            sel_indiv_1: "on",
                                            sel_indiv_2: "on",
                                            sel_indiv_3: "on",
                                            "wkl_indiv_": "on",         # bad
                                            "wkl_indiv_bad": "on"})     # bad
        self.assert_is_redirect_not_plein(resp)  # check for success

        # wissel naar BKO en haal de planning op
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        with self.assert_max_queries(25):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

    def test_planning_rayon_verwijder(self):
        # maak een wedstrijd aan en verwijder deze weer
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # doet een 'get' op de planning zodat er een plan aangemaakt wordt
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(23):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.deelcomp_rayon1_18 = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk)

        # maak een RK wedstrijd aan in het eigen rayon
        self.assertEqual(self.deelcomp_rayon1_18.plan.wedstrijden.count(), 0)
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(self.deelcomp_rayon1_18.plan.wedstrijden.count(), 1)

        # bevries de uitslag
        wedstrijd = self.deelcomp_rayon1_18.plan.wedstrijden.all()[0]
        uitslag = CompetitieWedstrijdUitslag(max_score=300,
                                             afstand_meter=18,
                                             is_bevroren=True)
        uitslag.save()
        wedstrijd.uitslag = uitslag
        wedstrijd.save()

        # wedstrijd met bevroren uitslag kan niet verwijderd worden
        url = self.url_verwijder_rk_wedstrijd % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)     # 404 = Not found/allowed

        # verwijder de bevriezing
        uitslag.is_bevroren = False
        uitslag.save()

        # verwijder de wedstrijd weer
        url = self.url_verwijder_rk_wedstrijd % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(self.deelcomp_rayon1_18.plan.wedstrijden.count(), 0)

    def test_planning_rayon_verwijder_bad(self):
        # verkeerde rol / niet ingelogd
        url = self.url_verwijder_rk_wedstrijd % 999999
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # inloggen
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # maak een RK wedstrijd aan
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success

        self.deelcomp_rayon1_18 = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk)
        wedstrijd = self.deelcomp_rayon1_18.plan.wedstrijden.all()[0]

        # verwijder bad pk
        url = self.url_verwijder_rk_wedstrijd % 999999
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)     # 404 = Not found/allowed

        # wedstrijd van niet-RK
        self.deelcomp_rayon1_18.laag = LAAG_REGIO
        self.deelcomp_rayon1_18.save()

        url = self.url_verwijder_rk_wedstrijd % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)     # 404 = Not found/allowed

        self.deelcomp_rayon1_18.laag = LAAG_RK
        self.deelcomp_rayon1_18.save()

        # verkeerde rol
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)
        url = self.url_verwijder_rk_wedstrijd % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # verwijder zonder uitslag
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_verwijder_rk_wedstrijd % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)

    def test_planning_rayon_geen_ver(self):
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # haal de wedstrijd op
        # hierbij lukt het niet om de wedstrijd.vereniging in te vullen
        wedstrijd_r2_pk = DeelCompetitie.objects.get(pk=self.deelcomp_rayon2_18.pk).plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r2_pk
        with self.assert_max_queries(28):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-wedstrijd-rk.dtl', 'plein/site_layout.dtl'))

        # nu met een vereniging zonder accommodatie
        ver = self.nhbver_112       # heeft geen locatie
        ver.regio = self.regio_105  # verhuis naar rayon 2
        ver.save()

        with self.assert_max_queries(32):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # wijzig de wedstrijd - hierbij wordt de wedstrijd.locatie op None gezet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'nhbver_pk': ver.ver_nr})
        self.assert_is_redirect_not_plein(resp)  # check for success

    def test_planning_rayon_bad(self):
        # anon
        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # probeer als BKO (RCL kom niet door de user-passes-test-mixin)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_planning_rayon % self.deelcomp_rayon2_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # slechte deelcompetitie
        url = self.url_planning_rayon % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        # probeer een wedstrijd te wijzigen als BKO
        url = self.url_wijzig_rk_wedstrijd % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # nogmaals, als RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_wijzig_rk_wedstrijd % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not allowed

        url = self.url_wijzig_rk_wedstrijd % "BAD"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not allowed

        url = self.url_wijzig_rk_wedstrijd % "##"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not allowed

        url = self.url_wijzig_rk_wedstrijd % "1(2)"
        with self.assert_max_queries(20):
            resp = self.client.get(url)

        self.assert404(resp)  # 404 = Not allowed
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)  # 404 = Not allowed

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success

        wedstrijd_r1_pk = DeelCompetitie.objects.get(pk=self.deelcomp_rayon1_18.pk).plan.wedstrijden.all()[0].pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r1_pk

        # wijzig de wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)  # 404 = Not allowed

        # slechte weekdag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': "XX",
                                          'aanvang': '12:34',
                                          'nhbver_pk': self.nhbver_112.ver_nr})
        self.assert404(resp)  # 404 = Not allowed

        # slechte weekdag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 99,
                                          'aanvang': '12:34',
                                          'nhbver_pk': self.nhbver_112.ver_nr})
        self.assert404(resp)  # 404 = Not allowed

        # slechte weekdag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': "-1",
                                          'aanvang': '12:34',
                                          'nhbver_pk': self.nhbver_112.ver_nr})
        self.assert404(resp)  # 404 = Not allowed

        # weekdag buiten RK range (is 1 week lang)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 30,
                                          'aanvang': '12:34',
                                          'nhbver_pk': self.nhbver_112.ver_nr})
        self.assert404(resp)  # 404 = Not allowed

        # slecht tijdstip
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '(*:#)',
                                          'nhbver_pk': self.nhbver_112.ver_nr})
        self.assert404(resp)  # 404 = Not allowed

        # slecht tijdstip
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:60',
                                          'nhbver_pk': self.nhbver_112.ver_nr})
        self.assert404(resp)  # 404 = Not allowed

        # bad vereniging nummer
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'nhbver_pk': 999999})
        self.assert404(resp)  # 404 = Not allowed

        # niet toegestane vereniging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'nhbver_pk': self.nhbver_112.ver_nr})
        self.assert404(resp)  # 404 = Not allowed

        # probeer wedstrijd van ander rayon te wijzigen
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'nhbver_pk': self.nhbver_101.ver_nr})
        self.assert403(resp)

    def test_lijst_rk(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_lijst_rk % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

        # nu doorzetten naar RK fase
        self.competitie_sluit_alle_regiocompetities(self.comp_18)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        resp = self.client.post(self.url_doorzetten_rk % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # zet een limiet
        limiet = DeelcompetitieKlasseLimiet(deelcompetitie=self.deelcomp_rayon1_18,
                                            klasse=self.klasse_r,
                                            limiet=20)
        limiet.save()
        self.assertTrue(str(limiet) != "")      # coverage only

        # nu nog een keer, met een RK deelnemerslijst
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        deelnemer = KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                              schutterboog=self.schutterboog,
                                              bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                              klasse=self.klasse_r)
        deelnemer.save()
        self.assertTrue(str(deelnemer) != "")      # coverage only

        deelnemer = KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                              schutterboog=self.schutterboog,
                                              bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                              klasse=self.klasse_c)
        deelnemer.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

        deelnemer.deelname = DEELNAME_JA
        deelnemer.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

        deelnemer.rank = 100
        deelnemer.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

        deelnemer.bij_vereniging = None
        deelnemer.rank = 1
        deelnemer.deelname = DEELNAME_NEE
        deelnemer.save()

        # twee deelnemers in dezelfde klasse
        deelnemer.pk = None
        deelnemer.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

        url = self.url_lijst_bestand % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assertContains(resp, "100007")
        self.assertContains(resp, "Schutter Test")
        self.assertContains(resp, "[1000] Grote Club")
        self.assertContains(resp, "(deelname onzeker)")
        self.assertContains(resp, "Recurve klasse 1")

    def test_bad_lijst_rk(self):
        # anon
        url = self.url_lijst_rk % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # regio deelcomp
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_rk % self.deelcomp_regio101_18.pk)
        self.assert404(resp)  # 404 = Not allowed

        # verkeerde rayon deelcomp
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_rk % self.deelcomp_rayon2_18.pk)
        self.assert403(resp)

        # geen deelnemers lijst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_bestand % self.deelcomp_rayon1_18.pk)
        self.assert404(resp)  # 404 = Not allowed

        # verkeerde rayon deelcomp - download
        self.deelcomp_rayon2_18.heeft_deelnemerslijst = True
        self.deelcomp_rayon2_18.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_bestand % self.deelcomp_rayon2_18.pk)
        self.assert403(resp)

        # bad deelcomp pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_bestand % 999999)
        self.assert404(resp)  # 404 = Not allowed

    def test_bad_wijzig_status(self):
        self.client.logout()
        url = self.url_wijzig_status % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)  # 404 = Not allowed

        # verkeerde RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        deelnemer = KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                              schutterboog=self.schutterboog,
                                              bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                              klasse=self.klasse_r)
        deelnemer.save()

        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_wijzig_status(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        deelnemer = KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                              schutterboog=self.schutterboog,
                                              bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                              klasse=self.klasse_r)
        deelnemer.save()

        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-status-rk-deelnemer.dtl', 'plein/site_layout.dtl'))

        # geen vereniging
        deelnemer.bij_vereniging = None
        deelnemer.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': '0', 'afmelden': '0', 'snel': 1})
        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': '0', 'afmelden': '1', 'snel': 1})
        self.assertEqual(CompetitieMutatie.objects.count(), 1)

        # bevestigen mag niet, want geen lid bij vereniging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': '1', 'afmelden': '0', 'snel': 1})
        self.assertEqual(CompetitieMutatie.objects.count(), 1)

        # verbouw 'time' en voer een test uit zonder 'snel'
        time.sleep = self._dummy_sleep
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': '0', 'afmelden': '1'})
        time.sleep = sleep_oud
        self.assertEqual(CompetitieMutatie.objects.count(), 2)

    def test_wijzig_status_hwl(self):
        # HWL
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        deelnemer = KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                              schutterboog=self.schutterboog,
                                              bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                              klasse=self.klasse_r)
        deelnemer.save()

        # probeer als HWL van een andere vereniging de status van deze sporter aan te passen
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 302)     # 302 = redirect

        lid = self.schutterboog.nhblid
        lid.bij_vereniging = self.ver_1100
        lid.save()

        deelnemer = KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                              schutterboog=self.schutterboog,
                                              bij_vereniging=self.ver_1100,
                                              klasse=self.klasse_r)
        deelnemer.save()

        # probeer als HWL van een andere vereniging de status van deze sporter aan te passen
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert403(resp)

    def test_bad_wijzig_limiet(self):
        self.client.logout()
        url = self.url_wijzig_limiet % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)  # 404 = Not allowed

        url = self.url_wijzig_limiet % self.deelcomp_rayon1_18.pk

        sel = 'sel_%s' % self.klasse_c.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 'xx'})
        self.assertEqual(resp.status_code, 302)     # doorloopt alles

        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: '19'})
        self.assert404(resp)     # 404 = Not allowed

        # verkeerde RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        url = self.url_wijzig_limiet % self.deelcomp_rayon1_18.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_wijzig_limiet(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # zonder limiet aanwezig
        url = self.url_wijzig_limiet % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/wijzig-limieten-rk.dtl', 'plein/site_layout.dtl'))

        sel = 'sel_%s' % self.klasse_r.pk

        # limiet op default zetten
        self.assertEqual(DeelcompetitieKlasseLimiet.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 24, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(DeelcompetitieKlasseLimiet.objects.count(), 0)

        # limiet zetten
        self.assertEqual(DeelcompetitieKlasseLimiet.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 20, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self._verwerk_mutaties()
        self.assertEqual(DeelcompetitieKlasseLimiet.objects.count(), 1)

        # limiet opnieuw zetten, geen wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 20, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self._verwerk_mutaties()
        self.assertEqual(DeelcompetitieKlasseLimiet.objects.count(), 1)

        # limiet aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 16, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self._verwerk_mutaties()
        self.assertEqual(DeelcompetitieKlasseLimiet.objects.count(), 1)

        # met limiet aanwezig
        url = self.url_wijzig_limiet % self.deelcomp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # limiet verwijderen, zonder 'snel'
        time.sleep = self._dummy_sleep
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 24})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self._verwerk_mutaties()
        self.assertEqual(DeelcompetitieKlasseLimiet.objects.count(), 0)
        time.sleep = sleep_oud

        # nu met een deelnemer, zodat de mutatie opgestart wordt
        deelnemer = KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_rayon1_18,
                                              schutterboog=self.schutterboog,
                                              bij_vereniging=self.schutterboog.nhblid.bij_vereniging,
                                              klasse=self.klasse_r)
        deelnemer.save()

        aantal = CompetitieMutatie.objects.count()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 4, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self._verwerk_mutaties()
        self.assertEqual(CompetitieMutatie.objects.count(), aantal + 1)

    def test_geen_vereniging(self):
        # deelnemer regiocompetitie is nu zonder vereniging
        # wordt wel opgenomen in de RK selectie
        # kan geen deelnemer status krijgen
        # wordt daarna weer lid en kan deelnemer worden

        scores = (200, 200, 200, 200, 200, 200, 200)
        deelnemer = RegioCompetitieSchutterBoog(
                            deelcompetitie=self.deelcomp_regio101_18,
                            schutterboog=self.schutterboog,     # bij self.nhbver_101
                            bij_vereniging=self.nhbver_101,
                            klasse=self.klasse_r,
                            ag_voor_indiv=8.765,
                            ag_voor_team=8.765,
                            ag_voor_team_mag_aangepast_worden=True,
                            score1=scores[0],
                            score2=scores[1],
                            score3=scores[2],
                            score4=scores[3],
                            score5=scores[4],
                            score6=scores[5],
                            score7=scores[6],
                            aantal_scores=7,
                            totaal=sum(scores),
                            laagste_score_nr=3)
        deelnemer.save()

        for waarde in scores:
            score = Score(
                        schutterboog=self.schutterboog,
                        waarde=waarde,
                        afstand_meter=18)
            score.save()
            deelnemer.scores.add(score)
        # for

        # lid stapt over naar een andere vereniging
        # noteer: deze situatie ontstaat pas na 15 januari (tot die tijd vast op oude vereniging)
        lid = self.schutterboog.nhblid
        lid.bij_vereniging = None           # was: self.ver_101
        lid.save()

        # nu doorzetten naar RK fase
        self.competitie_sluit_alle_regiocompetities(self.comp_18)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        with self.assert_max_queries(58):
            resp = self.client.post(self.url_doorzetten_rk % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # controleer dat schutterboog opgenomen is in de RK selectie
        deelnemer = KampioenschapSchutterBoog.objects.get(schutterboog=self.schutterboog)
        self.assertEqual(deelnemer.bij_vereniging, None)

        # wissel van rol naar RKO rayon1
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # status op "deelnemer" zetten terwijl bij_vereniging=None moet niet kunnen
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert404(resp)     # 404 = not allowed

        # TODO: deze test is nog niet af!

        # sluit het lid aan bij een andere vereniging
        # wat als dit in een ander rayon is?

# end of file
