# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from django.conf import settings
from .models import Account, AccountEmail,account_is_email_valide
from .views import obfuscate_email
from .forms import LoginForm
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestAccountAanmaken(E2EHelpers, TestCase):
    """ unit tests voor de Account applicatie; module Aanmaken/Email bevestigen """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_metmail = self.e2e_create_account('metmail', 'metmail@test.com', 'MetMail')

        self.email_normaal = self.account_normaal.accountemail_set.all()[0]
        self.email_metmail = self.account_metmail.accountemail_set.all()[0]

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid1 = lid

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

    def test_aangemaakt_direct(self):
        # test rechtstreeks de 'aangemaakt' pagina ophalen, zonder registratie stappen
        # hierbij ontbreekt er een sessie variabele --> exceptie en redirect naar het plein
        resp = self.client.get('/account/aangemaakt/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect
        self.assertEqual(resp.url, '/plein/')

    def test_email_bevestigd(self):
        # haal de bevestigd view direct op

        # uitgelogd --> login knop moet aanwezig zijn
        self.e2e_logout()
        resp = self.client.get('/account/bevestigd/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('account/bevestigd.dtl', 'plein/site_layout.dtl'))
        self.assertTrue('show_login' in resp.context)

        # al ingelogd
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/account/bevestigd/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('account/bevestigd.dtl', 'plein/site_layout.dtl'))
        self.assertFalse('show_login' in resp.context)

        self.e2e_assert_other_http_commands_not_supported('/account/bevestigd/')

# TODO: gebruik assert_other_http_commands_not_supported

# end of file
