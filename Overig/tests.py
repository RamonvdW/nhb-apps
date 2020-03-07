# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
from .models import SiteFeedback, save_tijdelijke_url
from .helpers import get_safe_from_ip
from .tijdelijke_url import dispatcher, SAVER, set_tijdelijke_url_receiver, \
                            RECEIVER_ACCOUNTEMAIL, maak_tijdelijke_url_accountemail
from Account.models import Account, AccountEmail, account_vhpg_is_geaccepteerd,\
                           account_zet_sessionvars_na_otp_controle, account_zet_sessionvars_na_login
from Account.rol import rol_zet_sessionvars_na_otp_controle, rol_zet_sessionvars_na_login, rol_activeer_rol


class TestOverig(TestCase):
    """ unit tests voor de Overig applicatie """

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')

        self.account_normaal = Account.objects.get(username='normaal')
        self.account_admin = Account.objects.get(username='admin')
        # TODO: add real feedback to the database, for better tests

        email, created_new = AccountEmail.objects.get_or_create(account=self.account_normaal)
        email.nieuwe_email = "hoi@gmail.not"
        email.save()
        self.email_normaal = email

        save_tijdelijke_url('code1', geldig_dagen=-1)       # verlopen
        save_tijdelijke_url('code2', geldig_dagen=1)        # no accountemail

    def test_feedback_get(self):
        resp = self.client.get('/overig/feedback/min/plein/')
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)

        resp = self.client.get('/overig/feedback/nul/plein/')
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)

        resp = self.client.get('/overig/feedback/plus/plein/')
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)

        resp = self.client.get('/overig/feedback/huh/plein/')
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)

    def test_feedback_bedankt(self):
        resp = self.client.get('/overig/feedback/bedankt/')
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        assert_other_http_commands_not_supported(self, '/overig/feedback/bedankt/')

    def test_feedback_post_annon(self):
        self.client.logout()
        resp = self.client.get('/overig/feedback/nul/plein/')    # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/overig/feedback/bedankt/')
        assert_other_http_commands_not_supported(self, '/overig/feedback/nul/plein/', post=False)   # post mag wel

    def test_feedback_post_user(self):
        self.client.login(username='normaal', password='wachtwoord')
        resp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 20*'Just testing '})   # 20x makes it >80 chars long
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/overig/feedback/bedankt/')
        obj = SiteFeedback.objects.all()[0]
        descr = str(obj)
        self.assertGreater(len(descr), 0)

    def test_feedback_post_annon_illegal_feedback(self):
        self.client.logout()
        resp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': ''})
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)

    def test_feedback_post_annon_illegal_bevinding(self):
        self.client.logout()
        resp = self.client.get('/overig/feedback/nul/plein/')   # zet sessie variabelen: op_pagina en gebruiker
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '5', 'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)

    def test_feedback_post_without_get(self):
        # probeer een post van het formulier zonder de get
        self.client.logout()
        resp = self.client.post('/overig/feedback/formulier/', {'bevinding': '4', 'feedback': 'Just testing'})
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-formulier.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)

    def test_feedback_afgehandeld(self):
        self.client.logout()
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
        self.client.logout()
        resp = self.client.get('/overig/feedback/formulier/')
        self.assertEqual(resp.status_code, 404)

    def test_feedback_inzicht_annon_redirect_login(self):
        # zonder inlog is feedback niet te zien
        self.client.logout()
        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 302)  # redirect
        self.assertRedirects(resp, '/account/login/?next=/overig/feedback/inzicht/')

    def test_feedback_inzicht_user_forbidden(self):
        # do een get van het logboek met een gebruiker die daar geen rechten toe heeft
        # resulteert rauwe Forbidden
        self.client.login(username='normaal', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()
        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 403)  # 403 = Forbidden

    def test_feedback_inzicht_admin(self):
        # do een get van alle feedback
        account_vhpg_is_geaccepteerd(self.account_admin)
        self.client.login(username=self.account_admin.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()
        rol_activeer_rol(self.client, 'beheerder').save()
        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-inzicht.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        self.assertContains(resp, "door de ontwikkelaar afgehandeld")
        assert_other_http_commands_not_supported(self, '/overig/feedback/inzicht/')

    def test_feedback_inzicht_bb(self):
        # do een get van alle feedback
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        account_vhpg_is_geaccepteerd(self.account_normaal)
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_normaal, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        resp = self.client.get('/overig/feedback/inzicht/')
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-inzicht.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        self.assertContains(resp, "door de ontwikkelaar afgehandeld")
        assert_other_http_commands_not_supported(self, '/overig/feedback/inzicht/')

    def test_tijdelijkeurl_nonexist(self):
        resp = self.client.get('/overig/url/test/')
        self.assertEqual(resp.status_code, 404)

    def test_tijdelijkeurl_verlopen(self):
        resp = self.client.get('/overig/url/code1/')
        self.assertEqual(resp.status_code, 404)

    def test_tijdelijkeurl_geen_accountemail(self):
        resp = self.client.get('/overig/url/code2/')
        self.assertEqual(resp.status_code, 404)

    def test_tijdelijkeurl_setup_dispatcher(self):
        self.assertTrue(SAVER in dispatcher)
        old = dispatcher[SAVER]
        set_tijdelijke_url_receiver("mytopic", "123")
        self.assertEqual(dispatcher["mytopic"], "123")
        self.assertEqual(dispatcher[SAVER], old)
        # controleer bescherming tegen overschrijven SAVER entry
        set_tijdelijke_url_receiver(SAVER, "456")
        self.assertEqual(dispatcher[SAVER], old)

    def _my_receiver_func(self, request, accountemail):
        # self.assertEqual(request, "request")
        self.assertEqual(accountemail, self.email_normaal)
        self.got_callback = True
        return "/overig/feedback/bedankt/"

    def test_tijdelijkeurl_accountemail(self):
        set_tijdelijke_url_receiver(RECEIVER_ACCOUNTEMAIL, self._my_receiver_func)
        url = maak_tijdelijke_url_accountemail(self.email_normaal, test="ja")
        self.assertTrue("/overig/url/" in url)
        self.got_callback = False
        # print("url: %s" % repr(url))
        resp = self.client.get(url, follow=True)
        self.assertTrue(self.got_callback)
        # redirect is naar de feedback-bedankt pagina
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

    def test_get_safe_from_ip(self):
        self.assertEqual(get_safe_from_ip(None), "")

        self.assertEqual(get_safe_from_ip(self.client), "")

        self.client.META = dict()
        self.assertEqual(get_safe_from_ip(self.client), "")

        self.client.META['REMOTE_ADDR'] = '1.2.3.4'
        self.assertEqual(get_safe_from_ip(self.client), "1.2.3.4")

        self.client.META['REMOTE_ADDR'] = '100.200.300.400'
        self.assertEqual(get_safe_from_ip(self.client), "100.200.300.400")

        self.client.META['REMOTE_ADDR'] = ''
        self.assertEqual(get_safe_from_ip(self.client), "")

        self.client.META['REMOTE_ADDR'] = '0000:1111:2222:3344:5555:6666:aabb:ccdd:EEFF'
        self.assertEqual(get_safe_from_ip(self.client), '0000:1111:2222:3344:5555:6666:aabb:ccdd:EEFF')

        self.client.META['REMOTE_ADDR'] = 'wat een puinhoop\0<li>'
        self.assertEqual(get_safe_from_ip(self.client), 'aee')

# TODO: add use of assert_other_http_commands_not_supported

# end of file
