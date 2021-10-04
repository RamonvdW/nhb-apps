# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from Handleiding.views import reverse_handleiding
from TestHelpers.e2ehelpers import E2EHelpers
from types import SimpleNamespace


class TestHandleiding(E2EHelpers, TestCase):

    """ tests voor de Handleiding applicatie """

    url_top = '/handleiding/'
    url_page = '/handleiding/%s/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

    def test_anon(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assert403(resp)

    def test_gebruiker(self):
        self.e2e_login(self.account)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assert403(resp)

    def test_beheerder(self):
        self.account.is_BB = True
        self.account.save()
        self.e2e_login(self.account)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('handleiding/Hoofdpagina.dtl', 'plein/site_layout.dtl'))

        # doorloop alle handleiding pagina
        for page in settings.HANDLEIDING_PAGINAS:
            url = self.url_page % page
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
        # for

    def test_reverse(self):
        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki/'):
            url = reverse_handleiding(None, settings.HANDLEIDING_TOP)
            self.assertEqual(url, 'https://test.now/wiki/' + settings.HANDLEIDING_TOP)

        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki'):
            url = reverse_handleiding(None, settings.HANDLEIDING_TOP)
            self.assertEqual(url, 'https://test.now/wiki/' + settings.HANDLEIDING_TOP)

        with self.settings(ENABLE_WIKI=False):
            url = reverse_handleiding(None, settings.HANDLEIDING_TOP)
            self.assertEqual(url, self.url_page % settings.HANDLEIDING_TOP)

        # not authenticated
        account = SimpleNamespace()
        request = SimpleNamespace(user=account)
        account.is_authenticated = False

        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki/'):
            url = reverse_handleiding(request, settings.HANDLEIDING_TOP)
            self.assertEqual(url, self.url_page % settings.HANDLEIDING_TOP)

        # authenticated but not IT/BB
        account.is_authenticated = True
        account.is_BB = False
        account.is_staff = False
        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki/'):
            url = reverse_handleiding(request, settings.HANDLEIDING_TOP)
            self.assertEqual(url, self.url_page % settings.HANDLEIDING_TOP)

        # authenticated BB
        account.is_BB = True
        account.is_staff = False
        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki'):
            url = reverse_handleiding(request, settings.HANDLEIDING_TOP)
            self.assertEqual(url, 'https://test.now/wiki/' + settings.HANDLEIDING_TOP)

        # authenticated IT
        account.is_BB = False
        account.is_staff = True
        with self.settings(ENABLE_WIKI=True, WIKI_URL='https://test.now/wiki'):
            url = reverse_handleiding(request, settings.HANDLEIDING_TOP)
            self.assertEqual(url, 'https://test.now/wiki/' + settings.HANDLEIDING_TOP)


# end of file
