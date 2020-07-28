# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers


class TestAccountActiviteit(E2EHelpers, TestCase):
    """ unit tests voor de Account applicatie; module Account Activiteit """

    test_after = ('Account.test_login',)

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

    def test_activiteit_anon(self):
        # geen inlog = geen toegang
        self.e2e_logout()
        resp = self.client.get('/account/activiteit/')
        self.assert_is_redirect(resp, '/plein/')

    def test_activiteit_normaal(self):
        # inlog maar geen rechten
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/account/activiteit/')
        self.assert_is_redirect(resp, '/plein/')

    def test_activiteit_bb(self):
        # inlog met rechten
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.e2e_login(self.account_normaal)

        # wissel-van-rol is niet nodig (Account weet daar niets van)
        with self.assertNumQueries(7):
            resp = self.client.get('/account/activiteit/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/activiteit.dtl', 'plein/site_layout.dtl'))

    def test_activiteit_admin(self):
        # admin rechten
        self.e2e_login(self.account_admin)
        # wissel-van-rol is niet nodig (Account weet daar niets van)
        with self.assertNumQueries(7):
            resp = self.client.get('/account/activiteit/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/activiteit.dtl', 'plein/site_layout.dtl'))

# TODO: gebruik assert_other_http_commands_not_supported

# end of file
