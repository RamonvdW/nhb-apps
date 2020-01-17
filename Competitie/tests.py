# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.contrib.auth import get_user_model
from Account.models import Account, account_zet_sessionvars_na_otp_controle
from Account.rol import rol_zet_sessionvars_na_login
from Plein.tests import assert_html_ok, assert_template_used


class TestCompetitie(TestCase):
    """ unit tests voor de BasisTypen application """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BKO aan, nodig om de competitie defaults in te zien
        usermodel = get_user_model()
        usermodel.objects.create_user('bko', 'bko@test.com', 'wachtwoord')
        account = Account.objects.get(username='bko')
        account.is_BKO = True
        account.save()
        self.account_bko = account

    def test_competitie_defaults_anon(self):
        self.client.logout()
        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

    def test_competitie_defaults_bko(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_bko, self.client).save()
        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/competitie-defaults.dtl', 'plein/site_layout.dtl'))

# end of file

