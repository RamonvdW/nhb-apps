# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
from django.utils import timezone
from .models import LogboekRegel, schrijf_in_logboek
from Account.models import Account, account_zet_sessionvars_na_login, account_zet_sessionvars_na_otp_controle
from Account.rol import rol_zet_sessionvars_na_login


class LogboekTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')

        self.account_normaal = Account.objects.get(username='normaal')
        self.account_admin = Account.objects.get(username='admin')

        schrijf_in_logboek(self.account_normaal, 'Logboek unittest', 'test setUp')

        schrijf_in_logboek(None, 'Logboek unittest', 'zonder account')

        self.logboek_url = '/overig/logboek/'

    def test_logboek_annon_redirect_login(self):
        # do een get van het logboek zonder ingelogd te zijn
        # resulteert in een redirect naar de login pagina
        self.client.logout()
        resp = self.client.get(self.logboek_url)
        self.assertRedirects(resp, '/account/login/?next=' + self.logboek_url)

    def test_logboek_str(self):
        # gebruik de str functie op de Logboek class
        log = LogboekRegel.objects.all()[0]
        msg = str(log)
        self.assertTrue("Logboek unittest" in msg and "normaal" in msg)

    def test_logboek_users_forbidden(self):
        # do een get van het logboek met een gebruiker die daar geen rechten toe heeft
        # resulteert rauwe Forbidden
        self.client.login(username='normaal', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()
        #sessionvars = rol_zet_sessionvars_na_login(self.account_normaal, self.client)
        #sessionvars.save()      # required for unittest only
        resp = self.client.get(self.logboek_url)
        self.assertEqual(resp.status_code, 403)  # 403 = Forbidden

    def test_logboek_user_allowed(self):
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        rsp = self.client.get(self.logboek_url)
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('logboek/logboek.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        self.assertContains(rsp, 'test setUp')
        self.assertContains(rsp, 'IT beheerder')
        assert_other_http_commands_not_supported(self, self.logboek_url)

# end of file
