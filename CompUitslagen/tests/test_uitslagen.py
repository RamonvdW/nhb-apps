# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.tests.test_helpers import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData
import datetime


class TestCompUitslagen(E2EHelpers, TestCase):

    """ tests voor de CompUitslagen applicatie, module Uitslagen """

    test_after = ('Competitie.tests.test_fase', 'Competitie.tests.test_beheerders')

    url_overzicht = '/bondscompetities/%s/'
    url_uitslagen_regio = '/bondscompetities/uitslagen/%s/%s/%s/regio-individueel/'                 # comp_pk, comp_boog
    url_uitslagen_regio_n = '/bondscompetities/uitslagen/%s/%s/%s/regio-individueel/%s/'            # comp_pk, comp_boog, regio_nr
    url_uitslagen_regio_teams = '/bondscompetities/uitslagen/%s/%s/regio-teams/'                    # comp_pk, team_type
    url_uitslagen_regio_teams_n = '/bondscompetities/uitslagen/%s/%s/regio-teams/%s/'               # comp_pk, team_type, regio_nr
    url_uitslagen_ver = '/bondscompetities/uitslagen/%s/%s/vereniging/'                             # comp_pk, comp_boog
    url_uitslagen_indiv_ver_n = '/bondscompetities/uitslagen/%s/%s/vereniging/%s/individueel/'      # comp_bk, boog_type, ver_nr
    url_uitslagen_teams_ver_n = '/bondscompetities/uitslagen/%s/%s/vereniging/%s/teams/'            # comp_pk, team_type, ver_nr

    url_uitslagen_rayon = '/bondscompetities/uitslagen/%s/%s/rayon-individueel/'                    # comp_pk, comp_boog
    url_uitslagen_rayon_n = '/bondscompetities/uitslagen/%s/%s/rayon-individueel/%s/'               # comp_pk, comp_boog, rayon_nr
    url_uitslagen_rayon_teams = '/bondscompetities/uitslagen/%s/%s/rayon-teams/'                    # comp_pk, team_type
    url_uitslagen_rayon_teams_n = '/bondscompetities/uitslagen/%s/%s/rayon-teams/%s/'               # comp_pk, team_type, rayon_nr
    url_uitslagen_bond = '/bondscompetities/uitslagen/%s/%s/bond/'                                  # comp_pk, comp_boog

    regio_nr = 101
    ver_nr = 0      # wordt in setupTestData ingevuld
    club_naam = ''  # wordt in setupTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('CompUitslagen: populating testdata start')
        s1 = timezone.now()
        cls.testdata = TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][2]
        cls.club_naam = '[%s] Club %s' % (cls.ver_nr, cls.ver_nr)
        #cls.testdata.maak_sporterboog_aanvangsgemiddelden(18, cls.ver_nr)
        #cls.testdata.maak_sporterboog_aanvangsgemiddelden(25, cls.ver_nr)
        cls.testdata.maak_bondscompetities()
        #cls.testdata.maak_inschrijvingen_regiocompetitie(18, ver_nr=cls.ver_nr)
        #cls.testdata.maak_inschrijvingen_regiocompetitie(25, ver_nr=cls.ver_nr)
        #cls.testdata.maak_inschrijvingen_regio_teamcompetitie(18, ver_nr=cls.ver_nr)
        #cls.testdata.maak_inschrijvingen_regio_teamcompetitie(25, ver_nr=cls.ver_nr)
        #cls.testdata.maak_poules(cls.testdata.deelcomp18_regio[cls.regio_nr])
        #cls.testdata.maak_poules(cls.testdata.deelcomp25_regio[cls.regio_nr])
        #cls.testdata.regio_teamcompetitie_ronde_doorzetten(cls.testdata.deelcomp18_regio[cls.regio_nr])
        s2 = timezone.now()
        d = s2 - s1
        print('CompUitslagen: populating testdata took %s seconds' % d.seconds)

    def test_anon(self):
        self.client.logout()

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

        url = self.url_uitslagen_regio_teams % (self.testdata.comp18.pk, 'R2')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 'TR', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_rayon % (self.testdata.comp18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_rayon_n % (self.testdata.comp18.pk, 'R', 2))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_bond % (self.testdata.comp18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk.dtl', 'plein/site_layout.dtl'))

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


# end of file
