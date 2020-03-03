# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from Account.models import Account, user_is_otp_verified, \
                           account_zet_sessionvars_na_login, account_zet_sessionvars_na_otp_controle


class TestBeheer(TestCase):
    """ unit tests voor de Beheer applicatie """

    def setUp(self):
        usermodel = get_user_model()
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        account = Account.objects.get(username='admin')
        account.otp_code = "1234567890123456"
        account.otp_is_actief = True
        account.save()
        self.account_admin = account

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
        # voordat 2FA verificatie gedaan is
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        self.assertFalse(user_is_otp_verified(self.client))

        # redirect naar wissel-van-rol pagina
        resp = self.client.get('/beheer/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/otp-controle/?next=/beheer/', 302))

        # na 2FA verificatie
        account_zet_sessionvars_na_otp_controle(self.client).save()
        resp = self.client.get('/beheer/', follow=True)
        self.assertTrue(len(resp.redirect_chain) == 0)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '<title>Websitebeheer | Django-websitebeheer</title>')

        # onnodig via beheer-login naar post-authenticatie pagina
        resp = self.client.get('/beheer/login/?next=/records/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/records/', 302))

        # onnodig via beheer-login zonder post-authenticatie pagina
        resp = self.client.get('/beheer/login/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/plein/', 302))
        #print("redirect_chain: %s" % repr(resp.redirect_chain))

    def test_logout(self):
        # controleer dat de admin login vervangen is door een redirect naar onze eigen login
        url = reverse('admin:logout')      # interne url
        self.assertEqual(url, '/beheer/logout/')

        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        resp = self.client.get('/beheer/logout/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/logout/', 302))

# end of file
