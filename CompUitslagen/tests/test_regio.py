# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData


class TestCompUitslagenRegio(E2EHelpers, TestCase):

    """ tests voor de CompUitslagen applicatie, module Regio Uitslagen """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_uitslagen_regio_indiv = '/bondscompetities/uitslagen/%s/regio-individueel/%s/'        # comp, boog
    url_uitslagen_regio_indiv_n = '/bondscompetities/uitslagen/%s/regio-individueel/%s/%s/'   # comp, regio_nr, boog
    url_uitslagen_regio_teams = '/bondscompetities/uitslagen/%s/regio-teams/%s/'              # comp, team
    url_uitslagen_regio_teams_n = '/bondscompetities/uitslagen/%s/regio-teams/%s/%s/'         # comp, regio_nr, team

    regio_nr = 101
    ver_nr = 0      # wordt in setUpTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][2]
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(18, cls.ver_nr)
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(25, cls.ver_nr)
        cls.testdata.maak_bondscompetities()
        cls.testdata.maak_inschrijvingen_regiocompetitie(18, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regiocompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regio_teamcompetitie(18, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regio_teamcompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_poules(cls.testdata.deelcomp18_regio[cls.regio_nr])
        cls.testdata.maak_poules(cls.testdata.deelcomp25_regio[cls.regio_nr])
        cls.testdata.regio_teamcompetitie_ronde_doorzetten(cls.testdata.deelcomp18_regio[cls.regio_nr])
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def test_regio(self):
        # als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        url = self.url_uitslagen_regio_indiv % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_indiv_n % (self.testdata.comp18.pk, 101, 'TR')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_uitslagen_regio_teams % (self.testdata.comp18.pk, 'R2')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-teams.dtl', 'design/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 101, 'TR')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-teams.dtl', 'design/site_layout.dtl'))

        # als BKO
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        url = self.url_uitslagen_regio_indiv % (self.testdata.comp18.pk, 'C')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # als RKO
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rko[1])
        url = self.url_uitslagen_regio_indiv % (self.testdata.comp25.pk, 'TR')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # als RCL
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[102])
        url = self.url_uitslagen_regio_indiv % (self.testdata.comp25.pk, 'LB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # als HWL
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])
        url = self.url_uitslagen_regio_indiv % (self.testdata.comp25.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # als bezoeker
        self.client.logout()
        url = self.url_uitslagen_regio_indiv % (self.testdata.comp25.pk, 'LB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # als Sporter
        sporter = self.testdata.ver_sporters_met_account[self.ver_nr][0]
        self.e2e_login(sporter.account)
        url = self.url_uitslagen_regio_indiv % (self.testdata.comp25.pk, 'BB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # slecht boog type
        url = self.url_uitslagen_regio_indiv % (self.testdata.comp25.pk, 'XXX')
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

    def test_regio_n(self):
        url = self.url_uitslagen_regio_indiv_n % (self.testdata.comp18.pk, 101, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_uitslagen_regio_indiv_n % (self.testdata.comp25.pk, 116, 'LB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # regio 100 is valide, maar heeft geen regiocompetitie
        url = self.url_uitslagen_regio_indiv_n % (self.testdata.comp18.pk, 100, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-indiv.dtl', 'design/site_layout.dtl'))

        # bad
        url = self.url_uitslagen_regio_indiv_n % (self.testdata.comp18.pk, 999, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_regio_indiv_n % (self.testdata.comp18.pk, "NaN", 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde regionummer')

        url = self.url_uitslagen_regio_indiv_n % (self.testdata.comp18.pk, 101, 'BAD')
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

        url = self.url_uitslagen_regio_indiv_n % (99, 'r', 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_regio_indiv_n % ('X', 'r', 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_teams(self):
        url = self.url_uitslagen_regio_teams % (self.testdata.comp18.pk, 'R2')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-teams.dtl', 'design/site_layout.dtl'))

        # bad
        url = self.url_uitslagen_regio_teams % ('X', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # regio 100 --> 101
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 100, 'R2')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-teams.dtl', 'design/site_layout.dtl'))

        # bad regio nr
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, "NaN", 'R2')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd regionummer')

        # niet bestaande regio
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 99999, 'R2')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # verkeerd team type
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 101, 'X')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd team type')

        # regio 101 heeft teams in een poule
        url = self.url_uitslagen_regio_teams_n % (self.testdata.comp18.pk, 101, 'R2')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/regio-teams.dtl', 'design/site_layout.dtl'))

    def test_hist(self):
        # test redirect naar HistComp uitslag
        resp = self.client.get(self.url_uitslagen_regio_indiv % ('indoor-2000-2001', 'r'))
        self.assert_is_redirect(resp, '/bondscompetities/hist/2000-2001/indoor-individueel/recurve/regio/')

        resp = self.client.get(self.url_uitslagen_regio_teams % ('25m1pijl-2000-2001', 'c'))
        self.assert_is_redirect(resp, '/bondscompetities/hist/2000-2001/25m1pijl-teams/compound/regio/')


# end of file
