# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import Competitie
from GoogleDrive.models import Token
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompBeheerToestemming(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module Toestemming (drive) """

    url_toestemming = '/bondscompetities/beheer/wedstrijdformulieren/toestemming/'
    url_aanmaken = '/bondscompetities/beheer/wedstrijdformulieren/aanmaken/'
    url_kies = '/bondscompetities/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def test_toestemming(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # geen toestemming tot de google drive
        self.assertEqual(Token.objects.count(), 0)

        resp = self.client.get(self.url_toestemming)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/drive-toestemming.dtl', 'design/site_layout.dtl'))

        resp = self.client.post(self.url_toestemming)
        redir_url = self.assert_is_redirect_not_plein(resp)
        self.assertIn('https://accounts.google.com/o/oauth2/auth?response_type=code', redir_url[:80])

        # maak de toestemming
        Token.objects.create()

        # al gegeven
        resp = self.client.get(self.url_toestemming)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/drive-toestemming.dtl', 'design/site_layout.dtl'))

    def test_aanmaken(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # geen toestemming tot de google drive
        self.assertEqual(Token.objects.count(), 0)

        resp = self.client.get(self.url_aanmaken)
        self.assert404(resp, 'Geen toestemming')

        # maak de toestemming
        Token.objects.create()

        resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/drive-aanmaken.dtl', 'design/site_layout.dtl'))

        # aanmaken zonder competities
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        # aanmaken met competities
        Competitie.objects.create(beschrijving="Indoor", afstand="18", begin_jaar=1900)
        Competitie.objects.create(beschrijving="25m 1pijl", afstand="25", begin_jaar=1900)

        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

# end of file
