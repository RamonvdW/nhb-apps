# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT, HIST_TEAM_TYPEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv, HistCompRegioTeam
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

        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    indiv_klasse='Recurve ERE',
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
        self.indiv_rec_pk = rec.pk

        HistCompRegioTeam(
                seizoen=hist_seizoen,
                team_klasse="test",
                rank=1,
                vereniging_nr=1234,
                vereniging_naam="Test Club",
                vereniging_plaats="Pijlstad",
                regio_nr="102",
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
                totaal_punten=80).save()

        HistCompSeizoen(seizoen='2017/2018', comp_type=HISTCOMP_TYPE_18,
                        indiv_bogen=",".join(HIST_BOGEN_DEFAULT)).save()

    def _add_many_records(self, pages):
        # paginator laat 100 entries per pagina zien, dus voeg er 100 toe
        rec = HistCompRegioIndiv.objects.get(pk=self.indiv_rec_pk)
        while pages > 0:
            pages -= 1
            for lp in range(RESULTS_PER_PAGE):
                rec.pk = None
                rec.rank += 1
                rec.totaal += 10
                rec.save()
            # for
        # while

    def test_histcompetitie(self):
        self.hist_seizoen.clean_fields()    # run field validators
        self.hist_seizoen.clean()           # run model validator
        self.assertTrue(str(self.hist_seizoen) != '')

        obj = HistCompRegioIndiv.objects.all()[0]
        obj.clean_fields()                  # run field validators
        obj.clean()                         # run model validator
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = HistCompRegioTeam.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_view_allejaren(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_hist_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/uitslagen-top.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "2018/2019")
        self.assertNotContains(resp, "2017/2018")
        self.assertContains(resp, 'Compound')
        self.assertContains(resp, 'Recurve')
        self.e2e_assert_other_http_commands_not_supported(self.url_hist_top)

        # controleer de volgorde waarin de klassen getoond wordt
        resp_str = str(resp.content)
        pos1 = resp_str.find('Recurve')
        pos2 = resp_str.find('Compound')
        self.assertTrue(0 < pos1 < pos2)

    def test_view_allejaren_leeg(self):
        # verwijder alle records en controleer dat het goed gaat
        HistCompSeizoen.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_hist_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertContains(resp, "Er is op dit moment geen uitslag beschikbaar")

    def test_view_indiv_non_existing(self):
        url = self.url_hist_indiv % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_view_indiv_few(self):
        url = self.url_hist_indiv % self.indiv_histcomp_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "page=1")     # pagination not active
        self.assertNotContains(resp, "page=1")     # pagination not active
        self.assertContains(resp, "2018/2019")
        self.assertContains(resp, "Recurve")
        self.e2e_assert_other_http_commands_not_supported(url)

    def test_view_indiv_many(self):
        self._add_many_records(10)  # 10*100 = +1000 records
        url = self.url_hist_indiv % self.indiv_histcomp_pk

        with self.assert_max_queries(20):
            resp = self.client.get(url, {'page': 6})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "page=5")

        # haal de eerste aan de laatste pagina op, voor coverage
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        with self.assert_max_queries(20):
            resp = self.client.get(url, {'page': 11})
        self.assertEqual(resp.status_code, 200)

    def test_view_indiv_all(self):
        # haal alle regels op, zonder paginering
        self._add_many_records(2)  # 20*100 = +200 records --> paginering actief
        url = self.url_hist_indiv % self.indiv_histcomp_pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertContains(resp, "page=2")         # paginator actief

        with self.assert_max_queries(20):
            resp = self.client.get(url, {'all': 1})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "page=2")      # paginator inactief

        # corner-case: invalid form data
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'all': 'not an integer'})
        self.assertEqual(resp.status_code, 200)

    def test_view_indiv_few_filter(self):
        rec = HistCompRegioIndiv.objects.get(pk=self.indiv_rec_pk)
        rec.sporter_naam = "Dhr Blazoengatenmaker"
        rec.save()
        url = self.url_hist_indiv % self.indiv_histcomp_pk

        # filter on a string
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': 'Blazoengatenmaker'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Blazoengatenmaker')
        # FUTURE: check correct records were returned

        # filter on a ver_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.vereniging_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # filter on a lid_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.sporter_lid_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_view_indiv_many_filter(self):
        self._add_many_records(2)  # 20*100 = +200 records --> paginering actief

        rec = HistCompRegioIndiv.objects.get(pk=self.indiv_rec_pk)
        url = self.url_hist_indiv % self.indiv_histcomp_pk

        # filter on a string
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.sporter_naam})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "page=2")         # paginator actief
        self.assertContains(resp, "Test Club")

        # filter on a number
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.vereniging_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "Test Club")

        # filter on an unknown number
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': 9999})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('histcomp/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "Test Club")

# end of file
