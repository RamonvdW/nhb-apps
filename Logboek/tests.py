# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
from django.utils import timezone
from .models import LogboekRegel, schrijf_in_logboek
from Account.models import Account, account_vhpg_is_geaccepteerd, account_zet_sessionvars_na_otp_controle
from Account.rol import rol_zet_sessionvars_na_otp_controle, rol_activeer_rol, rol_activeer_functie, rol_is_beheerder


class TestLogboek(TestCase):
    """ unit tests voor de Logboek applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')

        self.account_normaal = Account.objects.get(username='normaal')
        self.account_admin = Account.objects.get(username='admin')
        account_vhpg_is_geaccepteerd(self.account_admin)

        schrijf_in_logboek(self.account_normaal, 'Logboek unittest', 'test setUp')
        schrijf_in_logboek(None, 'Logboek unittest', 'zonder account')
        schrijf_in_logboek(None, 'Records', 'import gelukt')
        schrijf_in_logboek(None, 'Rollen', 'Jantje is de baas')
        schrijf_in_logboek(None, 'NhbStructuur', 'weer een nieuw lid')
        schrijf_in_logboek(self.account_normaal, 'OTP controle', 'alweer verkeerd')

        self.logboek_url = '/logboek/'

    def test_logboek_annon(self):
        # do een get van het logboek zonder ingelogd te zijn
        # resulteert in een redirect naar het plein
        self.client.logout()
        resp = self.client.get(self.logboek_url)
        self.assertRedirects(resp, '/plein/')

    def test_logboek_str(self):
        # gebruik de str functie op de Logboek class
        log = LogboekRegel.objects.all()[0]
        msg = str(log)
        self.assertTrue("Logboek unittest" in msg and "normaal" in msg)

    def test_logboek_users_forbidden(self):
        # do een get van het logboek met een gebruiker die daar geen rechten toe heeft
        # resulteert rauwe Forbidden
        self.client.login(username='normaal', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_normaal, self.client).save()
        #sessionvars = rol_zet_sessionvars_na_login(self.account_normaal, self.client)
        #sessionvars.save()      # required for unittest only
        resp = self.client.get(self.logboek_url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect (naar het plein)

    def test_logboek_user_allowed(self):
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()
        self.assertTrue(self.account_admin.is_staff)
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_beheerder(self.client))

        # alles
        resp = self.client.get(self.logboek_url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        assert_template_used(self, resp, ('logboek/logboek.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        self.assertContains(resp, 'test setUp')
        self.assertContains(resp, 'IT beheerder')
        assert_other_http_commands_not_supported(self, self.logboek_url)

        # records import
        resp = self.client.get(self.logboek_url + 'records/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        assert_template_used(self, resp, ('logboek/logboek-records.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        self.assertContains(resp, 'import gelukt')

        # accounts
        resp = self.client.get(self.logboek_url + 'accounts/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        assert_template_used(self, resp, ('logboek/logboek-accounts.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        self.assertContains(resp, 'alweer verkeerd')

        # rollen
        resp = self.client.get(self.logboek_url + 'rollen/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        assert_template_used(self, resp, ('logboek/logboek-rollen.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        self.assertContains(resp, 'Jantje is de baas')

        # nhbstructuur / crm import
        resp = self.client.get(self.logboek_url + 'crm-import/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        assert_template_used(self, resp, ('logboek/logboek-nhbstructuur.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, resp)
        self.assertContains(resp, 'weer een nieuw lid')

# end of file
