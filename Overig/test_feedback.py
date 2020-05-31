# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
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

        # TODO: add real feedback to the database, for better tests

    def test_smileys(self):
        # controleer de links vanuit de drie smileys
        url = '/plein/'
        resp = self.client.get(url)
        self.assertContains(resp, 'Wat vind je van deze pagina?')
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=False)
        self.assertTrue('/overig/feedback/min/plein-bezoeker/' in urls)
        self.assertTrue('/overig/feedback/nul/plein-bezoeker/' in urls)
        self.assertTrue('/overig/feedback/plus/plein-bezoeker/' in urls)

    def test_feedback_get(self):
        resp = self.client.get('/overig/feedback/min/plein/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get('/overig/feedback/nul/plein/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get('/overig/feedback/plus/plein/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get('/overig/feedback/huh/plein/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported('/overig/feedback/nul/plein/', post=False)

    def test_feedback_bedankt(self):
        resp = self.client.get('/overig/feedback/bedankt/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.e2e_assert_other_http_commands_not_supported('/overig/feedback/bedankt/')

    def test_feedback_post_anon(self):
        self.e2e_logout()
        resp = self.client.get('/overig/feedback/nul/plein/')    # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/overig/feedback/bedankt/')
        self.e2e_assert_other_http_commands_not_supported('/overig/feedback/nul/plein/', post=False)   # post mag wel

    def test_feedback_post_user(self):
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 20*'Just testing '})   # 20x makes it >80 chars long
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/overig/feedback/bedankt/')
        obj = SiteFeedback.objects.all()[0]
        descr = str(obj)
        self.assertGreater(len(descr), 0)

    def test_feedback_post_anon_illegal_feedback(self):
        self.e2e_logout()
        resp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': ''})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_feedback_post_anon_illegal_bevinding(self):
        self.e2e_logout()
        resp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '5', 'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_feedback_post_without_get(self):
        # probeer een post van het formulier zonder de get
        self.e2e_logout()
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_feedback_afgehandeld(self):
        self.e2e_logout()
        resp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 302)  # redirect to bedankt pagina
        obj = SiteFeedback.objects.all()[0]
        self.assertFalse(obj.is_afgehandeld)
        obj.is_afgehandeld = True
        obj.save()
        descr = str(obj)
        self.assertTrue("(afgehandeld) " in descr)

    def test_get_feedback_formulier(self):
        # get van het formulier is niet de bedoeling
        self.e2e_logout()
        resp = self.client.get('/overig/feedback/formulier/')
        self.assertEqual(resp.status_code, 404)

    def test_feedback_inzicht_anon_redirect_login(self):
        # zonder inlog is feedback niet te zien
        self.e2e_logout()
        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 302)  # redirect
        self.assertRedirects(resp, '/plein/')

    def test_feedback_inzicht_user_forbidden(self):
        # do een get van het logboek met een gebruiker die daar geen rechten toe heeft
        # resulteert rauwe Forbidden
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect (naar het plein)

    def test_feedback_inzicht_admin(self):
        # do een get van alle feedback als IT beheerder
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_beheerder()

        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-inzicht.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "door de ontwikkelaar afgehandeld")
        self.e2e_assert_other_http_commands_not_supported('/overig/feedback/inzicht/')

    def test_feedback_inzicht_bb(self):
        # do een get van alle feedback als BB
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-inzicht.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "door de ontwikkelaar afgehandeld")
        self.e2e_assert_other_http_commands_not_supported('/overig/feedback/inzicht/')

# end of file
