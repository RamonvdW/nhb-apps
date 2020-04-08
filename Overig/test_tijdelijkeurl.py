# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers
from .models import save_tijdelijke_url
from .tijdelijke_url import tijdelijkeurl_dispatcher, set_tijdelijke_url_receiver, \
                            RECEIVER_BEVESTIG_EMAIL, maak_tijdelijke_url_accountemail, \
                            RECEIVER_ACCOUNT_WISSEL, maak_tijdelijke_url_accountwissel
from Account.models import AccountEmail


class TestOverigTijdelijkeUrl(E2EHelpers, TestCase):
    """ unit tests voor de Overig applicatie, module Tijdelijke Urls """

    def setUp(self):
        """ initialisatie van de test case """
        tijdelijkeurl_dispatcher.test_backup()

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_admin = self.e2e_create_account_admin()

        email, created_new = AccountEmail.objects.get_or_create(account=self.account_normaal)
        email.nieuwe_email = "hoi@gmail.not"
        email.save()
        self.email_normaal = email

        save_tijdelijke_url('code1', 'bevestig_email', geldig_dagen=-1)       # verlopen
        #save_tijdelijke_url('code2', 'bevestig_email', geldig_dagen=1)        # no accountemail

    def tearDown(self):
        tijdelijkeurl_dispatcher.test_restore()

    def test_nonexist(self):
        resp = self.client.get('/overig/url/test/')
        self.assertEqual(resp.status_code, 404)

    def test_verlopen(self):
        resp = self.client.get('/overig/url/code1/')
        self.assertEqual(resp.status_code, 404)

    def test_geen_accountemail(self):
        resp = self.client.get('/overig/url/code2/')
        self.assertEqual(resp.status_code, 404)

    def test_onbekend(self):
        save_tijdelijke_url('code3', 'onbekende code', geldig_dagen=1)
        resp = self.client.get('/overig/url/code3/')
        self.assertEqual(resp.status_code, 404)

    def test_setup_dispatcher(self):
        set_tijdelijke_url_receiver("mytopic", "123")
        self.assertEqual(tijdelijkeurl_dispatcher.get_receiver("mytopic"), "123")

    def _my_receiver_func(self, request, accountemail):
        # self.assertEqual(request, "request")
        self.assertEqual(accountemail, self.email_normaal)
        self.callback_count += 1
        return "/overig/feedback/bedankt/"

    def test_accountemail(self):
        set_tijdelijke_url_receiver(RECEIVER_BEVESTIG_EMAIL, self._my_receiver_func)
        url = maak_tijdelijke_url_accountemail(self.email_normaal, test="een")
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 0
        resp = self.client.get(url, follow=True)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

    def test_accountwissel(self):
        set_tijdelijke_url_receiver(RECEIVER_ACCOUNT_WISSEL, self._my_receiver_func)
        url = maak_tijdelijke_url_accountwissel(self.email_normaal, test="twee")
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 0
        resp = self.client.get(url, follow=True)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

# TODO: add use of assert_other_http_commands_not_supported

# end of file
