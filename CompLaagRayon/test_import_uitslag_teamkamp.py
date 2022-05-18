# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.test.client import Client
from Competitie.test_fase import zet_competitie_fase
from Competitie.models import KampioenschapSchutterBoog, KampioenschapTeam, DEELNAME_NEE
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import io


class TestCompLaagRayonImportUitslagTeamKampioenschap(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, import van de RK/BK teams uitslag """

    url_klassengrenzen_teams_vaststellen = '/bondscompetities/rk/%s/rk-bk-teams-klassengrenzen/vaststellen/'  # comp_pk

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        for regio_nr in range(cls.regio_nr, cls.regio_nr+4):        # 4 regio's van dit rayon
            ver_nr = data.regio_ver_nrs[regio_nr][0]        # 1 verenigingen per regio
            data.maak_rk_deelnemers(25, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])

            # test file is voor een recurve-klasse
            per_team = 3 if ver_nr == 1121 else 4
            data.maak_inschrijvingen_rk_teamcompetitie(25, ver_nr, per_team, limit_teamtypen=['R2'])
        # for

    def setUp(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        self.e2e_check_rol('BKO')

        # zet de competitie in fase J (=vereiste vaststellen klassengrenzen)
        zet_competitie_fase(self.testdata.comp25, 'J')

        # stel de klassegrenzen vast
        resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp25.pk)
        # self.e2e_dump_resp(resp)
        self.assert_is_redirect_not_plein(resp)

        # for team in KampioenschapTeam.objects.prefetch_related('gekoppelde_schutters').all():
        #     print(team, '-->', team.team_klasse)
        #     print('  gekoppelde_schutters: %s' % repr([deelnemer.sporterboog.sporter.lid_nr for deelnemer in
        #                                                team.gekoppelde_schutters.select_related(
        #                                                    'sporterboog__sporter').all()]))

        # zet de competities in fase L
        zet_competitie_fase(self.testdata.comp18, 'L')
        zet_competitie_fase(self.testdata.comp25, 'L')

    def test_25m(self):
        real_file = 'CompLaagRayon/management/testfiles/test_rk-25mp_teams.xlsm'

        # afstand NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_uitslag_teamkamp', '999', 'bestand', 'blad', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Afstand moet 18 of 25 zijn')

        # file NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_teamkamp', '25', 'bestand', 'blad', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Kan het excel bestand niet openen')

        # blad NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_teamkamp', '25', real_file, 'blad', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Kan blad 'blad' niet vinden" in f1.getvalue())

        # kolommen NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_teamkamp', '25', real_file, 'Deelnemers en Scores', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Vereiste kolommen: ' in f1.getvalue())

        # dry-run
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_teamkamp', '25', real_file, 'Deelnemers en Scores', 'D', 'F', 'E', 'G', 'H', 'I', '--dryrun', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        self.assertTrue('[ERROR] Te hoog gemiddelde 8.991 voor invaller 301957 voor team rk-1091-2-R2 van vereniging 1091' in f1.getvalue())
        self.assertTrue('[ERROR] Lid 302220 is niet van vereniging 1121!' in f1.getvalue())
        self.assertTrue('[ERROR] Lid 123456 is niet gekwalificeerd voor dit kampioenschap!' in f1.getvalue())
        # self.assertTrue('[ERROR] Inconsistente team klasse op regel 45: Recurve klasse A [R2] (26.028) (RK/BK) (eerdere teams: Recurve klasse B [R2] (25.128) (RK/BK))' in f1.getvalue())
        self.assertTrue("[ERROR] Kan team 'Niet bestaand team' van vereniging 1121 op regel 51 niet vinden" in f1.getvalue())

        self.assertTrue('[WARNING] Geen scores voor sporter 301946 op regel 13' in f2.getvalue())

        # echte import
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_teamkamp', '25', real_file, 'Deelnemers en Scores', 'D', 'F', 'E', 'G', 'H', 'I', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        team1 = KampioenschapTeam.objects.filter(team_naam='rk-1111-1-R2')[0]
        team2 = KampioenschapTeam.objects.filter(team_naam='rk-1101-1-R2')[0]
        self.assertEqual(team1.result_teamscore, 1395)
        self.assertEqual(team1.result_rank, 1)              # een van de sporters heeft het hoogste resultaat
        self.assertEqual(team2.result_teamscore, 1395)
        self.assertEqual(team2.result_rank, 2)

    def test_18m(self):
        real_file = 'CompLaagRayon/management/testfiles/test_rk-25mp_teams.xlsm'

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_teamkamp', '18', real_file, 'Deelnemers en Scores', 'A', 'B', 'C', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue('[ERROR] Indoor nog niet ondersteund' in f1.getvalue())


# end of file
