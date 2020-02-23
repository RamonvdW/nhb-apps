# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from Account.models import Account, account_zet_sessionvars_na_login, account_zet_sessionvars_na_otp_controle


class TestBeheer(TestCase):
    """ unit tests voor de Beheer applicatie """

    def setUp(self):
        usermodel = get_user_model()
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')

    def test_login(self):
        # controleer dat de admin login vervangen is door een redirect naar onze eigen login
        url = reverse('admin:login')      # interne url
        self.assertEqual(url, '/beheer/login/')

        self.client.logout()
        resp = self.client.get('/beheer/login/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/login/', 302))

        resp = self.client.get('/beheer/login/?next=/records/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/login/?next=/records/', 302))

    def test_index(self):
        self.client.login(username='admin', password='wachtwoord')

        # voor 2FA verificatie
        account_zet_sessionvars_na_login(self.client).save()
        # since OTP verification is not done yet, it will still redirect to the login page
        resp = self.client.get('/beheer/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/login/?next=/beheer/', 302))

        # na 2FA verificatie
        account_zet_sessionvars_na_otp_controle(self.client).save()
        resp = self.client.get('/beheer/', follow=True)
        self.assertTrue(len(resp.redirect_chain) == 0)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '<title>Websitebeheer | Django-websitebeheer</title>')

    def test_logout(self):
        # controleer dat de admin login vervangen is door een redirect naar onze eigen login
        url = reverse('admin:logout')      # interne url
        self.assertEqual(url, '/beheer/logout/')

        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        resp = self.client.get('/beheer/logout/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/logout/', 302))

# end of file
