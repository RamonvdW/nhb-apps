# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.definities import DEEL_RK
from Competitie.models import KampioenschapTeam, Kampioenschap
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData


class TestCompLaagRayonTeams(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, RK Teams functie """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_rko_teams = '/bondscompetities/rk/ingeschreven-teams/%s/'                           # deelkamp_pk
    url_rk_teams_alle = '/bondscompetities/rk/ingeschreven-teams/%s/%s/'                    # comp_pk, subset
    url_teams_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/'  # comp_pk

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
        cls.testdata.maak_bondscompetities()
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.deelkamp_rk1 = Kampioenschap.objects.get(deel=DEEL_RK, competitie=self.testdata.comp18, rayon__rayon_nr=1)

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
        self.testdata.maak_rk_teams(25, self.ver_nr)

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

        # stel de RK/BK klassengrenzen vast
        zet_competitie_fase_rk_prep(self.testdata.comp25)
        resp = self.client.post(self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk)
        self.assert_is_redirect_not_plein(resp)

        # verpruts de klasse van 1 team
        team = KampioenschapTeam.objects.get(pk=self.testdata.comp25_kampioenschapteams[0].pk)
        for klasse in self.testdata.comp25_klassen_teams['R2']:         # pragma: no branch
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

    def test_admin(self):
        # admin filter with actual records
        account = self.testdata.account_admin
        account.is_superuser = True      # toegang tot admin interface
        account.save(update_fields=['is_superuser'])
        self.e2e_login_and_pass_otp(account)

        # without filter selection
        resp = self.client.get('/beheer/Competitie/kampioenschapteam/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # with filter selection
        resp = self.client.get('/beheer/Competitie/kampioenschapteam/?rk_bk_type=RK')
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        resp = self.client.get('/beheer/Competitie/kampioenschapteam/?rk_bk_type=BK')
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        resp = self.client.get('/beheer/Competitie/kampioenschapteam/?incompleet=incompleet')
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        resp = self.client.get('/beheer/Competitie/kampioenschapteam/?incompleet=compleet')
        self.assertEqual(resp.status_code, 200)  # 200 = OK


# end of file
