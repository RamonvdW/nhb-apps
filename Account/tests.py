# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Account.models import Account
from Plein.tests import assert_html_ok, assert_template_used

class AccountTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

    def test_inlog_form_get(self):
        # test ophalen van het inlog formulier
        resp = self.client.get('/account/login/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))

    def test_inlog_form_post(self):
        # test inlog via het inlog formulier
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'wachtwoord'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        # redirect is naar het plein
        assert_template_used(self, resp, ('plein/plein.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Uitloggen')

    def test_inlog_form_post_bad_login_naam(self):
        # test inlog via het inlog formulier, met onbekende login naam
        resp = self.client.post('/account/login/', {'login_naam': 'onbekend', 'wachtwoord': 'wachtwoord'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_inlog_form_post_bad_wachtwoord(self):
        # test inlog via het inlog formulier, met verkeerd wachtwoord
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'huh'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

    def test_logout(self):
        resp = self.client.post('/account/login/', {'login_naam': 'normaal', 'wachtwoord': 'wachtwoord'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Uitloggen')

        resp = self.client.get('/account/logout/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('account/uitgelogd.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Uitloggen')


# end of file
