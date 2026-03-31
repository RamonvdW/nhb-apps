# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMutatie
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import (evaluatie_datum, zet_competitie_fase_rk_prep,
                                            zet_competitie_fase_bk_prep)
from CompLaagRayon.models import KampRK, DeelnemerRK, CutRK, CutTeamRK
from Geo.models import Rayon, Regio
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime
import time

sleep_oud = time.sleep


class TestCompLaagRayonLimieten(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, Planning functie """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_wijzig_limiet_indiv = '/bondscompetities/rk/planning/%s/individuele-limieten/'          # kamp_rk.pk
    url_wijzig_limiet_teams = '/bondscompetities/rk/planning/%s/teams-limieten/'                # kamp_rk.pk
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

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_sporter = self._prep_beheerder_lid('Sporter')
        self.lid_sporter = Sporter.objects.get(lid_nr=self.account_sporter.username)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.sporterboog = SporterBoog(sporter=self.lid_sporter,
                                       boogtype=self.boog_r,
                                       voor_wedstrijd=True)
        self.sporterboog.save()

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

        self.deelkamp_rayon1_18 = KampRK.objects.filter(competitie=self.comp_18, rayon=self.rayon_1).first()
        self.deelkamp_rayon2_18 = KampRK.objects.filter(competitie=self.comp_18, rayon=self.rayon_2).first()

        self.functie_rko1_18 = self.deelkamp_rayon1_18.functie
        self.functie_rko2_18 = self.deelkamp_rayon2_18.functie

        self.functie_rko1_18.accounts.add(self.account_rko1_18)
        self.functie_rko2_18.accounts.add(self.account_rko2_18)

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

    def test_bad_indiv(self):
        self.client.logout()
        url = self.url_wijzig_limiet_indiv % 999999
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

        url = self.url_wijzig_limiet_indiv % self.deelkamp_rayon1_18.pk
        isel = 'isel_%s' % self.klasse_c.pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 'xx'})
        self.assertEqual(resp.status_code, 302)     # doorloopt alles

        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: '19'})
        self.assert404(resp, 'Geen valide keuze voor indiv')

        # verkeerde fase
        zet_competitie_fase_bk_prep(self.comp_18)

        # controleer dat de "opslaan" url niet aangeboden wordt
        resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(urls, [])

        resp = self.client.post(url)
        self.assert404(resp, 'Wijzigen kan niet meer')

        zet_competitie_fase_rk_prep(self.comp_18)

        # verkeerde RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        url = self.url_wijzig_limiet_indiv % self.deelkamp_rayon1_18.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_wijzig_indiv(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        # zonder limiet aanwezig
        url = self.url_wijzig_limiet_indiv % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-limieten-indiv.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertTrue(len(urls), 1)
        self.assertTrue('/individuele-limieten/' in urls[0])

        isel = 'isel_%s' % self.klasse_r.pk

        # limiet op default zetten
        self.assertEqual(CutRK.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 24, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.assertEqual(CutRK.objects.count(), 0)

        # limiet zetten
        self.assertEqual(CutRK.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 20, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertEqual(CutRK.objects.count(), 1)

        # limiet opnieuw zetten, geen wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 20, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertEqual(CutRK.objects.count(), 1)

        # limiet aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel: 16, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)  # check for success
        self.verwerk_competitie_mutaties()
        self.assertEqual(CutRK.objects.count(), 1)

        # met limiet aanwezig
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
        self.assertEqual(CutRK.objects.count(), 0)
        time.sleep = sleep_oud

        # nu met een deelnemer, zodat de mutatie opgestart wordt
        deelnemer = DeelnemerRK(kamp=self.deelkamp_rayon1_18,
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

    def test_wijzig_team(self):
        # RKO
        self.e2e_login_and_pass_otp(self.account_rko1_18)
        self.e2e_wissel_naar_functie(self.functie_rko1_18)

        url = self.url_wijzig_limiet_teams % 99999
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')
        resp = self.client.post(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # geen CutTeamRK record aanwezig
        self.assertEqual(CutTeamRK.objects.count(), 0)
        url = self.url_wijzig_limiet_teams % self.deelkamp_rayon1_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-limieten-teams.dtl', 'design/site_layout.dtl'))

        # geen wijzigingen
        resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect_not_plein(resp)

        # slecht wijziging
        tsel = 'tsel_%s' % self.klasse_r_ere.pk
        resp = self.client.post(url, {tsel: 1, 'snel': 1})
        self.assert404(resp, 'Geen valide keuze')

        self.assertEqual(CutTeamRK.objects.count(), 0)
        resp = self.client.post(url, {tsel: 4, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)
        self.verwerk_competitie_mutaties()
        self.assertEqual(CutTeamRK.objects.count(), 1)

        # wijziging naar dezelfde waarde
        resp = self.client.post(url, {tsel: 4, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.post(url, {tsel: 8, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)

        # slechtg getal
        resp = self.client.post(url, {tsel: 'xxx', 'snel': 1})
        self.assert_is_redirect_not_plein(resp)

        # verkeerde fase
        zet_competitie_fase_bk_prep(self.comp_18)

        # controleer dat de "opslaan" url niet aangeboden wordt
        resp = self.client.get(url)
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(urls, [])

        resp = self.client.post(url)
        self.assert404(resp, 'Wijzigen kan niet meer')

        zet_competitie_fase_rk_prep(self.comp_18)

        # verkeerde RKO
        self.e2e_login_and_pass_otp(self.account_rko2_18)
        self.e2e_wissel_naar_functie(self.functie_rko2_18)

        url = self.url_wijzig_limiet_teams % self.deelkamp_rayon1_18.pk
        resp = self.client.get(url)
        self.assert403(resp, 'Niet de beheerder')
        resp = self.client.post(url)
        self.assert403(resp, 'Niet de beheerder')


# end of file
