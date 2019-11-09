# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
from .models import SiteFeedback

class OverigTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')

    def test_feedback_get(self):
        rsp = self.client.get('/overig/feedback/min/plein/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)

        rsp = self.client.get('/overig/feedback/nul/plein/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)

        rsp = self.client.get('/overig/feedback/plus/plein/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)

        rsp = self.client.get('/overig/feedback/huh/plein/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)

    def test_feedback_bedankt(self):
        rsp = self.client.get('/overig/feedback/bedankt/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        assert_other_http_commands_not_supported(self, '/overig/feedback/bedankt/')

    def test_post_annon(self):
        self.client.logout()
        rsp = self.client.get('/overig/feedback/nul/plein/')    # zet sessie variabelen: op_pagina en gebruiker
        rsp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(rsp.status_code, 302)
        self.assertEqual(rsp.url, '/overig/feedback/bedankt/')
        assert_other_http_commands_not_supported(self, '/overig/feedback/nul/plein/', post=False)   # post mag wel

    def test_post_user(self):
        self.client.login(username='normaal', password='wachtwoord')
        rsp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        rsp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 20*'Just testing '})   # 20x makes it >80 chars long
        self.assertEqual(rsp.status_code, 302)
        self.assertEqual(rsp.url, '/overig/feedback/bedankt/')
        obj = SiteFeedback.objects.all()[0]
        descr = str(obj)
        self.assertGreater(len(descr), 0)

    def test_post_annon_illegal_feedback(self):
        self.client.logout()
        rsp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        rsp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': ''})
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)

    def test_post_annon_illegal_bevinding(self):
        self.client.logout()
        rsp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        rsp = self.client.post('/overig/feedback/formulier/', {'bevinding': '5', 'feedback': 'Just testing'})
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)

    def test_post_without_get(self):
        # probeer een post van het formulier zonder de get
        self.client.logout()
        rsp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)

    def test_afgehandeld(self):
        self.client.logout()
        rsp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        rsp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(rsp.status_code, 302)
        obj = SiteFeedback.objects.all()[0]
        self.assertFalse(obj.is_afgehandeld)
        obj.is_afgehandeld = True
        obj.save()
        descr = str(obj)
        self.assertTrue("(afgehandeld) " in descr)

    def test_get_formulier(self):
        # get van het formulier is niet de bedoeling
        self.client.logout()
        rsp = self.client.get('/overig/feedback/formulier/')
        self.assertEqual(rsp.status_code, 404)

    def test_inzicht(self):
        # do een get van alle feedback
        rsp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('overig/site-feedback-inzicht.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        assert_other_http_commands_not_supported(self, '/overig/feedback/inzicht/')

# TODO: add use of assert_other_http_commands_not_supported

# end of file
