# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .menu import menu_dynamics
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import types


class TestPlein(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie """

    url_root = '/'
    url_plein = '/plein/'
    url_privacy = '/plein/privacy/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def test_root_redirect(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_root)
        self.assertEqual(resp.status_code, 302)     # 302 = redirect
        self.assertEqual(resp.url, '/plein/')

    def test_privacy(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_privacy)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/privacy.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.e2e_assert_other_http_commands_not_supported(self.url_privacy)

    def test_dynamic_menu_assert(self):
        # test the assert in menu_dynamics
        context = dict()
        request = types.SimpleNamespace()      # creates an empty object
        request.user = types.SimpleNamespace()
        request.user.is_authenticated = False
        with self.assertRaises(AssertionError):
            menu_dynamics(request, context, actief='test-bestaat-niet')

    def test_quick(self):
        # voor test.sh om met een snelle run in debug mode
        # wissel naar IT zodat we het beheerders plein krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_it()
        self.e2e_check_rol('IT')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)

        urls = self.extract_all_urls(resp)      # for coverage

# end of file
