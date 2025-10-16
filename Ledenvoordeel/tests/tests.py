# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestLedenvoordeel(E2EHelpers, TestCase):
    """ unittests voor de Ledenvoordeel applicatie """

    url_overzicht = '/ledenvoordeel/'
    url_walibi = '/ledenvoordeel/walibi-2024/'

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver = ver

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_normaal,
                    email=self.account_normaal.email)
        sporter.save()
        self.sporter1 = sporter

    def test_anon(self):
        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_walibi)
        self.assert_is_redirect_login(resp)

    def test_sporter(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('ledenvoordeel/overzicht.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_walibi)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('ledenvoordeel/walibi.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_walibi)

    def test_gast(self):
        # gast-account
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])
        self.e2e_login(self.account_normaal)

        resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        resp = self.client.get(self.url_walibi)
        self.assert403(resp)


# end of file
