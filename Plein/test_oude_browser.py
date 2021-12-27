# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from .views import is_browser_supported
import types


class TestPlein(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie """

    test_after = ('Functie',)

    url_root = '/'
    url_plein = '/plein/'
    url_niet_ondersteund = '/plein/niet-ondersteund/'

    useragent_msie_1 = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)'
    useragent_msie_2 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko'
    useragent_firefox = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0'

    def test_is_browser_supported(self):
        request = types.SimpleNamespace()
        request.META = dict()

        # geen header
        self.assertTrue(is_browser_supported(request))

        # internet explorer
        request.META['HTTP_USER_AGENT'] = self.useragent_msie_1
        self.assertFalse(is_browser_supported(request))
        request.META['HTTP_USER_AGENT'] = self.useragent_msie_2
        self.assertFalse(is_browser_supported(request))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_root, HTTP_USER_AGENT=self.useragent_msie_1)
        self.assert_is_redirect(resp, self.url_niet_ondersteund)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein, HTTP_USER_AGENT=self.useragent_msie_2)
        self.assert_is_redirect(resp, self.url_niet_ondersteund)

        # andere
        request.META['HTTP_USER_AGENT'] = self.useragent_firefox
        self.assertTrue(is_browser_supported(request))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_root, HTTP_USER_AGENT=self.useragent_firefox)
        self.assert_is_redirect(resp, self.url_plein)

    def test_niet_ondersteund(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_niet_ondersteund)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/niet-ondersteund.dtl',))
        self.assert_html_ok(resp)

        # site_layout.dtl moet niet gebruikt worden ivm alle javascript
        for templ in resp.templates:
            self.assertFalse("site_layout.dtl" in templ.name)
        # for

        self.e2e_assert_other_http_commands_not_supported(self.url_niet_ondersteund)


# end of file
