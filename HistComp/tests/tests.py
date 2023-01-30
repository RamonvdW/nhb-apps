# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from HistComp.models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam
from HistComp.views import RESULTS_PER_PAGE
from TestHelpers.e2ehelpers import E2EHelpers
import io


class TestHistComp(E2EHelpers, TestCase):
    """ unittests voor de HistComp applicatie """

    url_hist_top = '/bondscompetities/hist/'
    url_hist_indiv = '/bondscompetities/hist/indiv/%s/'  # indiv_pk

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        obj = HistCompetitie()
        obj.seizoen = '2018/2019'
        obj.comp_type = '18'
        obj.boog_str = 'Compound'
        obj.is_team = False
        obj.save()

        obj.pk = None
        obj.boog_str = 'Special Type'
        obj.save()

        obj.pk = None
        obj.boog_str = 'Recurve'
        obj.save()
        self.indiv_histcomp_pk = obj.pk

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.sporter_lid_nr = 123456
        rec.sporter_naam = 'Schuttie van de Test'
        rec.vereniging_nr = 1234
        rec.vereniging_naam = 'Test Club'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.laagste_score_nr = 1
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()
        self.indiv_rec_pk = rec.pk

        HistCompetitieTeam(
            histcompetitie=obj,
            subklasse="test",
            rank=1,
            vereniging_nr=1234,
            vereniging_naam="Test Club",
            team_nr=1,
            totaal_ronde1=100,
            totaal_ronde2=200,
            totaal_ronde3=300,
            totaal_ronde4=400,
            totaal_ronde5=500,
            totaal_ronde6=600,
            totaal_ronde7=700,
            totaal=800,
            gemiddelde=543.2
        ).save()

        obj = HistCompetitie()
        obj.seizoen = '2017/2018'
        obj.comp_type = '18'
        obj.boog_str = 'Too old'
        obj.is_team = False
        obj.save()

    def _add_many_records(self, pages):
        # paginator laat 100 entries per pagina zien, dus voeg er 100 toe
        rec = HistCompetitieIndividueel.objects.get(pk=self.indiv_rec_pk)
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
        obj = HistCompetitie.objects.all()[0]
        obj.clean_fields()                  # run field validators
        obj.clean()                         # run model validator
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = HistCompetitieIndividueel.objects.all()[0]
        obj.clean_fields()                  # run field validators
        obj.clean()                         # run model validator
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

        obj = HistCompetitieTeam.objects.all()[0]
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_view_allejaren(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_hist_top)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('hist/histcomp_top.dtl', 'plein/site_layout.dtl'))
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
        HistCompetitie.objects.all().delete()
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
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
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
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
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
        rec = HistCompetitieIndividueel.objects.get(pk=self.indiv_rec_pk)
        rec.sporter_naam = "Dhr Blazoengatenmaker"
        rec.save()
        url = self.url_hist_indiv % self.indiv_histcomp_pk

        # filter on a string
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': 'Blazoengatenmaker'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Blazoengatenmaker')
        # FUTURE: check correct records were returned

        # filter on a ver_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.vereniging_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # filter on a lid_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.sporter_lid_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_view_indiv_many_filter(self):
        self._add_many_records(2)  # 20*100 = +200 records --> paginering actief

        rec = HistCompetitieIndividueel.objects.get(pk=self.indiv_rec_pk)
        url = self.url_hist_indiv % self.indiv_histcomp_pk

        # filter on a string
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.sporter_naam})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "page=2")         # paginator actief
        self.assertContains(resp, "Test Club")

        # filter on a number
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': rec.vereniging_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "Test Club")

        # filter on an unknown number
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'filter': 9999})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "Test Club")

# end of file
