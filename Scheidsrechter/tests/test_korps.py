# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.definities import SCHEIDS_NIET, SCHEIDS_BOND, SCHEIDS_INTERNATIONAAL
from Functie.models import Functie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Sporter.models import Sporter, SporterVoorkeuren


class TestScheidsrechterKorps(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; module Overzicht """

    test_after = ('Account',)

    url_korps = '/scheidsrechter/korps/'
    url_korps_met_contact = '/scheidsrechter/korps-met-contactgegevens/'

    testdata = None

    scheids_met_account = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:             # pragma: no branch
            if sporter.account is not None:
                cls.scheids_met_account = sporter
                break
        # for

    def setUp(self):
        """ initialisatie van de test case """
        self.assertIsNotNone(self.scheids_met_account)
        self.functie_cs = Functie.objects.get(rol='CS')
        self.voorkeuren = SporterVoorkeuren.objects.get(sporter=self.scheids_met_account)

    def test_anon(self):
        resp = self.client.get(self.url_korps)
        self.assert403(resp)

        resp = self.client.get(self.url_korps_met_contact)
        self.assert403(resp)

    def test_scheids(self):
        self.e2e_login(self.scheids_met_account.account)

        self.scheids_met_account.telefoon = '+3123456789'
        self.scheids_met_account.email = 'scheids@ergens.nl'
        self.scheids_met_account.save(update_fields=['telefoon', 'email'])

        # korps
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps.dtl', 'plein/site_layout.dtl'))
        html = resp.content.decode('utf-8').replace('<wbr>', '')
        self.assertFalse('+3123456789' in html)
        self.assertFalse('@ergens' in html)

        # zet voorkeuren voor delen
        self.voorkeuren.scheids_opt_in_korps_tel_nr = True
        self.voorkeuren.scheids_opt_in_korps_email = True
        self.voorkeuren.save(update_fields=['scheids_opt_in_korps_tel_nr', 'scheids_opt_in_korps_email'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps.dtl', 'plein/site_layout.dtl'))
        html = resp.content.decode('utf-8').replace('<wbr>', '')
        self.assertTrue('+3123456789' in html)
        self.assertTrue('scheids@ergens.nl' in html)

        # corner case: geen voorkeuren
        self.voorkeuren.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps.dtl', 'plein/site_layout.dtl'))

        # korps overzicht met contactgegevens is niet toegankelijk
        resp = self.client.get(self.url_korps_met_contact)
        self.assert403(resp, 'Geen toegang')

        # corner case: geen scheidsrechters
        Sporter.objects.exclude(scheids=SCHEIDS_INTERNATIONAAL).update(scheids=SCHEIDS_NIET)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps.dtl', 'plein/site_layout.dtl'))

    def test_cs(self):
        self.functie_cs.accounts.add(self.scheids_met_account.account)

        self.e2e_login_and_pass_otp(self.scheids_met_account.account)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # korps
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps.dtl', 'plein/site_layout.dtl'))

        # korps met contactgegevens
        self.voorkeuren.delete()            # corner case
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_korps_met_contact)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/korps-contactgegevens.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_korps)
        self.e2e_assert_other_http_commands_not_supported(self.url_korps_met_contact)


# end of file
