# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData


class TestCompUitslagenVer(E2EHelpers, TestCase):

    """ tests voor de CompUitslagen applicatie, module Uitslagen """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_overzicht = '/bondscompetities/%s/'
    url_uitslagen_ver = '/bondscompetities/uitslagen/%s/vereniging/%s/'                             # comp_pk, comp_boog
    url_uitslagen_indiv_ver_n = '/bondscompetities/uitslagen/%s/vereniging/%s/individueel/%s/'      # comp_bk, ver_nr, boog_type
    url_uitslagen_teams_ver_n = '/bondscompetities/uitslagen/%s/vereniging/%s/teams/%s/'            # comp_pk, ver_nr, team_type

    regio_nr = 101
    ver_nr = 0      # wordt in setUpTestData ingevuld
    club_naam = ''  # wordt in setUpTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][2]
        cls.club_naam = '[%s] Club %s' % (cls.ver_nr, cls.ver_nr)
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(18, cls.ver_nr)
        # cls.testdata.maak_sporterboog_aanvangsgemiddelden(25, cls.ver_nr)
        cls.testdata.maak_bondscompetities()
        cls.testdata.maak_inschrijvingen_regiocompetitie(18, ver_nr=cls.ver_nr)
        # cls.testdata.maak_inschrijvingen_regiocompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regio_teamcompetitie(18, ver_nr=cls.ver_nr)
        # cls.testdata.maak_inschrijvingen_regio_teamcompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_poules(cls.testdata.deelcomp18_regio[cls.regio_nr])
        # cls.testdata.maak_poules(cls.testdata.deelcomp25_regio[cls.regio_nr])
        cls.testdata.regio_teamcompetitie_ronde_doorzetten(cls.testdata.deelcomp18_regio[cls.regio_nr])
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def test_ver_indiv(self):
        # anon
        self.client.logout()
        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, self.ver_nr, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'design/site_layout.dtl'))

        # als je de pagina ophaalt als een ingelogd lid, dan wordt jouw vereniging getoond
        sporter = self.testdata.ver_sporters_met_account[self.ver_nr][0]
        self.e2e_login(sporter.account)

        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.club_naam)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'design/site_layout.dtl'))

        # corner-case: geen lid meer bent bij een vereniging
        sporter.is_actief_lid = False
        sporter.save(update_fields=['is_actief_lid'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'design/site_layout.dtl'))

    def test_ver_teams(self):
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, self.ver_nr, 'R2')
        with self.assert_max_queries(82):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-teams.dtl', 'design/site_layout.dtl'))

        # bad comp_pk
        url = self.url_uitslagen_teams_ver_n % (999999, self.ver_nr, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # bad ver_nr
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, 'xxx', 'R2')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd verenigingsnummer')

        # niet bestaande ver_nr
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, 999999, 'R2')
        resp = self.client.get(url)
        self.assert404(resp, 'Vereniging niet gevonden')

        # bad team type
        url = self.url_uitslagen_teams_ver_n % (self.testdata.comp18.pk, self.ver_nr, 'xxx')
        resp = self.client.get(url)
        self.assert404(resp, 'Team type niet bekend')

    def test_hwl(self):
        functie = self.testdata.functie_hwl[self.ver_nr]
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(functie)

        # als je de pagina ophaalt als functie SEC/HWL/WL, dan krijg je die vereniging
        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, self.club_naam)

        # bad
        url = self.url_uitslagen_ver % ('x', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_ver % (self.testdata.comp18.pk, 'x')
        resp = self.client.get(url)
        self.assert404(resp, 'Boogtype niet bekend')

    def test_regio_100(self):
        ver_nr = self.testdata.regio_ver_nrs[100][0]
        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, ver_nr, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-vereniging-indiv.dtl', 'design/site_layout.dtl'))

        # bad
        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, 999999, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Vereniging niet gevonden')

        url = self.url_uitslagen_indiv_ver_n % (self.testdata.comp18.pk, 'nan', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerd verenigingsnummer')

# end of file
