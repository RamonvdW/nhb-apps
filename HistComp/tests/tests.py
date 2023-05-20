# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT, HIST_TEAM_TYPEN_DEFAULT, HISTCOMP_RK, HISTCOMP_BK
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv, HistCompRegioTeam, HistKampIndiv, HistKampTeam
from TestHelpers.e2ehelpers import E2EHelpers


class TestHistComp(E2EHelpers, TestCase):
    """ unittests voor de HistComp applicatie """

    url_top = '/bondscompetities/hist/'
    url_seizoen = '/bondscompetities/hist/%s/%s/'      # seizoen, histcomp_type

    url_regio_indiv = '/bondscompetities/hist/%s/%s-individueel/%s/regio/'  # seizoen, histcomp_type, boog_type
    url_regio_teams = '/bondscompetities/hist/%s/%s-teams/%s/regio/'        # seizoen, histcomp_type, team_type

    url_regio_indiv_nr = '/bondscompetities/hist/%s/%s-individueel/%s/regio-%s/'  # seizoen, histcomp_type, boog_type, regio_nr
    url_regio_teams_nr = '/bondscompetities/hist/%s/%s-teams/%s/regio-%s/'        # seizoen, histcomp_type, team_type, regio_nr

    # rk
    url_rk_indiv = '/bondscompetities/hist/%s/%s-individueel/%s/rk/'  # seizoen, histcomp_type, boog_type
    url_rk_teams = '/bondscompetities/hist/%s/%s-teams/%s/rk/'        # seizoen, histcomp_type, team_type

    url_rk_indiv_nr = '/bondscompetities/hist/%s/%s-individueel/%s/rk-rayon%s/'   # seizoen, histcomp_type, boog_type, rayon_nr
    url_rk_teams_nr = '/bondscompetities/hist/%s/%s-teams/%s/rk-rayon%s/'         # seizoen, histcomp_type, team_type, rayon_nr

    # bk
    url_bk_indiv = '/bondscompetities/hist/%s/%s-individueel/%s/bk/'  # seizoen, histcomp_type, boog_type
    url_bk_teams = '/bondscompetities/hist/%s/%s-teams/%s/bk/'        # seizoen, histcomp_type, team_type

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        hist_seizoen = HistCompSeizoen(
                            seizoen='2018/2019',
                            comp_type=HISTCOMP_TYPE_18,
                            indiv_bogen=",".join(HIST_BOGEN_DEFAULT),
                            team_typen=",".join(HIST_TEAM_TYPEN_DEFAULT))
        hist_seizoen.save()
        self.hist_seizoen = hist_seizoen
        self.seizoen4url = '2018-2019'

        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    indiv_klasse='Recurve klasse 1',
                    sporter_lid_nr=123456,
                    sporter_naam='Schuttie van de Test',
                    boogtype='R',
                    vereniging_nr=1234,
                    vereniging_naam='Test Club',
                    vereniging_plaats="Pijlstad",
                    regio_nr=102,
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    laagste_score_nr=1,
                    totaal=80,
                    gemiddelde=5.321)
        rec.save()
        self.hist_regio_indiv = rec
        self.indiv_rec_pk = rec.pk

        rec.pk = None
        rec.sporter_lid_nr += 1
        rec.save()

        rec.pk = None
        rec.sporter_lid_nr += 1
        rec.sporter_naam += 'er'
        rec.vereniging_plaats = ''
        rec.indiv_klasse = 'Recurve klasse 2'
        rec.save()

        team = HistCompRegioTeam(
                    seizoen=hist_seizoen,
                    team_klasse="Recurve klasse ERE",
                    team_type='R',
                    rank=1,
                    vereniging_nr=1234,
                    vereniging_naam="Test Club",
                    vereniging_plaats="Pijlstad",
                    regio_nr=102,
                    team_nr=1,
                    ronde_1_score=100,
                    ronde_2_score=200,
                    ronde_3_score=300,
                    ronde_4_score=400,
                    ronde_5_score=500,
                    ronde_6_score=600,
                    ronde_7_score=700,
                    totaal_score=800,
                    ronde_1_punten=10,
                    ronde_2_punten=20,
                    ronde_3_punten=30,
                    ronde_4_punten=40,
                    ronde_5_punten=50,
                    ronde_6_punten=60,
                    ronde_7_punten=70,
                    totaal_punten=80)
        team.save()
        self.hist_regio_team = team

        team.pk = None
        team.rank += 1
        team.save()

        team.pk = None
        team.team_klasse = 'Recurve klasse A'
        team.team_nr += 1
        team.vereniging_plaats = ''
        team.save()

        rec = HistKampIndiv(
                    seizoen=self.hist_seizoen,
                    indiv_klasse='Recurve klasse 1',
                    sporter_lid_nr=100001,
                    sporter_naam='Achie van de Bond',
                    boogtype='R',
                    vereniging_nr=1001,
                    vereniging_naam='De bond',
                    vereniging_plaats='Arnhem',
                    rayon_nr=1,
                    rank_rk=1,
                    rank_bk=1,
                    rk_score_1=100,
                    rk_score_2=101,
                    rk_score_totaal=201,
                    rk_counts='30x10 29x9',
                    bk_score_1=102,
                    bk_score_2=103,
                    bk_score_totaal=205,
                    bk_counts='29x10 30x8',
                    teams_rk_score_1=200,
                    teams_rk_score_2=201,
                    teams_bk_score_1=202,
                    teams_bk_score_2=203)
        rec.save()
        self.hist_kamp_indiv = rec

        rec.pk = None
        rec.sporter_lid_nr += 1
        rec.sporter_naam += 'er'
        rec.save()

        rec.pk = None
        rec.indiv_klasse = 'Recurve klasse 2'
        rec.sporter_lid_nr += 1
        rec.vereniging_plaats = ''
        rec.rk_score_is_blanco = True
        rec.save()

        team = HistKampTeam(
                    seizoen=self.hist_seizoen,
                    rk_of_bk=HISTCOMP_RK,
                    rayon_nr=1,
                    teams_klasse='Recurve klasse ERE',
                    team_type='R',
                    vereniging_nr=self.hist_kamp_indiv.vereniging_nr,
                    vereniging_naam=self.hist_kamp_indiv.vereniging_naam,
                    vereniging_plaats='Pijlstad',
                    team_nr=1,
                    team_score=303,
                    rank=1,
                    lid_1=rec,
                    lid_2=rec,
                    lid_3=rec,
                    lid_4=None,
                    score_lid_1=100,
                    score_lid_2=101,
                    score_lid_3=102,
                    score_lid_4=0)
        team.save()
        self.hist_kamp_team_rk = team

        team.pk = None
        team.rank += 1
        team.save()

        team.pk = None
        team.rank = 1
        team.vereniging_plaats = ''
        team.teams_klasse = 'Recurve klasse A'
        team.save()

        team = HistKampTeam(
                    seizoen=self.hist_seizoen,
                    rk_of_bk=HISTCOMP_BK,
                    rayon_nr=1,
                    teams_klasse='Recurve klasse ERE',
                    team_type='R',
                    vereniging_nr=self.hist_kamp_indiv.vereniging_nr,
                    vereniging_naam=self.hist_kamp_indiv.vereniging_naam,
                    vereniging_plaats='Pijlstad',
                    team_nr=1,
                    team_score=333,
                    rank=1,
                    lid_1=rec,
                    lid_2=rec,
                    lid_3=rec,
                    lid_4=None,
                    score_lid_1=110,
                    score_lid_2=111,
                    score_lid_3=112,
                    score_lid_4=0)
        team.save()
        self.hist_kamp_team_bk = team

        team.pk = None
        team.teams_klasse = 'Recurve klasse A'
        team.save()

        team.pk = None
        team.vereniging_plaats = ''
        team.save()

        HistCompSeizoen(
                seizoen='2017/2018',
                comp_type=HISTCOMP_TYPE_18,
                indiv_bogen=",".join(HIST_BOGEN_DEFAULT)).save()

    def test_top(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'plein/site_layout.dtl'))

        # alle kaartjes activeren
        self.hist_seizoen.heeft_uitslag_regio_teams = True
        self.hist_seizoen.heeft_uitslag_rk_indiv = True
        self.hist_seizoen.heeft_uitslag_rk_teams = True
        self.hist_seizoen.heeft_uitslag_bk_indiv = True
        self.hist_seizoen.heeft_uitslag_bk_teams = True
        self.hist_seizoen.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'plein/site_layout.dtl'))

        # gebruik filters
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen % (self.seizoen4url, HISTCOMP_TYPE_18))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'plein/site_layout.dtl'))

        # bad filters
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen % ('x', 'y'))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'plein/site_layout.dtl'))

        # gebruik de model helpers
        self.assertTrue(str(self.hist_seizoen) != '')
        self.hist_seizoen.comp_type = 'x'
        self.assertTrue(str(self.hist_seizoen) != '')

        self.assertTrue(str(self.hist_regio_indiv) != '')
        self.assertEqual(self.hist_regio_indiv.tel_aantal_scores(), 7)

        self.assertTrue(str(self.hist_regio_team) != '')

        self.assertTrue(str(self.hist_kamp_indiv) != '')

        self.assertTrue(str(self.hist_kamp_team_rk) != '')

        # niet openbaar
        self.hist_seizoen.is_openbaar = False
        self.hist_seizoen.save(update_fields=['is_openbaar'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen % (self.seizoen4url, HISTCOMP_TYPE_18))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_top)

    def test_regio_indiv(self):
        url = self.url_regio_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_indiv_nr % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve', 102)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_indiv % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_regio_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.indiv_bogen = ''
        self.hist_seizoen.save(update_fields=['indiv_bogen'])
        url = self.url_regio_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

    def test_regio_teams(self):
        url = self.url_regio_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_teams_nr % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve', 102)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_teams % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_regio_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.team_typen = ''
        self.hist_seizoen.save(update_fields=['team_typen'])
        url = self.url_regio_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

    def test_rk_indiv(self):
        url = self.url_rk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        # geen uitslag
        url = self.url_rk_indiv_nr % (self.seizoen4url, HISTCOMP_TYPE_18, 'compound', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_rk_indiv % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_rk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.indiv_bogen = ''
        self.hist_seizoen.save(update_fields=['indiv_bogen'])
        url = self.url_rk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'plein/site_layout.dtl'))

    def test_rk_teams(self):
        # geen uitslag
        url = self.url_rk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'compound')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_rk_teams_nr % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_rk_teams % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_rk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.team_typen = ''
        self.hist_seizoen.save(update_fields=['team_typen'])
        url = self.url_rk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'plein/site_layout.dtl'))

    def test_bk_indiv(self):
        url = self.url_bk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'plein/site_layout.dtl'))

        # geen uitslag
        url = self.url_bk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'compound')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_bk_indiv % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_bk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'plein/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.indiv_bogen = ''
        self.hist_seizoen.save(update_fields=['indiv_bogen'])
        url = self.url_bk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'plein/site_layout.dtl'))

    def test_bk_teams(self):
        # lege uitslag
        url = self.url_bk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'compound')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_bk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'plein/site_layout.dtl'))

        url = self.url_bk_teams % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_bk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'plein/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.team_typen = ''
        self.hist_seizoen.save(update_fields=['team_typen'])
        url = self.url_bk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'plein/site_layout.dtl'))

    def test_geen_data(self):
        HistCompSeizoen.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'plein/site_layout.dtl'))

        url = self.url_regio_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_regio_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_rk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_rk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_bk_indiv % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_bk_teams % (self.seizoen4url, HISTCOMP_TYPE_18, 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

# end of file
