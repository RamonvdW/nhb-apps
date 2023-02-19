# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_rk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonImportUitslagTeamKampioenschap(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, import van de RK/BK teams uitslag """

    url_klassengrenzen_teams_vaststellen = '/bondscompetities/beheer/%s/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/'  # comp_pk

    test_file_25m = 'CompLaagRayon/management/testfiles/test_rk-25m1p_teams.xlsm'
    test_file1_18m = 'CompLaagRayon/management/testfiles/test_rk-indoor_teams_4.xlsm'
    test_file2_18m = 'CompLaagRayon/management/testfiles/test_rk-indoor_teams_8.xlsm'

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        # ver_nrs: 4091, 4101, 4111, 4121
        for regio_nr in range(cls.regio_nr, cls.regio_nr+4):        # 4 regio's van dit rayon
            ver_nr = data.regio_ver_nrs[regio_nr][0]        # 1 verenigingen per regio
            data.maak_rk_deelnemers(25, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
            data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])

            # test file is voor een recurve-klasse
            per_team = 3 if ver_nr == 4121 else 4
            data.maak_inschrijvingen_rk_teamcompetitie(25, ver_nr, per_team, limit_teamtypen=['R2'])
            data.maak_inschrijvingen_rk_teamcompetitie(18, ver_nr, per_team, limit_teamtypen=['R2'])
        # for

    def setUp(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        self.e2e_check_rol('BKO')

        # zet de competitie in fase J (=vereiste vaststellen klassengrenzen)
        zet_competitie_fase_rk_prep(self.testdata.comp25)
        zet_competitie_fase_rk_prep(self.testdata.comp18)

        # stel de klassegrenzen vast
        resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp25.pk)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp18.pk)
        self.assert_is_redirect_not_plein(resp)

        # zet de competities in fase L
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp25)

    def test_25m(self):
        # file NOK
        f1, f2 = self.run_management_command('import_uitslag_teamkamp_25m1pijl', 'bestand')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())

        # dry-run
        f1, f2 = self.run_management_command('import_uitslag_teamkamp_25m1pijl', self.test_file_25m, '--dryrun')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        # TODO: repair this testcase
        # self.assertTrue('[ERROR] Te hoog gemiddelde 8.991 voor invaller 301957 voor team rk-4091-2-R2 van vereniging 4091' in f1.getvalue())
        # self.assertTrue('[ERROR] Lid 302220 is niet van vereniging 4121!' in f1.getvalue())
        # self.assertTrue('[ERROR] Lid 123456 is niet gekwalificeerd voor dit kampioenschap!' in f1.getvalue())
        # self.assertTrue('[ERROR] Inconsistente team klasse op regel 45: Recurve klasse A [R2] (26.028) (RK/BK) (eerdere teams: Recurve klasse B [R2] (25.128) (RK/BK))' in f1.getvalue())
        # self.assertTrue("[ERROR] Kan team 'Niet bestaand team' van vereniging 4121 op regel 51 niet vinden" in f1.getvalue())

        # self.assertTrue('[WARNING] Geen scores voor sporter 301946 op regel 13' in f2.getvalue())

        # echte import
        f1, f2 = self.run_management_command('import_uitslag_teamkamp_25m1pijl', self.test_file_25m)
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        # TODO: repair this testcase
        # team1 = KampioenschapTeam.objects.filter(team_naam='rk-4111-1-R2')[0]
        # team2 = KampioenschapTeam.objects.filter(team_naam='rk-4101-1-R2')[0]
        # self.assertEqual(team1.result_teamscore, 1395)
        # self.assertEqual(team1.result_rank, 1)              # een van de sporters heeft het hoogste resultaat
        # self.assertEqual(team2.result_teamscore, 1395)
        # self.assertEqual(team2.result_rank, 2)

    def test_18m(self):
        f1, f2 = self.run_management_command('import_uitslag_teamkamp_indoor', 'bestand')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_teamkamp_indoor', self.test_file1_18m, '--dryrun', '--verbose')
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue("[INFO] Uitslag wordt van blad 'Finales 4 teams' gehaald" in f2.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_teamkamp_indoor', self.test_file2_18m)
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue("[INFO] Uitslag wordt van blad 'Finales 8 teams' gehaald" in f2.getvalue())
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

# end of file
