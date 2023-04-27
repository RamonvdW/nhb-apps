# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestSporterLogin(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie; module Login plugin """

    test_after = ('Account',)

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = ""      # belangrijk: leeg laten!
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_normaal
        sporter.save()
        self.sporter_100001 = sporter

    def test_normaal(self):
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get('/plein/')
        self.assert_template_used(resp, ('plein/plein-sporter.dtl',))

    def test_inactief_normaal(self):
        # probeer in te loggen als inactief lid
        self.sporter_100001.is_actief_lid = False
        self.sporter_100001.save()

        resp = self.e2e_login_no_check(self.account_normaal)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/is_inactief.dtl', 'plein/site_layout.dtl'))

    def test_inactief_bb(self):
        # inlog als BB met inactief nhblid moet gewoon werken
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.sporter_100001.is_actief_lid = False
        self.sporter_100001.save()
        self.e2e_login(self.account_normaal)

    def test_inactief_staff(self):
        # inlog als staff met inactief nhblid moet gewoon werken
        self.account_normaal.is_staff = True
        self.account_normaal.save()
        self.sporter_100001.is_actief_lid = False
        self.sporter_100001.save()
        self.e2e_login(self.account_normaal)

    def test_geen_nhblid(self):
        self.sporter_100001.account = None
        self.sporter_100001.save()

        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get('/plein/')
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl',))

    def test_overdracht_naam(self):
        # controleer dat de naam van het NHB lid door de login overgenomen wordt in het account
        self.assertNotEqual(self.account_normaal.first_name, self.sporter_100001.voornaam)
        self.assertNotEqual(self.account_normaal.last_name, self.sporter_100001.achternaam)
        self.e2e_login(self.account_normaal)
        self.account_normaal = Account.objects.get(username=self.account_normaal.username)
        self.assertEqual(self.account_normaal.first_name, self.sporter_100001.voornaam)
        self.assertEqual(self.account_normaal.last_name, self.sporter_100001.achternaam)

        # nogmaals inloggen voor coverage "naam is al gelijk"
        self.e2e_login(self.account_normaal)
        self.assertEqual(self.account_normaal.first_name, self.sporter_100001.voornaam)
        self.assertEqual(self.account_normaal.last_name, self.sporter_100001.achternaam)

    def test_nieuwe_email(self):
        # nieuwe email in CRM
        # tijdens login word accountemail.nieuwe_email gezet
        # gebruiker mag niet inloggen totdat email bevestigd is
        self.sporter_100001.email = 'nieuwe@test.com'
        self.sporter_100001.save()

        account = self.account_normaal
        self.assertEqual(account.nieuwe_email, '')
        self.assertTrue(account.email_is_bevestigd)

        resp = self.e2e_login_no_check(account, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'We hebben een nieuw e-mailadres doorgekregen uit de administratie van de NHB')
        self.assertContains(resp, 'ni###e@test.com')

        # check niet ingelogd
        self.e2e_assert_not_logged_in()

        # check propagatie is gedaan
        account = Account.objects.get(pk=account.pk)
        self.assertEqual(account.nieuwe_email, self.sporter_100001.email)
        self.assertFalse(account.email_is_bevestigd)

    def test_geen_nieuwe_email(self):
        # geen trigger als het e-mailadres niet gewijzigd is
        account = self.account_normaal
        self.assertTrue(account.email_is_bevestigd)
        self.sporter_100001.email = account.bevestigde_email
        self.sporter_100001.save(update_fields=['email'])

        self.e2e_login(self.account_normaal)    # checkt login success

# end of file
