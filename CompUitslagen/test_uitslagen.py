# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData
import datetime


class TestCompUitslagen(E2EHelpers, TestCase):

    """ tests voor de CompUitslagen applicatie, module Uitslagen """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    url_overzicht = '/bondscompetities/%s/'
    url_uitslagen_regio = '/bondscompetities/uitslagen/%s/%s/%s/regio-individueel/'                 # comp_pk, comp_boog
    url_uitslagen_regio_n = '/bondscompetities/uitslagen/%s/%s/%s/regio-individueel/%s/'            # comp_pk, comp_boog, regio_nr
    url_uitslagen_regio_teams = '/bondscompetities/uitslagen/%s/%s/regio-teams/'                    # comp_pk, team_type
    url_uitslagen_regio_teams_n = '/bondscompetities/uitslagen/%s/%s/regio-teams/%s/'               # comp_pk, team_type, regio_nr
    url_uitslagen_rayon = '/bondscompetities/uitslagen/%s/%s/rayon-individueel/'                    # comp_pk, comp_boog
    url_uitslagen_rayon_n = '/bondscompetities/uitslagen/%s/%s/rayon-individueel/%s/'               # comp_pk, comp_boog, rayon_nr
    url_uitslagen_bond = '/bondscompetities/uitslagen/%s/%s/bond/'                                  # comp_pk, comp_boog
    url_uitslagen_ver = '/bondscompetities/uitslagen/%s/%s/vereniging/'                             # comp_pk, comp_boog
    url_uitslagen_indiv_ver_n = '/bondscompetities/uitslagen/%s/%s/vereniging/%s/individueel/'      # comp_bk, boog_type, ver_nr
    url_uitslagen_teams_ver_n = '/bondscompetities/uitslagen/%s/%s/vereniging/%s/teams/'            # comp_pk, team_type, ver_nr

    ver_nr = 1012  # regio 101, vereniging 2
    club_naam = '[%s] Club %s' % (ver_nr, ver_nr)

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('CompUitslagen: populating testdata start')
        s1 = timezone.now()
        cls.testdata = TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(18, cls.ver_nr)
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(25, cls.ver_nr)
        cls.testdata.maak_bondscompetities()
        cls.testdata.maak_inschrijvingen_regiocompetitie(18, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regiocompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regio_teamcompetitie(18, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regio_teamcompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_poules(cls.testdata.deelcomp18_regio[101])
        cls.testdata.maak_poules(cls.testdata.deelcomp25_regio[101])
        cls.testdata.regio_teamcompetitie_ronde_doorzetten(cls.testdata.deelcomp18_regio[101])
        s2 = timezone.now()
        d = s2 - s1
        print('CompUitslagen: populating testdata took %s seconds' % d.seconds)

    def test_top(self):
        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        way_before = datetime.date(year=2018, month=1, day=1)   # must be before timezone.now()

        comp = self.testdata.comp25

        # fase A
        comp.begin_aanmeldingen = now + datetime.timedelta(days=1)      # morgen
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase < 'B', msg="comp.fase=%s (expected: below B)" % comp.fase)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in prep fase (B+)
        comp.begin_aanmeldingen = way_before   # fase B
        comp.einde_aanmeldingen = way_before   # fase C
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase >= 'B')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in scorende fase (E+)
        comp.einde_teamvorming = way_before    # fase D
        comp.eerste_wedstrijd = way_before     # fase E
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase >= 'E')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_regio(self):
        # als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        url = self.url_uitslagen_regio % (self.testdata.comp18.pk, 'R', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_n % (self.testdata.comp18.pk, 'IB', 'alle', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_regio_teams % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(70):       # TODO: reduceer
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'IB', 101)
        with self.assert_max_queries(46):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # als BKO
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        url = self.url_uitslagen_regio % (self.testdata.comp18.pk, 'C', 'zes')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als RKO
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rko[1])
        url = self.url_uitslagen_regio % (self.testdata.comp25.pk, 'IB', 'maakt-niet-uit')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als RCL
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[102])
        url = self.url_uitslagen_regio % (self.testdata.comp25.pk, 'LB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als HWL
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])
        url = self.url_uitslagen_regio % (self.testdata.comp25.pk, 'R', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als bezoeker
        self.client.logout()
        url = self.url_uitslagen_regio % (self.testdata.comp25.pk, 'LB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als Sporter
        sporter = self.testdata.ver_sporters_met_account[self.ver_nr][0]
        self.e2e_login(sporter.account)
        url = self.url_uitslagen_regio % (self.testdata.comp25.pk, 'BB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # slecht boog type
        url = self.url_uitslagen_regio % (self.testdata.comp25.pk, 'XXX', 'alle')
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

    def test_regio_n(self):
        url = self.url_uitslagen_regio_n % (self.testdata.comp18.pk, 'R', 'alle', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_regio_n % (self.testdata.comp25.pk, 'LB', 'alle', 116)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # regio 100 is valide maar heeft geen deelcompetitie
        url = self.url_uitslagen_regio_n % (self.testdata.comp18.pk, 'R', 'alle', 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # bad
        url = self.url_uitslagen_regio_n % (self.testdata.comp18.pk, 'R', 'alle', 999)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_regio_n % (self.testdata.comp18.pk, 'R', 'alle', "NaN")
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd regionummer')

        url = self.url_uitslagen_regio_n % (self.testdata.comp18.pk, 'BAD', 'alle', 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

        url = self.url_uitslagen_regio_n % (99, 'r', 'alle', 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_regio_n % ('X', 'r', 'alle', 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_rayon(self):
        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

        # slecht boogtype
        url = self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'XXX')
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

        url = self.url_uitslagen_rayon % ('x', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_rayon % (99, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_rayon_n(self):
        url = self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'IB', 1)      # bevat onze enige deelnemer met 6 scores
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'R', 'x')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd rayonnummer')

        url = self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'R', '0')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_bond(self):
        url = self.url_uitslagen_bond % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bond.dtl', 'plein/site_layout.dtl'))

        # illegale parameters
        url = self.url_uitslagen_bond % ('x', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_bond % (99, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # BK voor al afgesloten competitie
        comp = self.testdata.comp18
        comp.is_afgesloten = True
        comp.save(update_fields=['is_afgesloten'])
        url = self.url_uitslagen_bond % (comp.pk, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_ver_indiv(self):
        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, 'R', self.ver_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        # als je de pagina ophaalt als een ingelogd lid, dan krijg je je eigen vereniging
        sporter = self.testdata.ver_sporters_met_account[self.ver_nr][0]
        self.e2e_login(sporter.account)

        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.club_naam)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        # tenzij je geen lid meer bent bij een vereniging
        sporter.is_actief_lid = False
        sporter.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

    def test_ver_team(self):
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, 'R', self.ver_nr)
        with self.assert_max_queries(73):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-teams.dtl', 'plein/site_layout.dtl'))

        # bad comp_pk
        url = self.url_uitslagen_teams_ver_n % (999999, 'R', self.ver_nr)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # bad ver_nr
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, 'R', 'xxx')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd verenigingsnummer')

        # niet bestaande ver_nr
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, 'R', 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Vereniging niet gevonden')

        # bad team type
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, 'xxx', self.ver_nr)
        resp = self.client.get(url)
        self.assert404(resp, 'Team type niet bekend')

    def test_vereniging_hwl(self):
        functie = self.testdata.functie_hwl[self.ver_nr]
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(functie)

        # als je de pagina ophaalt als functie SEC/HWL/WL, dan krijg je die vereniging
        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, self.club_naam)

        # bad
        url = self.url_uitslagen_ver % ('x', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'x')
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

    def test_vereniging_regio_100(self):
        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, 'R', 1001)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        # bad
        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, 'R', 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Vereniging niet gevonden')

        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, 'R', 'nan')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd verenigingsnummer')

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % self.testdata.comp18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_regio % (self.testdata.comp18.pk, 'R', 'alle'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_regio_n % (self.testdata.comp18.pk, 'R', 'alle', 111))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_regio_teams % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(68):       # TODO: reduceer
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'IB', 101)
        with self.assert_max_queries(44):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'R', 2))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_bond % (self.testdata.comp18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bond.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_ver % (self.testdata.comp18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, 'R', self.ver_nr))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

    def test_teams(self):
        url = self.url_uitslagen_regio_teams % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(68):       # TODO: reduceer
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # bad
        url = self.url_uitslagen_regio_teams % ('X', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # regio 100 --> 101
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'R', 100)
        with self.assert_max_queries(68):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # bad regio nr
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'R', "NaN")
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd regionummer')

        # niet bestaande regio
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'R', 99999)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # verkeerd team type
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'X', 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd team type')

        # regio 101 heeft teams in een poule
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'R', 101)
        with self.assert_max_queries(68):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

# end of file
