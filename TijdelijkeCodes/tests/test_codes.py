# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.http import HttpResponseRedirect
from Functie.models import Functie
from TijdelijkeCodes.definities import (RECEIVER_BEVESTIG_ACCOUNT_EMAIL, RECEIVER_ACCOUNT_WISSEL,
                                        RECEIVER_WACHTWOORD_VERGETEN, RECEIVER_BEVESTIG_FUNCTIE_EMAIL)
from TijdelijkeCodes.models import TijdelijkeCode, save_tijdelijke_code
from TijdelijkeCodes.operations import (tijdelijkeurl_dispatcher, set_tijdelijke_codes_receiver,
                                        maak_tijdelijke_code_account_email,
                                        maak_tijdelijke_code_accountwissel,
                                        maak_tijdelijke_code_wachtwoord_vergeten,
                                        maak_tijdelijke_code_functie_email)
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from datetime import timedelta


class TestTijdelijkeCodes(E2EHelpers, TestCase):

    """ tests voor de TijdelijkeCodes applicatie """

    testdata = None
    url_code_prefix = '/tijdelijke-codes/'
    url_code = '/tijdelijke-codes/%s/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """
        tijdelijkeurl_dispatcher.test_backup()

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.account_normaal.nieuwe_email = "hoi@gmail.not"
        self.account_normaal.save(update_fields=['nieuwe_email'])

    def tearDown(self):
        tijdelijkeurl_dispatcher.test_restore()

    def test_nonexist(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_code % 'test')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-fout.dtl', 'plein/site_layout.dtl'))

    def test_verlopen(self):
        obj = save_tijdelijke_code('code1', 'iets_anders', geldig_dagen=-1)
        self.assertTrue(str(obj) != '')

        obj = save_tijdelijke_code('code1', 'bevestig_email', geldig_dagen=1)
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_code % 'code1')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        url = urls[0]

        # pas de datum aan zodat deze verlopen is tijdens de POST
        obj.geldig_tot = obj.aangemaakt_op - timedelta(days=1)
        obj.save()

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_bad_dispatch_to(self):
        save_tijdelijke_code('code3', 'onbekend', geldig_dagen=1)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_code % 'code3')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_setup_dispatcher(self):
        set_tijdelijke_codes_receiver("my topic", "123")
        self.assertEqual(tijdelijkeurl_dispatcher.get_receiver("my topic"), "123")

    def _my_receiver_func_email(self, request, hoortbij_account):
        # self.assertEqual(request, "request")
        self.assertEqual(hoortbij_account, self.account_normaal)
        self.callback_count += 1
        url = "/feedback/bedankt/"
        if self.callback_count == 1:
            # return url
            return url
        else:
            # return response
            return HttpResponseRedirect(url)

    def test_account_email(self):
        set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_ACCOUNT_EMAIL, self._my_receiver_func_email)

        url = maak_tijdelijke_code_account_email(self.account_normaal, test="een")
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 1

        # extra coverage
        obj = TijdelijkeCode.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        self.assertEqual(self.callback_count, 1)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 2)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'plein/site_layout.dtl'))

    def test_account_wissel(self):
        set_tijdelijke_codes_receiver(RECEIVER_ACCOUNT_WISSEL, self._my_receiver_func_email)

        url = maak_tijdelijke_code_accountwissel(self.account_normaal, test="twee")
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'plein/site_layout.dtl'))

    def test_wachtwoord_vergeten(self):
        set_tijdelijke_codes_receiver(RECEIVER_WACHTWOORD_VERGETEN, self._my_receiver_func_email)
        url = maak_tijdelijke_code_wachtwoord_vergeten(self.account_normaal, test="drie")
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        self.assertTrue(self.url_code_prefix in urls[0])
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'plein/site_layout.dtl'))

    def _my_receiver_func_functie(self, request, hoortbij_functie):
        # self.assertEqual(request, "request")
        self.callback_count += 1
        url = "/feedback/bedankt/"
        return url

    def test_functie_email(self):
        set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_FUNCTIE_EMAIL, self._my_receiver_func_functie)

        functie = Functie.objects.filter(rol='BKO').all()[0]
        url = maak_tijdelijke_code_functie_email(functie)
        self.assertTrue(self.url_code_prefix in url)
        self.callback_count = 0

        # extra coverage
        obj = TijdelijkeCode.objects.all()[0]
        self.assertTrue(str(obj) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('tijdelijkecodes/code-goed.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        # print('urls: %s' % repr(urls))
        self.assertEqual(1, len(urls))
        url = urls[0]
        self.assertTrue(self.url_code_prefix in url)
        self.assertEqual(self.callback_count, 0)

        # volg de 'ga door' knop
        with self.assert_max_queries(20):
            resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.callback_count, 1)
        # _my_receiver_func stuurt door naar de feedback-bedankt pagina
        self.assert_template_used(resp, ('feedback/bedankt.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_code % '0')

    # TODO verwijder in v20 of later
    def test_oude_url(self):
        # tijdelijke ondersteuning van de oude url
        code = 123456
        url = '/overig/url/%s/' % code
        resp = self.client.get(url)
        self.assert_is_redirect(resp, self.url_code % code)


# FUTURE: tijdelijke URL horende bij kampioenschap

# end of file
