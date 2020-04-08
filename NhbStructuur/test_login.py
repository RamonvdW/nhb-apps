# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account, AccountEmail
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
from Overig.models import SiteTijdelijkeUrl
import datetime


class TestNhbStructuurLogin(E2EHelpers, TestCase):
    """ unit tests voor de NhbStructuur applicatie; module Login plugin """

    test_after = ('Account',)

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

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
        lid.account = self.account_normaal
        lid.save()
        self.nhblid1 = lid

    def test_nhblid(self):
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/plein/')
        self.assertContains(resp, 'Schutter')

    def test_inactief(self):
        # probeer in te loggen als inactief lid
        self.nhblid1.is_actief_lid = False
        self.nhblid1.save()

        resp = self.e2e_login_no_check(self.account_normaal)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('nhbstructuur/is_inactief.dtl', 'plein/site_layout.dtl'))

    def test_geen_nhblid(self):
        self.nhblid1.account = None
        self.nhblid1.save()

        self.e2e_login(self.account_normaal)
        resp = self.client.get('/plein/')
        self.assertContains(resp, 'Gebruiker')
        self.assertNotContains(resp, 'Schutter')

    def test_overdracht_naam(self):
        # controleer dat de naam van het NHB lid door de login overgenomen wordt in het account
        self.assertNotEqual(self.account_normaal.first_name, self.nhblid1.voornaam)
        self.assertNotEqual(self.account_normaal.last_name, self.nhblid1.achternaam)
        self.e2e_login(self.account_normaal)
        self.account_normaal = Account.objects.get(username=self.account_normaal.username)
        self.assertEqual(self.account_normaal.first_name, self.nhblid1.voornaam)
        self.assertEqual(self.account_normaal.last_name, self.nhblid1.achternaam)

        # nogmaals inloggen voor coverage "naam is al gelijk"
        self.e2e_login(self.account_normaal)
        self.assertEqual(self.account_normaal.first_name, self.nhblid1.voornaam)
        self.assertEqual(self.account_normaal.last_name, self.nhblid1.achternaam)

    def test_geen_email(self):
        # corner case: account zonder accountemail
        self.account_normaal.accountemail_set.all()[0].delete()
        self.e2e_login(self.account_normaal)

    def test_nieuwe_email(self):
        # na login with accountemail.nieuwe_email gezet
        self.e2e_login(self.account_normaal)
        obj = self.account_normaal.accountemail_set.all()[0]
        self.assertEqual(obj.nieuwe_email, self.nhblid1.email)

        # dit gebeurt niet als het email als bevestigd is
        obj.bevestigde_email = self.nhblid1.email
        obj.nieuwe_email = ""
        obj.save()
        self.e2e_logout()
        self.e2e_login(self.account_normaal)
        self.assertEqual(obj.nieuwe_email, "")

# end of file
