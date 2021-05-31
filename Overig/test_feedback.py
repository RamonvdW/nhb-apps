# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import SiteFeedback
from Overig.e2ehelpers import E2EHelpers


class TestOverigFeedback(E2EHelpers, TestCase):
    """ unit tests voor de Overig applicatie, module Feedback """

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.e2e_login(self.account_normaal)

        self.url_plein = '/plein/'
        self.url_feedback = '/overig/feedback/%s/%s/'       # min/nul/plus, op_pagina
        self.url_feedback_formulier = '/overig/feedback/formulier/'
        self.url_feedback_min_plein = self.url_feedback % ('min', 'plein')
        self.url_feedback_nul_plein = self.url_feedback % ('nul', 'plein')
        self.url_feedback_plus_plein = self.url_feedback % ('plus', 'plein')
        self.url_feedback_bedankt = '/overig/feedback/bedankt/'
        self.url_feedback_inzicht = '/overig/feedback/inzicht/'

    def test_anon(self):
        # niet ingelogd --> gebruik smileys niet toegestaan
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertNotContains(resp, 'Wat vind je van deze pagina?')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 'Just testing'})
        self.assert403(resp)

        # zonder inlog is feedback niet te zien
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_inzicht)
        self.assert403(resp)

    def test_smileys(self):
        # controleer de links vanuit de drie smileys
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertContains(resp, 'Wat vind je van deze pagina?')
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=False)
        self.assertTrue('/overig/feedback/min/plein-bezoeker/' in urls)
        self.assertTrue('/overig/feedback/nul/plein-bezoeker/' in urls)
        self.assertTrue('/overig/feedback/plus/plein-bezoeker/' in urls)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_min_plein)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_nul_plein)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_plus_plein)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback % ('huh', 'plein'))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_feedback_nul_plein, post=False)

    def test_bedankt(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_bedankt)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_feedback_bedankt)

    def test_form(self):
        with self.assert_max_queries(20):
            # zet sessie variabelen: op_pagina en gebruiker
            self.client.get(self.url_feedback_nul_plein)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 20*'Just testing '})   # 20x makes it >80 chars long
        self.assert_is_redirect(resp, self.url_feedback_bedankt)
        obj = SiteFeedback.objects.all()[0]
        descr = str(obj)
        self.assertGreater(len(descr), 0)

    def test_form_bad(self):
        with self.assert_max_queries(20):
            # zet sessie variabelen: op_pagina en gebruiker
            resp = self.client.get(self.url_feedback_nul_plein)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': ''})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '5',
                                     'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_form_get(self):
        # de formulier-url is bedoeld voor een POST, maar staat ook een GET toe
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_formulier)
        self.assert404(resp)

    def test_post_without_get(self):
        # probeer een post van het formulier zonder de get
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_afgehandeld(self):
        with self.assert_max_queries(20):
            # zet sessie variabelen: op_pagina en gebruiker
            resp = self.client.get(self.url_feedback_nul_plein)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 'Just testing'})
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        obj = SiteFeedback.objects.all()[0]
        self.assertFalse(obj.is_afgehandeld)
        obj.is_afgehandeld = True
        obj.save()
        descr = str(obj)
        self.assertTrue("(afgehandeld) " in descr)

    def test_inzicht_user_forbidden(self):
        # do een get van het logboek met een gebruiker die daar geen rechten toe heeft
        # resulteert rauwe Forbidden
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_inzicht)
        self.assert403(resp)

    def test_inzicht_admin(self):
        # do een get van alle feedback als IT beheerder
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_it()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_inzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-inzicht.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "door de ontwikkelaar afgehandeld")

        self.e2e_assert_other_http_commands_not_supported(self.url_feedback_inzicht)

    def test_inzicht_bb(self):
        # do een get van alle feedback als BB
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_inzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-inzicht.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "door de ontwikkelaar afgehandeld")

        self.e2e_assert_other_http_commands_not_supported(self.url_feedback_inzicht)

# end of file
