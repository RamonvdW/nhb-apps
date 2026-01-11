# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Sporter.models import Sporter, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestSporterParaOpmerkingen(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Para Opmerkingen """

    url_para_opmerkingen = '/sporter/para-opmerkingen/'
    url_wijzig_opmerking = '/sporter/para-opmerkingen/%s/wijzig/'   # sporter_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """

        # maak een test lid aan
        sporter = Sporter.objects.create(
                        lid_nr=100001,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Tester",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        para_classificatie='DIS')
        self.sporter = sporter

        voorkeuren = SporterVoorkeuren.objects.create(sporter=sporter,
                                                      para_voorwerpen=True,
                                                      opmerking_para_sporter='Test')
        self.voorkeuren = voorkeuren

    def test_anon(self):
        # zonder login --> terug naar het plein
        resp = self.client.get(self.url_para_opmerkingen)
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_wijzig_opmerking)
        self.assert_is_redirect_login(resp)

    def test_lijst(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        # lijst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_para_opmerkingen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/para-opmerkingen-lijst.dtl', 'design/site_layout.dtl'))

        # lege lijst
        self.voorkeuren.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_para_opmerkingen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/para-opmerkingen-lijst.dtl', 'design/site_layout.dtl'))

    def test_wijzig(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        # get
        url = self.url_wijzig_opmerking % self.sporter.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/para-opmerkingen-wijzig.dtl', 'design/site_layout.dtl'))

        # post: switch off
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'para_voorwerpen': '',
                                          'para_notitie': 'aangepast'})
        self.voorkeuren.refresh_from_db()
        self.assertFalse(self.voorkeuren.para_voorwerpen)
        self.assertEqual(self.voorkeuren.opmerking_para_sporter, 'Aangepast')

        # post: switch on
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'para_voorwerpen': 'ja',
                                          'para_notitie': ''})
        self.voorkeuren.refresh_from_db()
        self.assertTrue(self.voorkeuren.para_voorwerpen)
        self.assertEqual(self.voorkeuren.opmerking_para_sporter, '')

        # corner cases
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_opmerking % 999999)
        self.assert404(resp, 'Sporter niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_opmerking % 999999)
        self.assert404(resp, 'Sporter niet gevonden')


# end of file
