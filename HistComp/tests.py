# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
from .models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam
#from .views import HistCompBaseView
from .forms import FilterForm
import datetime


class TestHistComp(TestCase):
    """ unittests voor de HistComp applicatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        obj = HistCompetitie()
        obj.seizoen = '2018/2019'
        obj.comp_type = '18'
        obj.klasse = 'Testcurve1'       # TODO: kan de klasse een spatie bevatten?
        obj.is_team = False
        obj.save()

        obj.pk = None
        obj.seizoen = '2019/2020'
        obj.klasse = 'Testcurve2'
        obj.save()

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
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

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

    def _add_many_records(self):
        # paginator laat 100 entries per pagina zien, dus voeg er 100 toe
        rec = HistCompetitieIndividueel.objects.all()[0]
        for lp in range(HistCompBaseView.paginate_by):
            rec.pk = None
            rec.rank += 1
            rec.totaal += 10
            rec.save()
        # for

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

    # def _UIT_test_view_allejaren(self):
    #     rsp = self.client.get('/hist/')
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_allejaren.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     assert_other_http_commands_not_supported(self, '/hist/')
    #
    # def _UIT_test_view_indiv(self):
    #     self._add_many_records()
    #     rsp = self.client.get('/hist/2019/18/Testcurve2/indiv/')
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     assert_other_http_commands_not_supported(self, '/hist/2019/18/Testcurve2/indiv/')
    #
    # def _UIT_test_view_bad_comptype(self):
    #     rsp = self.client.get('/hist/2019/42/Testcurve2/indiv/')
    #     self.assertEqual(rsp.status_code, 404)
    #
    # def _UIT_test_form(self):
    #     form = FilterForm(data={})
    #     self.assertTrue(form.is_valid())
    #
    #     form = FilterForm(data={'filter': 'test'})
    #     self.assertTrue(form.is_valid())
    #
    #     form = FilterForm(data={'all': 1})
    #     self.assertTrue(form.is_valid())
    #
    #     form = FilterForm(data={'filter': 'test', 'all': 1, 'pg': 1})
    #     self.assertTrue(form.is_valid())
    #
    # def _UIT_test_view_invid_all(self):
    #     rsp = self.client.get('/hist/2019/18/Testcurve2/indiv/', {'all': '1'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #
    # def _UIT_test_view_indiv_page_2(self):
    #     self._add_many_records()
    #     rsp = self.client.get('/hist/2019/18/Testcurve2/indiv/', {'page': '2'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #
    # def _UIT_test_view_invid_filter_schutter_nr(self):
    #     self._add_many_records()
    #     rsp = self.client.get('/hist/2019/18/Testcurve2/indiv/', {'filter': '123456'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     # TODO: check correct records was returned
    #
    # def _UIT_test_view_invid_filter_vereniging_nr(self):
    #     rsp = self.client.get('/hist/2019/18/Testcurve2/indiv/', {'filter': '1234'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     # TODO: check correct records were returned
    #
    # def _UIT_test_view_invid_filter_string(self):
    #     rsp = self.client.get('/hist/2019/18/Testcurve2/indiv/', {'filter': 'club'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     # TODO: check correct records were returned
    #
    # def _UIT_test_view_invid_empty(self):
    #     rsp = self.client.get('/hist/2019/18/Missing/indiv/')
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_indiv.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     # TODO: check correct records were returned
    #
    # def _UIT_test_view_team_all(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'all': '1'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #
    # def _UIT_test_view_team_filter_schutter_nr(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'filter': '123456'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     # TODO: check correct records was returned
    #
    # def _UIT_test_view_team_filter_vereniging_nr(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'filter': '1234'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     # TODO: check correct records were returned
    #
    # def _UIT_test_view_team_filter_string(self):
    #     rsp = self.client.get('/hist/2019/18/Teamcurve3/team/', {'filter': 'club'})
    #     self.assertEqual(rsp.status_code, 200)
    #     assert_template_used(self, rsp, ('hist/histcomp_team.dtl', 'plein/site_layout.dtl'))
    #     assert_html_ok(self, rsp)
    #     # TODO: check correct records were returned

# end of file
