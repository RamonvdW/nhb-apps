# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import DeelCompetitie, LAAG_RK
from .operations import competities_aanmaken
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompetitieRegioTeams(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    url_rko_teams = '/bondscompetities/rk/%s/teams/'            # rk_deelcomp_pk
    url_rk_teams_alle = '/bondscompetities/rk/%s/teams/%s/'     # comp_pk, subset

    testdata = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_bondscompetities()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        competities_aanmaken(jaar=2019)

        self.rk_deelcomp_1 = DeelCompetitie.objects.get(laag=LAAG_RK, competitie=self.testdata.comp18, nhb_rayon__rayon_nr=1)

    def test_rk_teams_alle(self):
        # BB en BKO mogen deze pagina ophalen

        url = self.url_rk_teams_alle % (self.testdata.comp18.pk, 'auto')

        # anon
        resp = self.client.get(url)
        self.assert403(resp)

        # wordt BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('competitie/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wordt BKO
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('competitie/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # specifiek rayon
        url = self.url_rk_teams_alle % (self.testdata.comp18.pk, '1')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('competitie/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(url)

        # bad urls
        url = self.url_rk_teams_alle % (999999, 'alle')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_rk_teams_alle % ('xyz', 'alle')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_rk_teams_alle % (self.testdata.comp18.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Selectie wordt niet ondersteund')

        url = self.url_rk_teams_alle % (self.testdata.comp18.pk, 'xyz')
        resp = self.client.get(url)
        self.assert404(resp, 'Selectie wordt niet ondersteund')

        # wordt RKO
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rko[1])
        url = self.url_rk_teams_alle % (self.testdata.comp18.pk, 'auto')
        resp = self.client.get(url)
        self.assert403(resp)        # RKO heeft andere ingang

    def test_rko_teams(self):
        # alleen de RKO mag deze pagina ophalen
        url = self.url_rko_teams % self.testdata.deelcomp25_rk[1].pk

        # anon
        resp = self.client.get(url)
        self.assert403(resp)

        # wordt RKO
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_rko[1])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('competitie/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(url)

        # bad urls
        resp = self.client.get(self.url_rko_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_rko_teams % 'xyz')
        self.assert404(resp, 'Competitie niet gevonden')

        # verkeerde rayon
        url = self.url_rko_teams % self.testdata.deelcomp25_rk[2].pk
        resp = self.client.get(url)
        self.assert403(resp)


# end of file
