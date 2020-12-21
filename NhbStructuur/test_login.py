# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
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
        lid.email = ""      # belangrijk: leeg laten!
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_normaal
        lid.save()
        self.nhblid1 = lid

    def test_nhblid(self):
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/plein/')
        self.assertContains(resp, 'Sporter')

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
        self.assertNotContains(resp, 'Sporter')

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
        # nieuwe email in CRM
        # tijdens login word accountemail.nieuwe_email gezet
        # gebruiker mag niet inloggen totdat email bevestigd is
        self.nhblid1.email = 'nieuwe@test.com'
        self.nhblid1.save()

        obj = self.account_normaal.accountemail_set.all()[0]
        self.assertEqual(obj.nieuwe_email, '')
        self.assertTrue(obj.email_is_bevestigd)

        resp = self.e2e_login_no_check(self.account_normaal)
        self.assertEqual(resp.status_code, 200)
        # check niet ingelogd
        self.assertContains(resp, '/account/login/')
        self.assertNotContains(resp, '/account/logout/')
        self.assertContains(resp, 'We hebben een nieuw e-mailadres doorgekregen uit de administratie van de NHB')
        self.assertContains(resp, 'ni###e@test.com')

        # check propagatie is gedaan
        obj = self.account_normaal.accountemail_set.all()[0]
        self.assertEqual(obj.nieuwe_email, self.nhblid1.email)
        self.assertFalse(obj.email_is_bevestigd)

    def test_geen_nieuwe_email(self):
        # geen trigger als het e-mailadres niet gewijzigd is
        obj = self.account_normaal.accountemail_set.all()[0]
        self.assertTrue(obj.email_is_bevestigd)
        self.nhblid1.email = obj.bevestigde_email
        self.nhblid1.save()

        self.e2e_login(self.account_normaal)    # checkt login success

# end of file
