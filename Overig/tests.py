# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
from .models import save_tijdelijke_url
from .tijdelijke_url import dispatcher, SAVER, set_tijdelijke_url_receiver, \
                            RECEIVER_BEVESTIG_EMAIL, maak_tijdelijke_url_accountemail, \
                            RECEIVER_SELECTEER_SCHUTTER, maak_tijdelijke_url_selecteer_schutter
from Account.models import Account, AccountEmail


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

        save_tijdelijke_url('code1', 'bevestig_email', geldig_dagen=-1)       # verlopen
        #save_tijdelijke_url('code2', 'bevestig_email', geldig_dagen=1)        # no accountemail

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
        self.callback_count += 1
        return "/overig/feedback/bedankt/"

    def test_tijdelijkeurl_accountemail(self):
        set_tijdelijke_url_receiver(RECEIVER_BEVESTIG_EMAIL, self._my_receiver_func)
        url = maak_tijdelijke_url_accountemail(self.email_normaal, test="een")
        #print("url: %s" % repr(url))
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 0
        resp = self.client.get(url, follow=True)
        self.assertEqual(self.callback_count, 1)
        # redirect is naar de feedback-bedankt pagina
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

    def test_tijdelijkeurl_selecteerschutter(self):
        set_tijdelijke_url_receiver(RECEIVER_SELECTEER_SCHUTTER, self._my_receiver_func)
        url = maak_tijdelijke_url_selecteer_schutter(self.email_normaal, test="twee")
        #print("url: %s" % repr(url))
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 0
        resp = self.client.get(url, follow=True)
        self.assertEqual(self.callback_count, 1)
        # redirect is naar de feedback-bedankt pagina
        self.assertEqual(resp.status_code, 200)
        assert_template_used(self, resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

# TODO: add use of assert_other_http_commands_not_supported

# end of file
