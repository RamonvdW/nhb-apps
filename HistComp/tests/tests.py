# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT, HIST_TEAM_TYPEN_DEFAULT, HISTCOMP_RK, HISTCOMP_BK
from HistComp.models import (HistCompSeizoen,
                             HistCompRegioIndiv, HistKampIndivRK, HistKampIndivBK,
                             HistCompRegioTeam, HistKampTeam)
from HistComp.operations import get_hist_url
from TestHelpers.e2ehelpers import E2EHelpers


class TestHistComp(E2EHelpers, TestCase):
    """ unittests voor de HistComp applicatie """

    url_top = '/bondscompetities/hist/'
    url_seizoen = url_top + '%s/%s-kies/'                            # seizoen, histcomp_type

    url_regio_indiv = url_top + '%s/%s-individueel/%s/regio/'        # seizoen, histcomp_type, boog_type
    url_regio_teams = url_top + '%s/%s-teams/%s/regio/'              # seizoen, histcomp_type, team_type

    url_regio_indiv_nr = url_top + '%s/%s-individueel/%s/regio-%s/'  # seizoen, histcomp_type, boog_type, regio_nr
    url_regio_teams_nr = url_top + '%s/%s-teams/%s/regio-%s/'        # seizoen, histcomp_type, team_type, regio_nr

    # rk
    url_rk_indiv = url_top + '%s/%s-individueel/%s/rk/'              # seizoen, histcomp_type, boog_type
    url_rk_teams = url_top + '%s/%s-teams/%s/rk/'                    # seizoen, histcomp_type, team_type

    url_rk_indiv_nr = url_top + '%s/%s-individueel/%s/rk-rayon%s/'   # seizoen, histcomp_type, boog_type, rayon_nr
    url_rk_teams_nr = url_top + '%s/%s-teams/%s/rk-rayon%s/'         # seizoen, histcomp_type, team_type, rayon_nr

    # bk
    url_bk_indiv = url_top + '%s/%s-individueel/%s/bk/'              # seizoen, histcomp_type, boog_type
    url_bk_teams = url_top + '%s/%s-teams/%s/bk/'                    # seizoen, histcomp_type, team_type

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

        rec = HistKampIndivRK(
                    seizoen=self.hist_seizoen,
                    indiv_klasse='Recurve klasse 1',
                    sporter_lid_nr=100001,
                    sporter_naam='Archie van de Bond',
                    boogtype='R',
                    vereniging_nr=1001,
                    vereniging_naam='De bond',
                    vereniging_plaats='Arnhem',
                    rayon_nr=1,
                    rank_rk=1,
                    rk_score_1=100,
                    rk_score_2=101,
                    rk_score_totaal=201,
                    rk_counts='30x10 29x9',
                    teams_rk_score_1=200,
                    teams_rk_score_2=201)
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
        team.team_score_counts = '##COUNTS##'
        team.save()

        team.pk = None
        team.vereniging_plaats = ''
        team.save()

        # BK
        rec = HistKampIndivBK(
                    seizoen=self.hist_seizoen,
                    bk_indiv_klasse='Recurve klasse 1',
                    sporter_lid_nr=100001,
                    sporter_naam='Archie van de Bond',
                    boogtype='R',
                    vereniging_nr=1001,
                    vereniging_naam='De bond',
                    vereniging_plaats='Arnhem',
                    rank_bk=1,
                    bk_score_1=102,
                    bk_score_2=103,
                    bk_score_totaal=205,
                    bk_counts='29x10 30x8')
        rec.save()
        self.hist_kamp_indiv_bk = rec

        rec = HistKampIndivBK(
                    seizoen=self.hist_seizoen,
                    bk_indiv_klasse='Recurve klasse 2',     # anders dan vorige sporter
                    sporter_lid_nr=100099,
                    sporter_naam='Archy van de Bond',
                    boogtype='R',
                    vereniging_nr=1001,
                    vereniging_naam='De bond',
                    vereniging_plaats='',       # corner case
                    rank_bk=2,
                    bk_score_1=102,
                    bk_score_2=102,
                    bk_score_totaal=204,
                    bk_counts='')
        rec.save()

        rec = HistKampIndivBK(
                    seizoen=self.hist_seizoen,
                    bk_indiv_klasse='Recurve klasse 2',     # zelfde als vorige sporter
                    sporter_lid_nr=100098,
                    sporter_naam='Argy van de Bond',
                    boogtype='R',
                    vereniging_nr=1001,
                    vereniging_naam='De bond',
                    vereniging_plaats='Arnhem',
                    rank_bk=3,
                    bk_score_1=102,
                    bk_score_2=100,
                    bk_score_totaal=202,
                    bk_counts='')
        rec.save()
        HistCompSeizoen(
                seizoen='2017/2018',
                comp_type=HISTCOMP_TYPE_18,
                indiv_bogen=",".join(HIST_BOGEN_DEFAULT)).save()

    def test_top(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'design/site_layout.dtl'))

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
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'design/site_layout.dtl'))

        # gebruik filters
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen % (self.seizoen4url, '18m'))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'design/site_layout.dtl'))

        # bad filters
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen % ('x', 'y'))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'design/site_layout.dtl'))

        # gebruik de model helpers
        self.assertTrue(str(self.hist_seizoen) != '')
        self.hist_seizoen.comp_type = 'x'
        self.assertTrue(str(self.hist_seizoen) != '')

        self.assertTrue(str(self.hist_regio_indiv) != '')
        self.assertEqual(self.hist_regio_indiv.tel_aantal_scores(), 7)

        self.assertTrue(str(self.hist_regio_team) != '')

        self.assertTrue(str(self.hist_kamp_indiv) != '')

        self.assertTrue(str(self.hist_kamp_team_rk) != '')

        self.assertTrue(str(self.hist_kamp_indiv_bk) != '')

        # niet openbaar
        self.hist_seizoen.is_openbaar = False
        self.hist_seizoen.save(update_fields=['is_openbaar'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen % (self.seizoen4url, '18m'))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'design/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_top)

    def test_regio_indiv(self):
        url = self.url_regio_indiv % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_indiv_nr % (self.seizoen4url, '18m', 'recurve', 102)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_indiv % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_regio_indiv % (self.seizoen4url, '18m', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'design/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.indiv_bogen = ''
        self.hist_seizoen.save(update_fields=['indiv_bogen'])
        url = self.url_regio_indiv % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-indiv.dtl', 'design/site_layout.dtl'))

    def test_regio_teams(self):
        url = self.url_regio_teams % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_teams_nr % (self.seizoen4url, '18m', 'recurve', 102)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_teams % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_regio_teams % (self.seizoen4url, '18m', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'design/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.team_typen = ''
        self.hist_seizoen.save(update_fields=['team_typen'])
        url = self.url_regio_teams % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-regio-teams.dtl', 'design/site_layout.dtl'))

    def test_rk_indiv(self):
        url = self.url_rk_indiv % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'design/site_layout.dtl'))

        # geen uitslag
        url = self.url_rk_indiv_nr % (self.seizoen4url, '18m', 'compound', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_rk_indiv % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_rk_indiv % (self.seizoen4url, '18m', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'design/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.indiv_bogen = ''
        self.hist_seizoen.save(update_fields=['indiv_bogen'])
        url = self.url_rk_indiv % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-indiv.dtl', 'design/site_layout.dtl'))

    def test_rk_teams(self):
        # geen uitslag
        url = self.url_rk_teams % (self.seizoen4url, '18m', 'compound')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_rk_teams_nr % (self.seizoen4url, '18m', 'recurve', 1)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_rk_teams % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_rk_teams % (self.seizoen4url, '18m', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'design/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.team_typen = ''
        self.hist_seizoen.save(update_fields=['team_typen'])
        url = self.url_rk_teams % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-rk-teams.dtl', 'design/site_layout.dtl'))

    def test_bk_indiv(self):
        url = self.url_bk_indiv % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        # geen uitslag
        url = self.url_bk_indiv % (self.seizoen4url, '18m', 'compound')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        url = self.url_bk_indiv % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_bk_indiv % (self.seizoen4url, '18m', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.indiv_bogen = ''
        self.hist_seizoen.save(update_fields=['indiv_bogen'])
        url = self.url_bk_indiv % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-indiv.dtl', 'design/site_layout.dtl'))

    def test_bk_teams(self):
        # lege uitslag
        url = self.url_bk_teams % (self.seizoen4url, '18m', 'compound')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))

        url = self.url_bk_teams % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, '##COUNTS##')      # 25m1p telling 10-en en 9-ens

        url = self.url_bk_teams % ('x', 'x', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # fallback to default
        url = self.url_bk_teams % (self.seizoen4url, '18m', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))

        # empty filter exception
        self.hist_seizoen.team_typen = ''
        self.hist_seizoen.save(update_fields=['team_typen'])
        url = self.url_bk_teams % (self.seizoen4url, '18m', 'recurve')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-bk-teams.dtl', 'design/site_layout.dtl'))

    def test_geen_data(self):
        HistCompSeizoen.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'design/site_layout.dtl'))

        url = self.url_regio_teams % (self.seizoen4url, '18m', 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_regio_indiv % (self.seizoen4url, '18m', 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_rk_indiv % (self.seizoen4url, '18m', 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_rk_teams % (self.seizoen4url, '18m', 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_bk_indiv % (self.seizoen4url, '18m', 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

        url = self.url_bk_teams % (self.seizoen4url, '18m', 'recurve')
        self.assert404(self.client.get(url), 'Geen data')

    def test_get_hist_url(self):
        # good weather:
        url = get_hist_url('indoor-' + self.seizoen4url, 'indiv', 'regio', 'r')
        self.assertEqual(url, '/bondscompetities/hist/2018-2019/indoor-individueel/recurve/regio/')

        url = get_hist_url('indoor-' + self.seizoen4url, 'indiv', 'rk', 'r')
        self.assertEqual(url, '/bondscompetities/hist/2018-2019/indoor-individueel/recurve/rk/')

        url = get_hist_url('indoor-' + self.seizoen4url, 'indiv', 'bk', 'lb')
        self.assertEqual(url, '/bondscompetities/hist/2018-2019/indoor-individueel/longbow/bk/')

        url = get_hist_url('25m1pijl-' + self.seizoen4url, 'teams', 'regio', 'c')
        self.assertEqual(url, '/bondscompetities/hist/2018-2019/25m1pijl-teams/compound/regio/')

        url = get_hist_url('indoor-' + self.seizoen4url, 'teams', 'rk', 'r')
        self.assertEqual(url, '/bondscompetities/hist/2018-2019/indoor-teams/recurve/rk/')

        url = get_hist_url('indoor-' + self.seizoen4url, 'teams', 'bk', 'lb')
        self.assertEqual(url, '/bondscompetities/hist/2018-2019/indoor-teams/longbow/bk/')

        url = get_hist_url('BAD', 'teams', 'bk', 'lb')
        self.assertIsNone(url)

        url = get_hist_url('indoor-' + self.seizoen4url, 'BAD', 'rk', 'r')
        self.assertIsNone(url)

        url = get_hist_url('indoor-' + self.seizoen4url, 'teams', 'BAD', 'r')
        self.assertIsNone(url)

        url = get_hist_url('indoor-' + self.seizoen4url, 'indiv', 'bk', 'BAD')
        self.assertIsNone(url)

        url = get_hist_url('indoor-' + self.seizoen4url, 'teams', 'bk', 'BAD')
        self.assertIsNone(url)



# end of file
