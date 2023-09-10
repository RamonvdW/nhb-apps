# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from Functie.definities import SCHEIDS_BOND, SCHEIDS_VERENIGING, SCHEIDS_INTERNATIONAAL
from Functie.models import Functie
from Geo.models import Regio
from Mailer.models import MailQueue
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Sporter.models import Sporter
from Vereniging.models import Vereniging
from Vereniging.models2 import Secretaris
import datetime


class TestScheidsrechterOverzicht(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; module Overzicht """

    test_after = ('Account',)

    url_plein = '/plein/'
    url_scheids = '/scheidsrechter/'
    url_korps = url_scheids + 'korps/'
    url_wedstrijden = url_scheids + 'wedstrijden/'

    testdata = None

    scheids_met_account = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:
            if sporter.account is not None:
                cls.scheids_met_account = sporter
                break
        # for

    def setUp(self):
        """ initialisatie van de test case """
        self.assertIsNotNone(self.scheids_met_account)

    def test_anon(self):
        resp = self.client.get(self.url_plein)
        urls = self.extract_all_urls(resp)
        self.assertNotIn(self.url_scheids, urls)

        resp = self.client.get(self.url_scheids)
        self.assert403(resp)

        resp = self.client.get(self.url_korps)
        self.assert403(resp)

        resp = self.client.get(self.url_wedstrijden)
        self.assert403(resp)

    def test_scheids(self):
        self.e2e_login(self.scheids_met_account.account)

        # plein heeft kaartje voor scheidsrechters
        resp = self.client.get(self.url_plein)
        urls = self.extract_all_urls(resp)
        self.assertIn(self.url_scheids, urls)

        # scheids overzicht
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_scheids)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/overzicht.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_scheids)

        # korps
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_korps)

        # wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijden.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)

    def test_bb(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # plein heeft kaartje voor scheidsrechters
        resp = self.client.get(self.url_plein)
        urls = self.extract_all_urls(resp)
        self.assertIn(self.url_scheids, urls)

        # corner case: geen SR5
        Sporter.objects.filter(scheids=SCHEIDS_INTERNATIONAAL).delete()

        # korps
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps.dtl', 'plein/site_layout.dtl'))

        # wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijden.dtl', 'plein/site_layout.dtl'))


# end of file
