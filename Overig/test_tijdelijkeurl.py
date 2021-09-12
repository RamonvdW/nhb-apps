# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.http import HttpResponseRedirect
from Account.models import AccountEmail
from Functie.models import Functie
from .models import save_tijdelijke_url, SiteTijdelijkeUrl
from .tijdelijke_url import (tijdelijkeurl_dispatcher, set_tijdelijke_url_receiver,
                             RECEIVER_BEVESTIG_ACCOUNT_EMAIL, maak_tijdelijke_url_account_email,
                             RECEIVER_ACCOUNT_WISSEL, maak_tijdelijke_url_accountwissel,
                             RECEIVER_WACHTWOORD_VERGETEN, maak_tijdelijke_url_wachtwoord_vergeten,
                             RECEIVER_BEVESTIG_FUNCTIE_EMAIL, maak_tijdelijke_url_functie_email)
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from datetime import timedelta


class TestOverigTijdelijkeUrl(E2EHelpers, TestCase):
    """ unit tests voor de Overig applicatie, module Tijdelijke Urls """

    testdata = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """
        tijdelijkeurl_dispatcher.test_backup()

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        email, created_new = AccountEmail.objects.get_or_create(account=self.account_normaal)
        email.nieuwe_email = "hoi@gmail.not"
        email.save()
        self.email_normaal = email

    def tearDown(self):
        tijdelijkeurl_dispatcher.test_restore()

    def test_nonexist(self):
        with self.assert_max_queries(20):
            resp = self.client.get('/overig/url/test/')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/tijdelijke-url-fout.dtl', 'plein/site_layout.dtl'))

    def test_verlopen(self):
        save_tijdelijke_url('code1', 'iets_anders', geldig_dagen=-1)
        obj = save_tijdelijke_url('code1', 'bevestig_email', geldig_dagen=1)

        # extra coverage
        obj = SiteTijdelijkeUrl.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get('/overig/url/code1/')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/tijdelijke-url-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        self.assertEqual(1, len(urls))
        self.assertTrue('/overig/url/' in urls[0])
        url = urls[0]

        # pas de datum aan zodat deze verlopen is tijdens de POST
        obj.geldig_tot = obj.aangemaakt_op - timedelta(days=1)
        obj.save()

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_bad_dispatch_to(self):
        save_tijdelijke_url('code3', 'onbekend', geldig_dagen=1)

        with self.assert_max_queries(20):
            resp = self.client.get('/overig/url/code3/')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/tijdelijke-url-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue('/overig/url/' in urls[0])

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_setup_dispatcher(self):
        set_tijdelijke_url_receiver("mytopic", "123")
        self.assertEqual(tijdelijkeurl_dispatcher.get_receiver("mytopic"), "123")

    def _my_receiver_func_email(self, request, hoortbij_accountemail):
        # self.assertEqual(request, "request")
        self.assertEqual(hoortbij_accountemail, self.email_normaal)
        self.callback_count += 1
        url = "/overig/feedback/bedankt/"
        if self.callback_count == 1:
            # return url
            return url
        else:
            # return response
            return HttpResponseRedirect(url)

    def test_account_email(self):
        set_tijdelijke_url_receiver(RECEIVER_BEVESTIG_ACCOUNT_EMAIL, self._my_receiver_func_email)

        url = maak_tijdelijke_url_account_email(self.email_normaal, test="een")
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 1

        # extra coverage
        obj = SiteTijdelijkeUrl.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/tijdelijke-url-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue('/overig/url/' in urls[0])
        self.assertEqual(self.callback_count, 1)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 2)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

    def test_account_wissel(self):
        set_tijdelijke_url_receiver(RECEIVER_ACCOUNT_WISSEL, self._my_receiver_func_email)

        url = maak_tijdelijke_url_accountwissel(self.email_normaal, test="twee")
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 0

        # extra coverage
        obj = SiteTijdelijkeUrl.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/tijdelijke-url-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue('/overig/url/' in urls[0])
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

    def test_wachtwoord_vergeten(self):
        set_tijdelijke_url_receiver(RECEIVER_WACHTWOORD_VERGETEN, self._my_receiver_func_email)
        url = maak_tijdelijke_url_wachtwoord_vergeten(self.email_normaal, test="drie")
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 0

        # extra coverage
        obj = SiteTijdelijkeUrl.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/tijdelijke-url-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue('/overig/url/' in urls[0])
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

    def _my_receiver_func_functie(self, request, hoortbij_functie):
        # self.assertEqual(request, "request")
        self.callback_count += 1
        url = "/overig/feedback/bedankt/"
        return url

    def test_functie_email(self):
        set_tijdelijke_url_receiver(RECEIVER_BEVESTIG_FUNCTIE_EMAIL, self._my_receiver_func_functie)

        functie = Functie.objects.filter(rol='BKO').all()[0]
        url = maak_tijdelijke_url_functie_email(functie)
        self.assertTrue("/overig/url/" in url)
        self.callback_count = 0

        # extra coverage
        obj = SiteTijdelijkeUrl.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/tijdelijke-url-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue('/overig/url/' in urls[0])
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('overig/site-feedback-bedankt.dtl', 'plein/site_layout.dtl'))

    def test_other_http(self):
        self.e2e_assert_other_http_commands_not_supported('/overig/url/0/')


# TODO: tijdelijke URL horende bij kampioenschap

# end of file
