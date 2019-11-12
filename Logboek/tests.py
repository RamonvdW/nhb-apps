# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
from django.utils import timezone
from .models import LogboekRegel, schrijf_in_logboek
from Account.models import Account


class OverigTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')

        account = Account.objects.get(username='normaal')
        schrijf_in_logboek(account, 'Logboek unittest', 'test setUp')

        schrijf_in_logboek(None, 'Logboek unittest', 'zonder account')

    def test_logboek_annon(self):
        # do een get van alle feedback
        self.client.logout()
        rsp = self.client.get('/logboek/')
        self.assertRedirects(rsp, '/account/login/?next=/logboek/')

    def test_logboek_str(self):
        # gebruik de str functie op de Logboek class
        log = LogboekRegel.objects.all()[0]
        msg = str(log)
        self.assertTrue("Logboek unittest" in msg and "normaal" in msg)

    def test_logboek_user(self):
        self.client.login(username='normaal', password='wachtwoord')
        rsp = self.client.get('/logboek/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('logboek/logboek.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        self.assertContains(rsp, 'test setUp')
        self.assertContains(rsp, 'IT beheerder')
        assert_other_http_commands_not_supported(self, '/logboek/')

# end of file
