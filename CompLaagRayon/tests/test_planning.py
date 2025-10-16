# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_BK, DEEL_RK, DEELNAME_NEE, DEELNAME_JA, DEELNAME_ONBEKEND, INSCHRIJF_METHODE_1
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMutatie,
                               Regiocompetitie, RegiocompetitieSporterBoog,
                               Kampioenschap, KampioenschapSporterBoog,
                               KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet)
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import (evaluatie_datum, zet_competitie_fase_rk_prep,
                                            zet_competitie_fase_regio_afsluiten)
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio, Cluster
from Locatie.models import WedstrijdLocatie
from Score.models import Uitslag
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime
import time

sleep_oud = time.sleep


class TestCompLaagRayonPlanning(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, Planning functie """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_planning_rayon = '/bondscompetities/rk/planning/%s/'                                    # deelcomp_pk
    url_wijzig_rk_wedstrijd = '/bondscompetities/rk/planning/wedstrijd/wijzig/%s/'              # match_pk
    url_verwijder_rk_wedstrijd = '/bondscompetities/rk/planning/wedstrijd/verwijder/%s/'        # match_pk
    url_lijst_rk = '/bondscompetities/rk/lijst/%s/'                                             # deelcomp_pk
    url_lijst_bestand = '/bondscompetities/rk/lijst/%s/bestand/'                                # deelcomp_pk
    url_wijzig_status = '/bondscompetities/rk/lijst/wijzig-status-rk-deelnemer/%s/'             # deelnemer_pk
    url_wijzig_limiet = '/bondscompetities/rk/planning/%s/limieten/'                            # deelcomp_pk
    url_doorzetten_regio_naar_rk = '/bondscompetities/beheer/%s/doorzetten/regio-naar-rk/'      # comp_pk
    url_doorzetten_rk_indiv = '/bondscompetities/beheer/%s/doorzetten/rk-indiv-naar-bk/'        # comp_pk
    url_doorzetten_rk_teams = '/bondscompetities/beheer/%s/doorzetten/rk-teams-naar-bk/'        # comp_pk
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp.pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def _dummy_sleep(self, duration):
        pass

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

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL101')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL101-25')
        self.account_rcl112_18 = self._prep_beheerder_lid('RCL112')
        self.account_sporter = self._prep_beheerder_lid('Sporter')
        self.account_hwl = self._prep_beheerder_lid('HWL')
        self.lid_sporter = Sporter.objects.get(lid_nr=self.account_sporter.username)
        self.lid_sporter2 = Sporter.objects.get(lid_nr=self.account_rcl101_18.username)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.sporterboog = SporterBoog(sporter=self.lid_sporter,
                                       boogtype=self.boog_r,
                                       voor_wedstrijd=True)
        self.sporterboog.save()

        self.sporterboog2 = SporterBoog(sporter=self.lid_sporter2,
                                        boogtype=self.boog_r,
                                        voor_wedstrijd=True)
        self.sporterboog2.save()

        # creëer een competitie met regiocompetities
        competities_aanmaken(jaar=2019)
        evaluatie_datum.zet_test_datum('2019-08-01')

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen_18 = self.url_klassengrenzen_vaststellen % self.comp_18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)                 # redirect = success
        self.comp_18 = Competitie.objects.get(afstand='18')     # refresh met nieuwe status

        self.client.logout()

        self.deelcomp_bond_18 = Kampioenschap.objects.filter(deel=DEEL_BK, competitie=self.comp_18)[0]
        self.deelkamp_rayon1_18 = Kampioenschap.objects.filter(deel=DEEL_RK, competitie=self.comp_18,
                                                               rayon=self.rayon_1)[0]
        self.deelkamp_rayon2_18 = Kampioenschap.objects.filter(deel=DEEL_RK, competitie=self.comp_18,
                                                               rayon=self.rayon_2)[0]
        self.deelcomp_regio101_18 = Regiocompetitie.objects.filter(competitie=self.comp_18, regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = Regiocompetitie.objects.filter(competitie=self.comp_25, regio=self.regio_101)[0]
        self.deelcomp_regio112_18 = Regiocompetitie.objects.filter(competitie=self.comp_18, regio=self.regio_112)[0]

        self.cluster_101a = Cluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')

        self.functie_bko_18 = self.deelcomp_bond_18.functie
        self.functie_rko1_18 = self.deelkamp_rayon1_18.functie
        self.functie_rko2_18 = self.deelkamp_rayon2_18.functie
        self.functie_rcl101_18 = self.deelcomp_regio101_18.functie
        self.functie_rcl101_25 = self.deelcomp_regio101_25.functie
        self.functie_rcl112_18 = self.deelcomp_regio112_18.functie

        self.functie_bko_18.accounts.add(self.account_bko_18)
        self.functie_rko1_18.accounts.add(self.account_rko1_18)
        self.functie_rko2_18.accounts.add(self.account_rko2_18)
        self.functie_rcl101_18.accounts.add(self.account_rcl101_18)
        self.functie_rcl101_25.accounts.add(self.account_rcl101_25)
        self.functie_rcl112_18.accounts.add(self.account_rcl112_18)
        self.functie_hwl.accounts.add(self.account_hwl)

        self.klasse_r = CompetitieIndivKlasse.objects.filter(competitie=self.comp_18,
                                                             is_onbekend=False,
                                                             is_ook_voor_rk_bk=True,
                                                             volgorde=1100,           # Recurve klasse 1
                                                             boogtype__afkorting='R')[0]
        self.klasse_c = CompetitieIndivKlasse.objects.filter(competitie=self.comp_18,
                                                             is_onbekend=False,
                                                             is_ook_voor_rk_bk=True,
                                                             volgorde=1201,           # Compound klasse 2
                                                             boogtype__afkorting='C')[0]
        self.klasse_ib = CompetitieIndivKlasse.objects.filter(competitie=self.comp_18,
                                                              is_onbekend=False,
                                                              is_ook_voor_rk_bk=True,
                                                              volgorde=1400,          # TR klasse 1
                                                              boogtype__afkorting='TR')[0]

        self.klasse_r_ere = CompetitieTeamKlasse.objects.get(competitie=self.comp_18,
                                                             beschrijving='Recurve klasse ERE',
                                                             is_voor_teams_rk_bk=True)

        # maak nog een test vereniging, zonder HWL functie
        ver = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver.save()
        self.ver_1100 = ver

    def competitie_sluit_alle_regiocompetities(self, comp):
        # deze functie sluit alle regiocompetities af zodat de competitie in fase G komt
        comp.bepaal_fase()
        self.assertEqual(comp.fase_indiv, 'G')
        self.assertEqual(comp.fase_teams, 'G')
        for deelcomp in Regiocompetitie.objects.filter(competitie=comp):
            if not deelcomp.is_afgesloten:          # pragma: no branch
                deelcomp.is_afgesloten = True
                deelcomp.save(update_fields=['is_afgesloten'])
        # for

    def _deelnemers_aanmaken(self):
        KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                 sporterboog=self.sporterboog,
                                 indiv_klasse=self.klasse_r,
                                 bij_vereniging=self.sporterboog.sporter.bij_vereniging).save()

        KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                 sporterboog=self.sporterboog,
                                 indiv_klasse=self.klasse_r,
                                 bij_vereniging=self.sporterboog.sporter.bij_vereniging).save()

        KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                 sporterboog=self.sporterboog,
                                 indiv_klasse=self.klasse_r,
                                 bij_vereniging=self.sporterboog.sporter.bij_vereniging).save()

        KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                 sporterboog=self.sporterboog,
                                 indiv_klasse=self.klasse_c,
                                 bij_vereniging=self.sporterboog.sporter.bij_vereniging).save()

        KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                 sporterboog=self.sporterboog,
                                 indiv_klasse=self.klasse_c,
                                 bij_vereniging=self.sporterboog.sporter.bij_vereniging).save()

    def test_buiten_eigen_rayon(self):
        # RKO probeert RK wedstrijd toe te voegen en wijzigen buiten eigen rayon
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # maak een RK wedstrijd aan in een ander rayon
        url = self.url_planning_rayon % self.deelkamp_rayon2_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        # controleer dat er geen 'ronde toevoegen' knop is
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(url, urls)     # url wordt gebruikt voor POST

        # coverage: nog een keer ophalen, want dan is het plan er al
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success

        wedstrijd_r1_pk = Kampioenschap.objects.get(pk=self.deelkamp_rayon1_18.pk).rk_bk_matches.first().pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r1_pk

        with self.assert_max_queries(22):
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
        deelcomp = Regiocompetitie.objects.get(competitie=self.comp_18,
                                               regio=self.regio_101)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelkamp_rayon1_18.pk
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
        self.assert_template_used(resp, ('complaagrayon/planning-rayon.dtl', 'design/site_layout.dtl'))

        # haal de wedstrijd op
        wedstrijd_r1 = Kampioenschap.objects.get(pk=self.deelkamp_rayon1_18.pk).rk_bk_matches.first()
        url_w = self.url_wijzig_rk_wedstrijd % wedstrijd_r1.pk
        with self.assert_max_queries(27):
            resp = self.client.get(url_w)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-wedstrijd-rk.dtl', 'design/site_layout.dtl'))

        # nog een keer ophalen, want dan zijn wedstrijd.vereniging en wedstrijd.locatie al gezet
        with self.assert_max_queries(27):
            resp = self.client.get(url_w)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # wijzig de wedstrijd en zet een aantal wedstrijdklassen
        sel_indiv_1 = "wkl_indiv_%s" % self.klasse_r.pk
        sel_indiv_2 = "wkl_indiv_%s" % self.klasse_c.pk
        sel_indiv_3 = "wkl_indiv_%s" % self.klasse_ib.pk
        with self.assert_max_queries(28):
            resp = self.client.post(url_w, {'weekdag': 1,
                                            'aanvang': '12:34',
                                            'ver_pk': self.ver_101.ver_nr,
                                            'loc_pk': self.loc.pk,
                                            sel_indiv_1: "on",
                                            sel_indiv_2: "on",
                                            sel_indiv_3: "on",
                                            'wkl_indiv_': "on",         # bad
                                            'wkl_indiv_bad': "on",      # bad
                                            'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success

        # wissel naar BKO en haal de planning op
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        with self.assert_max_queries(23):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

    def test_planning_rayon_verwijder(self):
        # maak een wedstrijd aan en verwijder deze weer
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # doet een 'get' op de planning zodat er een plan aangemaakt wordt
        url = self.url_planning_rayon % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.deelkamp_rayon1_18 = Kampioenschap.objects.get(pk=self.deelkamp_rayon1_18.pk)

        # maak een RK wedstrijd aan in het eigen rayon
        self.assertEqual(self.deelkamp_rayon1_18.rk_bk_matches.count(), 0)
        url = self.url_planning_rayon % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(self.deelkamp_rayon1_18.rk_bk_matches.count(), 1)

        # bevries de uitslag
        wedstrijd = self.deelkamp_rayon1_18.rk_bk_matches.first()
        url = self.url_verwijder_rk_wedstrijd % wedstrijd.pk

        self.deelkamp_rayon1_18.rk_bk_matches.clear()
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Geen RK wedstrijd')
        self.deelkamp_rayon1_18.rk_bk_matches.add(wedstrijd)

        # wedstrijd met bevroren uitslag kan niet verwijderd worden
        uitslag = Uitslag(max_score=300,
                          afstand=18,
                          is_bevroren=True)
        uitslag.save()
        wedstrijd.uitslag = uitslag
        wedstrijd.save(update_fields=['uitslag'])

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Uitslag mag niet meer gewijzigd worden')

        # verwijder de bevriezing
        uitslag.is_bevroren = False
        uitslag.save()

        # verwijder de wedstrijd weer
        url = self.url_verwijder_rk_wedstrijd % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(self.deelkamp_rayon1_18.rk_bk_matches.count(), 0)

    def test_planning_rayon_verwijder_bad(self):
        # verkeerde rol / niet ingelogd
        url = self.url_verwijder_rk_wedstrijd % 999999
        resp = self.client.post(url)
        self.assert403(resp)

        # inloggen
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # maak een RK wedstrijd aan
        url = self.url_planning_rayon % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)     # check success

        self.deelkamp_rayon1_18 = Kampioenschap.objects.get(pk=self.deelkamp_rayon1_18.pk)
        wedstrijd = self.deelkamp_rayon1_18.rk_bk_matches.first()

        # verwijder bad pk
        url = self.url_verwijder_rk_wedstrijd % 999999
        resp = self.client.post(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

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
        url = self.url_planning_rayon % self.deelkamp_rayon2_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # haal de wedstrijd op
        # hierbij lukt het niet om de wedstrijd.vereniging in te vullen
        wedstrijd_r2_pk = Kampioenschap.objects.get(pk=self.deelkamp_rayon2_18.pk).rk_bk_matches.first().pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r2_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-wedstrijd-rk.dtl', 'design/site_layout.dtl'))

        # nu met een vereniging zonder accommodatie
        ver = self.ver_112       # heeft geen locatie
        ver.regio = self.regio_105  # verhuis naar rayon 2
        ver.save()

        with self.assert_max_queries(21):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # wijzig de wedstrijd - hierbij wordt de wedstrijd.locatie op None gezet
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'ver_pk': ver.ver_nr})
        self.assert_is_redirect_not_plein(resp)  # check for success

    def test_planning_rayon_bad(self):
        # anon
        url = self.url_planning_rayon % self.deelkamp_rayon2_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # probeer als BKO (RCL kom niet door de user-passes-test-mixin)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_planning_rayon % self.deelkamp_rayon2_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # slechte regiocompetitie
        url = self.url_planning_rayon % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # probeer een wedstrijd te wijzigen als BKO
        url = self.url_wijzig_rk_wedstrijd % 999999
        resp = self.client.get(url)
        self.assert403(resp)

        # nogmaals, als RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_wijzig_rk_wedstrijd % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        url = self.url_wijzig_rk_wedstrijd % "BAD"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        url = self.url_wijzig_rk_wedstrijd % "##"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Pagina bestaat niet')

        url = self.url_wijzig_rk_wedstrijd % "1(2)"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # maak een RK wedstrijd aan in het eigen rayon
        url = self.url_planning_rayon % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)  # check for success

        wedstrijd_r1_pk = Kampioenschap.objects.get(pk=self.deelkamp_rayon1_18.pk).rk_bk_matches.first().pk
        url = self.url_wijzig_rk_wedstrijd % wedstrijd_r1_pk

        # wijzig de wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Incompleet verzoek')

        # slechte weekdag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': "XX",
                                          'aanvang': '12:34',
                                          'ver_pk': self.ver_112.ver_nr})
        self.assert404(resp, 'Geen valide verzoek')

        # slechte weekdag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 99,
                                          'aanvang': '12:34',
                                          'ver_pk': self.ver_112.ver_nr})
        self.assert404(resp, 'Geen valide verzoek')

        # slechte weekdag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': "-1",
                                          'aanvang': '12:34',
                                          'ver_pk': self.ver_112.ver_nr})
        self.assert404(resp, 'Geen valide verzoek')

        # weekdag buiten RK range (is 1 week lang)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 30,
                                          'aanvang': '12:34',
                                          'ver_pk': self.ver_112.ver_nr})
        self.assert404(resp, 'Geen valide datum')

        # slecht tijdstip
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '(*:#)',
                                          'ver_pk': self.ver_112.ver_nr})
        self.assert404(resp, 'Geen valide verzoek')

        # slecht tijdstip
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:60',
                                          'ver_pk': self.ver_112.ver_nr})
        self.assert404(resp, 'Geen valide tijdstip')

        # bad vereniging nummer
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'ver_pk': 999999})
        self.assert404(resp, 'Vereniging niet gevonden')

        # niet toegestane vereniging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'ver_pk': self.ver_112.ver_nr})
        self.assert404(resp, 'Geen valide rayon')

        # probeer wedstrijd van ander rayon te wijzigen
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'weekdag': 1,
                                          'aanvang': '12:34',
                                          'ver_pk': self.ver_101.ver_nr})
        self.assert403(resp)

    def test_alvast_afgemeld(self):
        # maak een deelnemer aan die wel mee wilt doen met het RK
        deelnemer = RegiocompetitieSporterBoog(
                                sporterboog=self.sporterboog,
                                bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                regiocompetitie=self.deelcomp_regio101_18,
                                indiv_klasse=self.klasse_r,
                                aantal_scores=6,
                                inschrijf_voorkeur_rk_bk=True)
        deelnemer.save()

        # maak een deelnemer aan die alvast afgemeld is voor het RK
        deelnemer2 = RegiocompetitieSporterBoog(
                                sporterboog=self.sporterboog2,
                                bij_vereniging=self.sporterboog2.sporter.bij_vereniging,
                                regiocompetitie=self.deelcomp_regio101_18,
                                indiv_klasse=self.klasse_r,
                                aantal_scores=6,
                                inschrijf_voorkeur_rk_bk=False)
        deelnemer2.save()

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_lijst_rk % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/rko-rk-selectie.dtl', 'design/site_layout.dtl'))

        # nu doorzetten naar RK fase
        zet_competitie_fase_regio_afsluiten(self.comp_18)
        self.competitie_sluit_alle_regiocompetities(self.comp_18)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        resp = self.client.post(self.url_doorzetten_regio_naar_rk % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # laat de mutaties verwerken
        self.verwerk_competitie_mutaties()

        # controleer de 'deelname' instelling voor de KampioenschapSporterBoog
        kampioen = KampioenschapSporterBoog.objects.get(sporterboog=self.sporterboog)
        self.assertEqual(kampioen.deelname, DEELNAME_ONBEKEND)

        kampioen2 = KampioenschapSporterBoog.objects.get(sporterboog=self.sporterboog2)
        self.assertEqual(kampioen2.deelname, DEELNAME_NEE)

    def test_lijst_rk(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_lijst_rk % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/rko-rk-selectie.dtl', 'design/site_layout.dtl'))

        # nu doorzetten naar RK fase
        zet_competitie_fase_regio_afsluiten(self.comp_18)
        self.competitie_sluit_alle_regiocompetities(self.comp_18)
        self.e2e_login_and_pass_otp(self.account_bko_18)
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        resp = self.client.post(self.url_doorzetten_regio_naar_rk % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success

        # laat de mutaties verwerken
        self.verwerk_competitie_mutaties()

        # zet een limiet
        limiet = KampioenschapIndivKlasseLimiet(kampioenschap=self.deelkamp_rayon1_18,
                                                indiv_klasse=self.klasse_r,
                                                limiet=20)
        limiet.save()
        self.assertTrue(str(limiet) != "")      # coverage only

        limiet = KampioenschapTeamKlasseLimiet(kampioenschap=self.deelkamp_rayon1_18,
                                               team_klasse=self.klasse_r_ere,
                                               limiet=20)
        limiet.save()
        self.assertTrue(str(limiet) != '')

        # nu nog een keer, met een RK deelnemerslijst
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        deelnemer = KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                             sporterboog=self.sporterboog,
                                             bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                             indiv_klasse=self.klasse_r)
        deelnemer.save()
        self.assertTrue(str(deelnemer) != "")      # coverage only

        deelnemer = KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                             sporterboog=self.sporterboog,
                                             bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                             indiv_klasse=self.klasse_c)
        deelnemer.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/rko-rk-selectie.dtl', 'design/site_layout.dtl'))

        deelnemer.deelname = DEELNAME_JA
        deelnemer.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/rko-rk-selectie.dtl', 'design/site_layout.dtl'))

        deelnemer.rank = 100
        deelnemer.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/rko-rk-selectie.dtl', 'design/site_layout.dtl'))

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
        self.assert_template_used(resp, ('complaagrayon/rko-rk-selectie.dtl', 'design/site_layout.dtl'))

        url = self.url_lijst_bestand % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assertContains(resp, "100007")
        self.assertContains(resp, "Sporter Test")
        self.assertContains(resp, "[1000] Grote Club")
        self.assertContains(resp, "(deelname onzeker)")
        self.assertContains(resp, "Recurve klasse 1")

    def test_bad_lijst_rk(self):
        # anon
        url = self.url_lijst_rk % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # regio deelcomp
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_rk % self.deelcomp_regio101_18.pk)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # verkeerde rayon deelcomp
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_rk % self.deelkamp_rayon2_18.pk)
        self.assert403(resp)

        # geen deelnemers lijst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_bestand % self.deelkamp_rayon1_18.pk)
        self.assert404(resp, 'Geen deelnemerslijst')

        # verkeerde rayon deelcomp - download
        self.deelkamp_rayon2_18.heeft_deelnemerslijst = True
        self.deelkamp_rayon2_18.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_bestand % self.deelkamp_rayon2_18.pk)
        self.assert403(resp)

        # bad deelcomp pk
        resp = self.client.get(self.url_lijst_bestand % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

    def test_bad_wijzig_status(self):
        self.client.logout()
        url = self.url_wijzig_status % 999999
        resp = self.client.get(url)
        self.assert403(resp)

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Deelnemer niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Deelnemer niet gevonden')

        # verkeerde RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        zet_competitie_fase_rk_prep(self.comp_18)

        deelnemer = KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                             sporterboog=self.sporterboog,
                                             bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                             indiv_klasse=self.klasse_r)
        deelnemer.save()

        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_wijzig_status_rko(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        zet_competitie_fase_rk_prep(self.comp_18)

        deelnemer = KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                             sporterboog=self.sporterboog,
                                             bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                             indiv_klasse=self.klasse_r)
        deelnemer.save()

        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-status-rk-deelnemer.dtl', 'design/site_layout.dtl'))

        # geen vereniging
        deelnemer.bij_vereniging = None
        deelnemer.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        with self.assert_max_queries(20):
            self.client.post(url, {'bevestig': '0', 'afmelden': '0', 'snel': 1})
        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        with self.assert_max_queries(20):
            self.client.post(url, {'bevestig': '0', 'afmelden': '1', 'snel': 1})
        self.assertEqual(CompetitieMutatie.objects.count(), 1)

        # bevestigen mag niet, want geen lid bij vereniging
        with self.assert_max_queries(20):
            self.client.post(url, {'bevestig': '1', 'afmelden': '0', 'snel': 1})
        self.assertEqual(CompetitieMutatie.objects.count(), 1)

        # verbouw 'time' en voer een test uit zonder 'snel'
        time.sleep = self._dummy_sleep
        with self.assert_max_queries(20):
            self.client.post(url, {'bevestig': '0', 'afmelden': '1'})
        time.sleep = sleep_oud
        self.assertEqual(CompetitieMutatie.objects.count(), 2)

    def test_wijzig_status_hwl(self):
        # HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        zet_competitie_fase_rk_prep(self.comp_18)

        deelnemer = KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                             sporterboog=self.sporterboog,
                                             bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                             indiv_klasse=self.klasse_r)
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

        sporter = self.sporterboog.sporter
        sporter.bij_vereniging = self.ver_1100
        sporter.save()

        deelnemer = KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                             sporterboog=self.sporterboog,
                                             bij_vereniging=self.ver_1100,
                                             indiv_klasse=self.klasse_r)
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
        resp = self.client.get(url)
        self.assert403(resp)

        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        url = self.url_wijzig_limiet % self.deelkamp_rayon1_18.pk
        isel = 'isel_%s' % self.klasse_c.pk
        tsel = 'tsel_%s' % self.klasse_r_ere.pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 'xx'})
        self.assertEqual(resp.status_code, 302)     # doorloopt alles

        with self.assert_max_queries(20):
            resp = self.client.post(url, {tsel: 'xx'})
        self.assertEqual(resp.status_code, 302)     # doorloopt alles

        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: '19'})
        self.assert404(resp, 'Geen valide keuze voor indiv')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {tsel: '19'})
        self.assert404(resp, 'Geen valide keuze voor team')

        # verkeerde RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        url = self.url_wijzig_limiet % self.deelkamp_rayon1_18.pk

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
        url = self.url_wijzig_limiet % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-limieten-rk.dtl', 'design/site_layout.dtl'))

        isel = 'isel_%s' % self.klasse_r.pk
        tsel = 'tsel_%s' % self.klasse_r_ere.pk

        # limiet op default zetten
        self.assertEqual(KampioenschapIndivKlasseLimiet.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 24, tsel: 12, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(KampioenschapIndivKlasseLimiet.objects.count(), 0)

        # limiet zetten
        self.assertEqual(KampioenschapIndivKlasseLimiet.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 20, tsel: 10, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertEqual(KampioenschapIndivKlasseLimiet.objects.count(), 1)

        # limiet opnieuw zetten, geen wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 20, tsel: 10, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertEqual(KampioenschapIndivKlasseLimiet.objects.count(), 1)

        # limiet aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 16, tsel: 8, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertEqual(KampioenschapIndivKlasseLimiet.objects.count(), 1)

        # met limiet aanwezig
        url = self.url_wijzig_limiet % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # limiet verwijderen, zonder 'snel'
        time.sleep = self._dummy_sleep
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 24})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertEqual(KampioenschapIndivKlasseLimiet.objects.count(), 0)
        time.sleep = sleep_oud

        # nu met een deelnemer, zodat de mutatie opgestart wordt
        deelnemer = KampioenschapSporterBoog(kampioenschap=self.deelkamp_rayon1_18,
                                             sporterboog=self.sporterboog,
                                             bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                             indiv_klasse=self.klasse_r)
        deelnemer.save()

        aantal = CompetitieMutatie.objects.count()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 4, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertGreater(CompetitieMutatie.objects.count(), aantal)


# end of file
