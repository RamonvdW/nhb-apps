# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.definities import DEELNAME_JA, DEELNAME_NEE, DEELNAME_ONBEKEND
from Competitie.models import KampioenschapTeam
from Competitie.test_utils.tijdlijn import (zet_competitie_fase_bk_wedstrijden, zet_competitie_fase_bk_prep,
                                            zet_competitie_fase_rk_wedstrijden)
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompetitiePlanningBond(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, beheer BK teams """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_lijst_bk_teams = '/bondscompetities/bk/teams/%s/'                            # deelkamp_pk
    url_wijzig_status_bk_team = '/bondscompetities/bk/teams/wijzig-status-bk-team/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        for regio_nr in (111, 113):
            ver_nr = data.regio_ver_nrs[regio_nr][0]
            data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
            data.maak_rk_teams(18, ver_nr, zet_klasse=True)
        # for

        data.maak_uitslag_rk_indiv(18)
        data.maak_bk_deelnemers(18)
        data.maak_bk_teams(18)

        # zet de competities in fase P
        zet_competitie_fase_bk_wedstrijden(data.comp18)

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_lijst_bk_teams % 999999)
        self.assert403(resp)

        resp = self.client.post(self.url_wijzig_status_bk_team)
        self.assert403(resp)

    def test_lijst(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)

        resp = self.client.get(self.url_lijst_bk_teams % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        # niet de beheerder
        resp = self.client.get(self.url_lijst_bk_teams % self.testdata.deelkamp25_bk.pk)
        self.assert403(resp, 'Niet de beheerder')

        # mag niet meer wijzigen (fase P)
        resp = self.client.get(self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/bko-bk-teams.dtl', 'design/site_layout.dtl'))

        # verkeerde fase (niet BK)
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        resp = self.client.get(self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        # pas een paar team statussen aan
        teams = list(KampioenschapTeam.objects.filter(kampioenschap=self.testdata.deelkamp18_bk))
        teams[0].deelname = DEELNAME_NEE
        teams[0].save(update_fields=['deelname'])

        teams[1].deelname = DEELNAME_JA
        teams[1].save(update_fields=['deelname'])

        teams[2].is_reserve = True
        teams[2].save(update_fields=['is_reserve'])

        # mag nog wel wijzigen
        zet_competitie_fase_bk_prep(self.testdata.comp18)
        resp = self.client.get(self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/bko-bk-teams.dtl', 'design/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)

    def test_wijzig(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)

        team = KampioenschapTeam.objects.filter(kampioenschap=self.testdata.deelkamp18_bk).first()
        team.deelname = DEELNAME_ONBEKEND
        team.is_reserve = True
        team.save(update_fields=['deelname', 'is_reserve'])

        resp = self.client.post(self.url_wijzig_status_bk_team)
        self.assert404(resp, 'Kan team niet vinden')

        # verkeerde fase
        resp = self.client.post(self.url_wijzig_status_bk_team, data={'team_pk': team.pk})
        self.assert404(resp, 'Mag niet meer wijzigen')

        # mag wel wijzigen
        zet_competitie_fase_bk_prep(self.testdata.comp18)

        # geen wijziging
        resp = self.client.post(self.url_wijzig_status_bk_team, data={'team_pk': team.pk})
        self.assert_is_redirect(resp, self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)
        team = KampioenschapTeam.objects.get(pk=team.pk)
        self.assertEqual(team.deelname, DEELNAME_ONBEKEND)
        self.assertTrue(team.is_reserve)

        # zet NEE
        resp = self.client.post(self.url_wijzig_status_bk_team, data={'team_pk': team.pk, 'status': 'afmelden'})
        self.assert_is_redirect(resp, self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)
        team = KampioenschapTeam.objects.get(pk=team.pk)
        self.assertEqual(team.deelname, DEELNAME_NEE)
        self.assertTrue(team.is_reserve)

        # zet JA
        resp = self.client.post(self.url_wijzig_status_bk_team, data={'team_pk': team.pk, 'status': 'toch_ja'})
        self.assert_is_redirect(resp, self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)
        team = KampioenschapTeam.objects.get(pk=team.pk)
        self.assertEqual(team.deelname, DEELNAME_JA)
        self.assertTrue(team.is_reserve)

        # reserve oproepen
        resp = self.client.post(self.url_wijzig_status_bk_team, data={'team_pk': team.pk, 'status': 'maak_deelnemer'})
        self.assert_is_redirect(resp, self.url_lijst_bk_teams % self.testdata.deelkamp18_bk.pk)
        team = KampioenschapTeam.objects.get(pk=team.pk)
        self.assertFalse(team.is_reserve)

        # verkeerde beheerder
        team.kampioenschap = self.testdata.deelkamp25_bk
        team.save(update_fields=['kampioenschap'])
        zet_competitie_fase_bk_prep(self.testdata.comp25)

        resp = self.client.post(self.url_wijzig_status_bk_team, data={'team_pk': team.pk})
        self.assert403(resp, 'Niet de beheerder')


# end of file
