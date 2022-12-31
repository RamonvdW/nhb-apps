# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import Competitie, KampioenschapTeam, DeelKampioenschap, DEEL_RK
from Competitie.operations import competities_aanmaken
from Competitie.tests.test_fase import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData


class TestCompLaagRayonTeams(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, RK Teams functie """

    test_after = ('Competitie.tests.test_fase', 'Competitie.tests.test_beheerders', 'Competitie.tests.test_competitie')

    url_rko_teams = '/bondscompetities/rk/ingeschreven-teams/%s/'            # deelkamp_pk
    url_rk_teams_alle = '/bondscompetities/rk/ingeschreven-teams/%s/%s/'     # comp_pk, subset
    url_doorzetten_rk = '/bondscompetities/beheer/%s/doorzetten-rk/'                                       # comp_pk
    url_teams_klassengrenzen_vaststellen = '/bondscompetities/rk/%s/rk-bk-teams-klassengrenzen/vaststellen/'     # comp_pk

    regio_nr = 101
    ver_nr = 0      # wordt in setupTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('CompLaagRayon.test_teams_rko: populating testdata start')
        s1 = timezone.now()
        cls.testdata = TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[101][2]
        cls.testdata.maak_bondscompetities()
        s2 = timezone.now()
        d = s2 - s1
        print('CompLaagRayon.test_teams_rko: populating testdata took %s seconds' % d.seconds)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        competities_aanmaken(jaar=2019)

        self.deelkamp_rk1 = DeelKampioenschap.objects.get(deel=DEEL_RK, competitie=self.testdata.comp18, nhb_rayon__rayon_nr=1)

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
        self.assert_template_used(resp, ('complaagrayon/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wordt BKO
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # specifiek rayon
        url = self.url_rk_teams_alle % (self.testdata.comp18.pk, '1')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/rko-teams.dtl', 'plein/site_layout.dtl'))
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
        self.testdata.maak_rk_deelnemers(25, self.ver_nr, self.regio_nr)
        self.testdata.maak_inschrijvingen_rk_teamcompetitie(25, self.ver_nr)

        url = self.url_rko_teams % self.testdata.deelkamp25_rk[1].pk        # rayon 1

        # anon
        resp = self.client.get(url)
        self.assert403(resp)            # alleen de RKO mag deze pagina ophalen

        # wordt RKO van rayon 1
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_rko[1])

        # pagina ophalen zonder vastgestelde team klassen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(url)

        # wordt BKO
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)

        # stel de RK/BK klassegrenzen vast
        zet_competitie_fase(self.testdata.comp25, 'J')
        resp = self.client.post(self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk)
        self.assert_is_redirect_not_plein(resp)

        # verpruts de klasse van 1 team
        team = KampioenschapTeam.objects.get(pk=self.testdata.comp25_kampioenschapteams[0].pk)
        for klasse in self.testdata.comp25_klassen_team['R2']:          # pragma: no branch
            if not klasse.is_voor_teams_rk_bk:                          # pragma: no branch
                team.team_klasse = klasse
                team.save(update_fields=['team_klasse'])
                break   # from the for
        # for

        # wordt RKO van rayon 1
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_rko[1])

        # pagina ophalen met vastgestelde team klassen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/rko-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(url)

        # bad urls
        resp = self.client.get(self.url_rko_teams % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_rko_teams % 'xyz')
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # verkeerde rayon
        url = self.url_rko_teams % self.testdata.deelkamp25_rk[2].pk
        resp = self.client.get(url)
        self.assert403(resp)

    def test_rk_bk_klassengrenzen(self):
        # maak een paar teams aan
        self.testdata.maak_voorinschrijvingen_rk_teamcompetitie(25, self.ver_nr, ook_incomplete_teams=False)
        self.testdata.geef_rk_team_tijdelijke_sporters_genoeg_scores(25, self.ver_nr)

        # als BKO doorzetten naar RK fase (G --> J) en bepaal de klassengrenzen (fase J --> K)
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        zet_competitie_fase(self.testdata.comp25, 'G')

        url = self.url_teams_klassengrenzen_vaststellen % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet in de juiste fase')
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet in de juiste fase')

        url = self.url_doorzetten_rk % self.testdata.comp25.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.verwerk_regiocomp_mutaties()

        comp = Competitie.objects.get(pk=self.testdata.comp25.pk)
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'J')

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/bko-klassengrenzen-vaststellen-rk-bk-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.get(url)
        self.assert404(resp, 'De klassengrenzen zijn al vastgesteld')
        resp = self.client.post(url)
        self.assert404(resp, 'De klassengrenzen zijn al vastgesteld')


# end of file
