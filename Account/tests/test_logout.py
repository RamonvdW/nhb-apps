# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestAccountLogout(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; module Logout """

    url_login = '/account/login/'
    url_logout = '/account/logout/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_metmail = self.e2e_create_account('metmail', 'metmail@test.com', 'MetMail')

    def test_logout(self):
        # controleer wat er gebeurd indien niet ingelogd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logout)
        self.assert_is_redirect(resp, '/plein/')

        # log in
        with self.assert_max_queries(21):
            resp = self.client.post(self.url_login, {'login_naam': 'normaal',
                                                     'wachtwoord': E2EHelpers.WACHTWOORD}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))

        # logout pagina ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logout)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('account/uitloggen.dtl', 'plein/site_layout.dtl'))

        # echt uitloggen via een POST
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_logout, {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_login, post=False)


# end of file
