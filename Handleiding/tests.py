# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from Handleiding.views import reverse_handleiding
from Overig.e2ehelpers import E2EHelpers


class TestHandleiding(E2EHelpers, TestCase):
    """ unit tests voor de Handleiding applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        """ initialisatie van de test case """
        self.account = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.url = '/handleiding/'

    def test_anon(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url)
        self.assert_is_redirect(resp, '/plein/')

    def test_gebruiker(self):
        self.e2e_login(self.account)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url)
        self.assert_is_redirect(resp, '/plein/')

    def test_beheerder(self):
        self.account.is_BB = True
        self.account.save()
        self.e2e_login(self.account)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('handleiding/Hoofdpagina.dtl', 'plein/site_layout.dtl'))

        # doorloop alle handleiding pagina
        for page in settings.HANDLEIDING_PAGINAS:
            url = '/handleiding/%s/' % page
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
        # for

    def test_reverse(self):
        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki/'):
            url = reverse_handleiding(settings.HANDLEIDING_TOP)
            self.assertEqual(url, 'https://test.now/wiki/' + settings.HANDLEIDING_TOP)

        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki'):
            url = reverse_handleiding(settings.HANDLEIDING_TOP)
            self.assertEqual(url, 'https://test.now/wiki/' + settings.HANDLEIDING_TOP)

        with self.settings(ENABLE_WIKI=False):
            url = reverse_handleiding(settings.HANDLEIDING_TOP)
            self.assertEqual(url, '/handleiding/%s/' % settings.HANDLEIDING_TOP)

# end of file
