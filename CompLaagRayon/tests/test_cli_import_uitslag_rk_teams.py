# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import KampioenschapTeam
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_rk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonImportUitslagRkTeams(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, import van de RK/BK teams uitslag """

    url_klassengrenzen_teams_vaststellen = '/bondscompetities/beheer/%s/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/'  # comp_pk

    test_file_25m = 'CompLaagRayon/test-files/test_rk-25m1pijl-teams.xlsx'
    test_file1_18m = 'CompLaagRayon/test-files/test_rk-indoor-teams_4.xlsx'
    test_file2_18m = 'CompLaagRayon/test-files/test_rk-indoor-teams_8.xlsx'

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        # ver_nrs: 4091, 4101, 4111, 4121
        for regio_nr in range(cls.regio_nr, cls.regio_nr+4):        # 4 regio's van dit rayon
            ver_nr = data.regio_ver_nrs[regio_nr][0]        # 1 verenigingen per regio
            data.maak_rk_deelnemers(25, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
            data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])

            # test file is voor een recurve-klasse
            per_team = 3 if ver_nr == 4121 else 4
            data.maak_rk_teams(25, ver_nr, per_team, limit_teamtypen=['R2'])
            data.maak_rk_teams(18, ver_nr, per_team, limit_teamtypen=['R2'])
        # for

        # maak nog een paar teams aan in
        regio_nr = cls.regio_nr + 3        # is deelbaar door 4 --> krijgt hogere scores --> ERE klasse
        ver_nr = data.regio_ver_nrs[regio_nr][1]
        data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
        data.maak_rk_teams(18, ver_nr, 4, limit_teamtypen=['R2'])

    def setUp(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        self.e2e_check_rol('BKO')

        # zet de competitie in fase J (=vereiste vaststellen klassengrenzen)
        zet_competitie_fase_rk_prep(self.testdata.comp25)
        zet_competitie_fase_rk_prep(self.testdata.comp18)

        # stel de klassengrenzen vast
        resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp25.pk)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp18.pk)
        self.assert_is_redirect_not_plein(resp)

        # zet de competities in fase L
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp25)

        # for team in self.testdata.comp18_kampioenschapteams:
        #     team = KampioenschapTeam.objects.get(pk=team.pk)
        #     print('Indoor team: %s, klasse: %s' % (team, team.team_klasse))
        #     for lid in team.gekoppelde_leden.all():
        #         print('  lid: %s, gem: %s' % (lid, lid.gemiddelde))
        # # for

    def test_25m(self):
        # file NOK
        f1, f2 = self.run_management_command('import_uitslag_rk_25m1pijl_teams', 'bestand')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())

        # dry-run
        f1, f2 = self.run_management_command('import_uitslag_rk_25m1pijl_teams', self.test_file_25m, '--dryrun')
        # print('\nf1:', f1.getvalue())
        # print('\nf2:', f2.getvalue())
        self.assertTrue(
            '[ERROR] Te hoog gemiddelde 8.916 voor invaller 301834 voor team team-4091-2-R2 van vereniging 4091'
            in f1.getvalue())
        self.assertTrue('[ERROR] Lid 302093 is niet van vereniging 4121!' in f1.getvalue())
        self.assertTrue('[ERROR] Lid 123456 is niet gekwalificeerd voor dit kampioenschap!' in f1.getvalue())
        self.assertTrue("[ERROR] Kan team 'Niet bestaand team' van vereniging 4121 op regel 51 niet vinden"
                        in f1.getvalue())
        self.assertTrue("[ERROR] Te veel invallers voor team 'team-4121-2-R2' met max 2 sporters (vereniging 4121"
                        in f1.getvalue())

        self.assertTrue(
            "[WARNING] Team 'team-4111-2-R2' op regel 45 niet herkend voor klasse Recurve klasse B [R2] (25.128) (RK/BK"
            in f2.getvalue())
        self.assertTrue('[WARNING] Geen scores voor sporter 301826 op regel 13' in f2.getvalue())

        # echte import
        f1, f2 = self.run_management_command('import_uitslag_rk_25m1pijl_teams', self.test_file_25m)
        _ = (f1, f2)
        # print('\nf1:', f1.getvalue())
        # print('\nf2:', f2.getvalue())
        team1 = KampioenschapTeam.objects.get(team_naam='team-4111-1-R2', kampioenschap__competitie__afstand=25)
        team2 = KampioenschapTeam.objects.get(team_naam='team-4101-1-R2', kampioenschap__competitie__afstand=25)
        self.assertEqual(team1.result_rank, 1)              # een van de sporters heeft het hoogste resultaat
        self.assertEqual(team2.result_rank, 2)
        self.assertEqual(team1.result_teamscore, 1395)
        self.assertEqual(team2.result_teamscore, 1395)

    def test_18m(self):
        f1, f2 = self.run_management_command('import_uitslag_rk_indoor_teams', 'bestand')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_rk_indoor_teams',
                                             self.test_file1_18m,
                                             '--dryrun', '--verbose')
        # print('\nf1:', f1.getvalue())
        # print('\nf2:', f2.getvalue())
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue("[INFO] Uitslag wordt van blad 'Finales 4 teams' gehaald" in f2.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_rk_indoor_teams', self.test_file2_18m)
        # print('\nf1:', f1.getvalue())
        # print('\nf2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan team 'team-4122-' van vereniging 4122 op regel 33 niet kiezen uit"
                        in f1.getvalue())
        self.assertTrue("[ERROR] Kan team 'team-4122-' van vereniging 4122 op regel 33 niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 4122, lid 301948 met ag=9.447 niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 123456 is niet gekwalificeerd voor dit kampioenschap!" in f1.getvalue())
        self.assertTrue("[ERROR] Probleem met de scores op regel 16" in f1.getvalue())
        self.assertTrue("[INFO] Uitslag wordt van blad 'Finales 8 teams' gehaald" in f2.getvalue())
        self.assertTrue("[WARNING] Aangepaste team naam: 'team-4122-5-R2' --> 'Aangepast team-4122-5-R2'"
                        in f2.getvalue())
        self.assertTrue("[WARNING] Team 4122 van vereniging team-4122-3-R2 heeft niet meegedaan (geen scores)"
                        in f2.getvalue())

        team1 = KampioenschapTeam.objects.get(team_naam='team-4122-5-R2', kampioenschap__competitie__afstand=18)
        team2 = KampioenschapTeam.objects.get(team_naam='team-4121-7-R2', kampioenschap__competitie__afstand=18)
        self.assertEqual(team1.result_rank, 2)              # een van de sporters heeft het hoogste resultaat
        self.assertEqual(team2.result_rank, 3)
        self.assertEqual(team1.result_teamscore, 1174)
        self.assertEqual(team2.result_teamscore, 909)

# end of file
