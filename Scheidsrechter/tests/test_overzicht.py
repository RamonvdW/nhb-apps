# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.definities import SCHEIDS_BOND
from Functie.models import Functie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestScheidsrechterOverzicht(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; module Overzicht """

    test_after = ('Account',)

    url_plein = '/plein/'
    url_overzicht = '/scheidsrechter/'

    testdata = None

    sr3_met_account = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:             # pragma: no branch
            if sporter.account is not None:
                cls.sr3_met_account = sporter
                break
        # for

    def setUp(self):
        """ initialisatie van de test case """
        self.assertIsNotNone(self.sr3_met_account)
        self.functie_cs = Functie.objects.get(rol='CS')

    def test_anon(self):
        resp = self.client.get(self.url_plein)
        urls = self.extract_all_urls(resp)
        self.assertNotIn(self.url_overzicht, urls)

        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect_login(resp, self.url_overzicht)

    def test_sr3(self):
        self.e2e_login(self.sr3_met_account.account)

        # plein heeft kaartje voor scheidsrechters
        resp = self.client.get(self.url_plein)
        urls = self.extract_all_urls(resp)
        self.assertIn(self.url_overzicht, urls)

        # scheids overzicht
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/overzicht.dtl', 'design/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_cs(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # plein heeft kaartje voor scheidsrechters
        resp = self.client.get(self.url_plein)
        urls = self.extract_all_urls(resp)
        self.assertIn(self.url_overzicht, urls)

        # scheids overzicht
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/overzicht.dtl', 'design/site_layout.dtl'))


# end of file
