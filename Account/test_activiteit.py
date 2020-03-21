# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Account, AccountEmail,is_email_valide
from Plein.tests import assert_html_ok, assert_template_used


class TestAccountActiviteit(TestCase):
    """ unit tests voor de Account applicatie; module Account Activiteit """

    def setUp(self):
        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

    def test_activiteit_anon(self):
        # test ophalen van het inlog formulier
        self.client.logout()
        resp = self.client.get('/account/activiteit/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_activiteit_normaal(self):
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        resp = self.client.get('/account/activiteit/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-gebruiker.dtl', 'plein/site_layout.dtl'))

    def test_activiteit_admin(self):
        self.client.login(username=self.account_admin.username, password='wachtwoord')
        resp = self.client.get('/account/activiteit/', follow=True)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/activiteit.dtl', 'plein/site_layout.dtl'))

# end of file
