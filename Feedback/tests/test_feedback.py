# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Feedback.models import Feedback, feedback_opschonen
from Feedback.operations import store_feedback
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


class TestFeedback(E2EHelpers, TestCase):

    """ tests voor de Feedback applicatie """

    url_plein = '/plein/'
    url_privacy = '/plein/privacy/'
    url_feedback = '/feedback/%s/%s/%s/'  # min/nul/plus, op_pagina, volledige_url
    url_feedback_min_plein = '/feedback/min/plein-bezoeker/plein/'
    url_feedback_nul_plein = '/feedback/nul/plein-bezoeker/plein/'
    url_feedback_plus_plein = '/feedback/plein-bezoeker/plus/plein/'
    url_feedback_formulier = '/feedback/formulier/'
    url_feedback_bedankt = '/feedback/bedankt/'
    url_feedback_inzicht = '/feedback/inzicht/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

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
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertContains(resp, 'Wat vind je van deze pagina?')
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=False)
        self.assertTrue(self.url_feedback % ('min', 'plein-beheerder', 'plein') in urls)
        self.assertTrue(self.url_feedback % ('nul', 'plein-beheerder', 'plein') in urls)
        self.assertTrue(self.url_feedback % ('plus', 'plein-beheerder', 'plein') in urls)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_min_plein)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_nul_plein)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_plus_plein)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback % ('huh', 'plein', 'plein'))
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_feedback_nul_plein, post=False)

    def test_geen_feedback(self):
        # geen inlog, dan geen feedback
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_privacy)
        self.assertNotContains(resp, 'Wat vind je van deze pagina?')

    def test_bedankt(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_bedankt)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_feedback_bedankt)

    def test_form(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            # zet sessie variabelen: op_pagina en gebruiker
            self.client.get(self.url_feedback_nul_plein)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 20*'Just testing '})   # 20x makes it >80 chars long
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        self.assertEqual(Feedback.objects.count(), 1)
        obj = Feedback.objects.first()
        descr = str(obj)
        self.assertGreater(len(descr), 0)

        # probeer dezelfde feedback nog een keer te posten (wordt voorkomen)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 20*'Just testing '})   # 20x makes it >80 chars long
        self.assert_is_redirect(resp, self.url_feedback_bedankt)
        self.assertEqual(Feedback.objects.count(), 1)

    def test_form_bad(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            # zet sessie variabelen: op_pagina en gebruiker
            resp = self.client.get(self.url_feedback_nul_plein)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': ''})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '5',
                                     'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_form_get(self):
        self.e2e_login(self.account_normaal)

        # de formulier-url is bedoeld voor een POST, maar staat ook een GET toe
        resp = self.client.get(self.url_feedback_formulier)
        self.assert404(resp, 'Pagina bestaat niet')

    def test_post_without_get(self):
        self.e2e_login(self.account_normaal)

        # probeer een post van het formulier zonder de get
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 'Just testing'})
        self.assert404(resp, 'Verkeerd gebruik')

    def test_afgehandeld(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            # zet sessie variabelen: op_pagina en gebruiker
            resp = self.client.get(self.url_feedback_nul_plein)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_feedback_formulier,
                                    {'bevinding': '4',
                                     'feedback': 'Just testing'})
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        obj = Feedback.objects.first()
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

    def test_inzicht_bb(self):
        # do een get van alle feedback als BB
        self.account_normaal.is_BB = True
        self.account_normaal.save(update_fields=['is_BB'])
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_inzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/inzicht.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, "Aantal afgehandeld:")

        self.e2e_assert_other_http_commands_not_supported(self.url_feedback_inzicht)

    def test_inzicht_link_beheer(self):
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        # maak feedback aan
        # zet sessie variabelen: op_pagina en gebruiker
        self.client.get(self.url_feedback_nul_plein)
        resp = self.client.post(self.url_feedback_formulier,
                                {'bevinding': '4',
                                 'feedback': 'Just testing 4'})
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        self.client.get(self.url_feedback_nul_plein)
        resp = self.client.post(self.url_feedback_formulier,
                                {'bevinding': '6',
                                 'feedback': 'Just testing 6'})
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        self.client.get(self.url_feedback_nul_plein)
        resp = self.client.post(self.url_feedback_formulier,
                                {'bevinding': '8',
                                 'feedback': 'Just testing 8'})
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_feedback_inzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('feedback/inzicht.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        urls = self.extract_all_urls(resp, skip_menu=True)
        urls = [url for url in urls if url.startswith('/beheer/Feedback/feedback/')]
        self.assertEqual(len(urls), 3)

    def test_taak(self):
        # controleer aanmaken van een taak

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        self.assertEqual(Taak.objects.count(), 0)

        # maak feedback aan
        self.client.get(self.url_feedback_nul_plein)
        resp = self.client.post(self.url_feedback_formulier,
                                {'bevinding': '4',
                                 'feedback': 'Just testing'})
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        self.assertEqual(Taak.objects.count(), 1)

        # maak nog meer feedback aan
        self.client.get(self.url_feedback_nul_plein)
        resp = self.client.post(self.url_feedback_formulier,
                                {'bevinding': '8',
                                 'feedback': 'Meer getest'})
        self.assert_is_redirect(resp, self.url_feedback_bedankt)

        # controleer dat er niet nog een taak aangemaakt i
        self.assertEqual(Taak.objects.count(), 1)

    def test_opschonen(self):
        f1 = io.StringIO()
        feedback_opschonen(f1)

        # maak een oude, afgehandelde site feedback aan
        store_feedback('mij', 'rol', 'pagina', '/pagina/', Feedback.url2bev['plus'], 'feedback')
        feedback = Feedback.objects.first()
        feedback.toegevoegd_op -= datetime.timedelta(days=92)
        feedback.is_afgehandeld = True
        feedback.save()

        f1 = io.StringIO()
        feedback_opschonen(f1)
        self.assertTrue('[INFO] Verwijder 1 afgehandelde feedback' in f1.getvalue())

# end of file
