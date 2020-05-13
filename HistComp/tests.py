# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers
from .models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam
from .views import RESULTS_PER_PAGE


class TestHistComp(E2EHelpers, TestCase):
    """ unittests voor de HistComp applicatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        obj = HistCompetitie()
        obj.seizoen = '2018/2019'
        obj.comp_type = '18'
        obj.klasse = 'Compound'
        obj.is_team = False
        obj.save()

        obj.pk = None
        obj.klasse = 'Special Type'
        obj.save()

        obj.pk = None
        obj.klasse = 'Recurve'
        obj.save()
        self.indiv_histcomp_pk = obj.pk

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = 123456
        rec.schutter_naam = 'Schuttie van de Test'
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

        obj.pk = None
        obj.klasse = 'Teamcurve3'
        obj.is_team = True
        obj.save()

        rec = HistCompetitieTeam()
        rec.histcompetitie = obj
        rec.subklasse = 'TERE'
        rec.rank = 1
        rec.vereniging_nr = 123
        rec.vereniging_naam = 'Groen Veldje'
        rec.team_nr = 1
        rec.totaal_ronde1 = 1000
        rec.totaal_ronde2 = 1100
        rec.totaal_ronde3 = 1200
        rec.totaal_ronde4 = 1300
        rec.totaal_ronde5 = 1400
        rec.totaal_ronde6 = 1500
        rec.totaal_ronde7 = 1600
        rec.totaal = 9876
        rec.gemiddelde = 1234.5
        rec.save()

        obj = HistCompetitie()
        obj.seizoen = '2017/2018'
        obj.comp_type = '18'
        obj.klasse = 'Too old'
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

    def test_histcomp_individueel(self):
        obj = HistCompetitieIndividueel.objects.all()[0]
        obj.clean_fields()                  # run field validators
        obj.clean()                         # run model validator
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_histcomp_team(self):
        obj = HistCompetitieTeam.objects.all()[0]
        obj.clean_fields()                  # run field validators
        obj.clean()                         # run model validator
        self.assertIsNotNone(str(obj))      # use the __str__ method (only used by admin interface)

    def test_view_allejaren(self):
        resp = self.client.get('/hist/')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('hist/histcomp_allejaren.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "2018/2019")
        self.assertNotContains(resp, "2017/2018")
        self.assertContains(resp, 'Compound')
        self.assertContains(resp, 'Special Type')
        self.assertContains(resp, 'Recurve')
        self.e2e_assert_other_http_commands_not_supported('/hist/')

        # controleer de volgorde waarin de klassen getoond wordt
        resp_str = str(resp.content)
        pos1 = resp_str.find('Recurve')
        pos2 = resp_str.find('Compound')
        pos3 = resp_str.find('Special Type')
        self.assertTrue(0 < pos1 < pos2)
        self.assertTrue(0 < pos2 < pos3)

    def test_view_allejaren_leeg(self):
        # verwijder alle records en controleer dat het goed gaat
        HistCompetitie.objects.all().delete()
        resp = self.client.get('/hist/')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertContains(resp, "Er is op dit moment geen uitslag beschikbaar")

    def test_view_indiv_non_existing(self):
        resp = self.client.get('/hist/indiv/999999/')
        self.assertEqual(resp.status_code, 404)

    def test_view_indiv_few(self):
        url = '/hist/indiv/%s/' % self.indiv_histcomp_pk
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
        url = '/hist/indiv/%s/' % self.indiv_histcomp_pk

        resp = self.client.get(url, {'page': 6})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "page=5")

        # haal de eerste aan de laatste pagina op, voor coverage
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url, {'page': 11})
        self.assertEqual(resp.status_code, 200)

    def test_view_indiv_all(self):
        # haal alle regels op, zonder paginering
        self._add_many_records(2)  # 20*100 = +200 records --> paginering actief
        url = '/hist/indiv/%s/' % self.indiv_histcomp_pk

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertContains(resp, "page=2")         # paginator actief

        resp = self.client.get(url, {'all': 1})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "page=2")      # paginator inactief

        # corner-case: invalid form data
        resp = self.client.get(url, {'all': 'not an integer'})
        self.assertEqual(resp.status_code, 200)

    def test_view_indiv_few_filter(self):
        rec = HistCompetitieIndividueel.objects.get(pk=self.indiv_rec_pk)
        rec.schutter_naam = "Dhr Blazoengatenmaker"
        rec.save()
        url = '/hist/indiv/%s/' % self.indiv_histcomp_pk

        # filter on a string
        resp = self.client.get(url, {'filter': 'Blazoengatenmaker'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Blazoengatenmaker')
        # TODO: check correct records was returned

        # filter on a number
        resp = self.client.get(url, {'filter': rec.vereniging_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_view_indiv_many_filter(self):
        self._add_many_records(2)  # 20*100 = +200 records --> paginering actief

        rec = HistCompetitieIndividueel.objects.get(pk=self.indiv_rec_pk)
        url = '/hist/indiv/%s/' % self.indiv_histcomp_pk

        # filter on a string
        resp = self.client.get(url, {'filter': rec.schutter_naam})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "page=2")         # paginator actief
        self.assertContains(resp, "Test Club")

        # filter on a number
        resp = self.client.get(url, {'filter': rec.vereniging_nr})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "Test Club")

        # filter on an unknown number
        resp = self.client.get(url, {'filter': 9999})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "Test Club")

    # def _UIT_test_view_invid_empty(self):
    #     rsp = self.client.get('/hist/2019/18/Missing/indiv/')
    #     self.assertEqual(rsp.status_code, 200)
    #     self.assert_template_used(rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     self.assert_html_ok(rsp)
    #     # TODO: check correct records were returned
    #
    # def _UIT_test_view_team_all(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'all': '1'})
    #     self.assertEqual(rsp.status_code, 200)
    #     self.assert_template_used(rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     self.assert_html_ok(rsp)
    #
    # def _UIT_test_view_team_filter_schutter_nr(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'filter': '123456'})
    #     self.assertEqual(rsp.status_code, 200)
    #     self.assert_template_used(rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     self.assert_html_ok(rsp)
    #     # TODO: check correct records was returned
    #
    # def _UIT_test_view_team_filter_vereniging_nr(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'filter': '1234'})
    #     self.assertEqual(rsp.status_code, 200)
    #     self.assert_template_used(rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     self.assert_html_ok(rsp)
    #     # TODO: check correct records were returned
    #
    # def _UIT_test_view_team_filter_string(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'filter': 'club'})
    #     self.assertEqual(rsp.status_code, 200)
    #     self.assert_template_used(rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     self.assert_html_ok(rsp)
    #     # TODO: check correct records were returned

# TODO: assert_other_http_commands_not_supported

# end of file
