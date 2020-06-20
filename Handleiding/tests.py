# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers


class TestHandleiding(E2EHelpers, TestCase):
    """ unit tests voor de Handleiding applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        """ initialisatie van de test case """
        self.account = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.url = '/handleiding/'

    def test_anon(self):
        resp = self.client.get(self.url)
        self.assert_is_redirect(resp, '/plein/')

    def test_gebruiker(self):
        self.e2e_login(self.account)
        resp = self.client.get(self.url)
        self.assert_is_redirect(resp, '/plein/')

    def test_beheerder(self):
        self.account.is_BB = True
        self.account.save()
        self.e2e_login(self.account)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('handleiding/Hoofdpagina.dtl', 'plein/site_layout.dtl'))


# end of file
