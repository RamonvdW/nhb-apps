# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Geo.models import Regio
from Spelden.models import Speld, SpeldScore, SpeldAanvraag
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestSpeldenInfoViews(E2EHelpers, TestCase):

    """ tests voor de Spelden applicatie, informatie views """

    url_begin = '/webwinkel/spelden/'
    url_graadspelden = '/webwinkel/spelden/graadspelden/'
    url_meesterspelden = '/webwinkel/spelden/meesterspelden/'
    url_hall_of_fame = '/webwinkel/spelden/meesterspelden/hall-of-fame/'
    url_tussenspelden = '/webwinkel/spelden/tussenspelden/'
    url_arrowhead = '/webwinkel/spelden/arrowhead/'
    url_sterspelden = '/webwinkel/spelden/sterspelden/'
    url_target_awards = '/webwinkel/spelden/target-awards/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()

        # maak een vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        # maak de sporter aan
        self.account_sporter = self.e2e_create_account('100001', 'normaal@test.com', 'Normaal')
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_sporter,
                    email=self.account_sporter.email)
        sporter.save()
        self.sporter_100001 = sporter

    def test_anon(self):
        self.client.logout()

        # begin
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/begin.dtl', 'design/site_layout.dtl'))

        # meesterspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_meesterspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-meesterspelden.dtl', 'design/site_layout.dtl'))

        # meesterspelden hall of fame
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_hall_of_fame)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-meesterspelden_hall-of-fame.dtl', 'design/site_layout.dtl'))

        # graadspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_graadspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-graadspelden.dtl', 'design/site_layout.dtl'))

        # tussenspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_tussenspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-tussenspelden.dtl', 'design/site_layout.dtl'))

        # arrowhead
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_arrowhead)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/wa-arrowhead-spelden.dtl', 'design/site_layout.dtl'))

        # sterspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_sterspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/wa-sterspelden.dtl', 'design/site_layout.dtl'))

        # target
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_target_awards)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/wa-target-awards.dtl', 'design/site_layout.dtl'))

        speld = Speld.objects.first()
        self.assertTrue(str(speld) != '')

        speld_score = SpeldScore.objects.first()
        self.assertTrue(str(speld_score) != '')

        aanvraag = SpeldAanvraag(door_account=self.account_sporter, datum_wedstrijd='Hallo')
        self.assertTrue(str(aanvraag) != '')

    def test_sporter(self):
        self.e2e_login(self.account_sporter)

        # begin
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/begin.dtl', 'design/site_layout.dtl'))

        # meesterspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_meesterspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-meesterspelden.dtl', 'design/site_layout.dtl'))

        # meesterspelden hall of fame
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_hall_of_fame)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-meesterspelden_hall-of-fame.dtl', 'design/site_layout.dtl'))

        # graadspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_graadspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-graadspelden.dtl', 'design/site_layout.dtl'))

        # tussenspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_tussenspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/khsn-tussenspelden.dtl', 'design/site_layout.dtl'))

        # arrowhead
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_arrowhead)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/wa-arrowhead-spelden.dtl', 'design/site_layout.dtl'))

        # sterspelden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_sterspelden)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/wa-sterspelden.dtl', 'design/site_layout.dtl'))

        # target
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_target_awards)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/wa-target-awards.dtl', 'design/site_layout.dtl'))

# end of file
