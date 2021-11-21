# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from Handleiding.views import reverse_handleiding
from TestHelpers.e2ehelpers import E2EHelpers


class TestHandleiding(E2EHelpers, TestCase):

    """ tests voor de Handleiding applicatie """

    url_top = '/handleiding/'
    url_page = '/handleiding/%s/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

    def test_all(self):
        # anon
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assert403(resp)

        # gebruiker
        self.e2e_login(self.account)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assert403(resp)

        # beheerder
        self.account.is_BB = True
        self.account.save()
        self.e2e_login(self.account)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_top)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('handleiding/Hoofdpagina.dtl', 'plein/site_layout.dtl'))

        url = reverse_handleiding(None, settings.HANDLEIDING_TOP)
        self.assertEqual(url, self.url_page % settings.HANDLEIDING_TOP)

        # doorloop alle handleiding pagina
        for page in settings.HANDLEIDING_PAGINAS:
            url = self.url_page % page
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
        # for


# end of file
