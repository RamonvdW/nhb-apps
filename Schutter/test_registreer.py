# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account, AccountEmail
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Overig.models import SiteTijdelijkeUrl
import datetime


class TestSchutterRegistreer(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie; module Registreer """

    test_after = ('Account',)

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
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
        lid.save()
        self.nhblid_100001 = lid

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

    def test_get(self):
        # test registratie via het formulier
        resp = self.client.get('/schutter/registreer/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))

    def test_partialfields(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Niet alle velden zijn ingevuld')

    def test_invalidfields(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100678',
                                 'email': 'is geen email',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De gegevens worden niet geaccepteerd')

    def test_bad_nhb_nr(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': 'hallo!',
                                 'email': 'test@test.not',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Onbekend NHB nummer')

    def test_nonexisting_nr(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '999999',
                                 'email': 'test@test.not',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Onbekend NHB nummer')

    def test_geen_email(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100002',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Geen email adres bekend. Neem contact op met de secretaris van je vereniging.')

    def test_verkeerde_email(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.yes',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    def test_registreer(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/aangemaakt.dtl', 'plein/site_layout.dtl'))

        # controleer dat het email adres obfuscated is
        self.assertNotContains(resp, 'rdetester@gmail.not')
        self.assertContains(resp, 'r@gmail.not')     # iets van r######r@gmail.not

        # controleer dat de volledige naam meteen al overgenomen is
        account = Account.objects.get(username='100001')
        self.assertEqual(account.volledige_naam(), 'Ramon de Tester')

        # verander de naam, om te testen dat de volledige naam later uit het NhbLid overgenomen wordt
        account.first_name = '100001'
        account.last_name = ''
        account.save()
        self.assertEqual(account.volledige_naam(), '100001')

        nhblid = NhbLid.objects.get(nhb_nr=self.nhblid_100001.nhb_nr)
        self.assertEqual(nhblid.account, account)

        # volg de link om de email te bevestigen
        # (dit test een stukje functionaliteit aangeboden door Account)
        objs = SiteTijdelijkeUrl.objects.all().order_by('-aangemaakt_op')       # nieuwste eerst
        self.assertTrue(len(objs) > 0)
        obj = objs[0]
        self.assertEqual(obj.hoortbij_accountemail.nieuwe_email, 'rdetester@gmail.not')
        self.assertFalse(obj.hoortbij_accountemail.email_is_bevestigd)
        url = '/overig/url/' + obj.url_code + '/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/bevestigd.dtl', 'plein/site_layout.dtl'))

        account = Account.objects.get(username='100001')
        email = AccountEmail.objects.get(account=account)
        self.assertTrue(email.email_is_bevestigd)
        self.assertEqual(account.get_email(), 'rdetester@gmail.not')

        # tijdens inlog wordt de volledige naam overgenomen
        self.e2e_login(account)
        account = Account.objects.get(username='100001')
        self.assertEqual(account.volledige_naam(), 'Ramon de Tester')

    def test_bestaat_al(self):
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/aangemaakt.dtl', 'plein/site_layout.dtl'))

        # tweede poging
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Account bestaat al')

    def test_zwak_wachtwoord(self):
        # te kort
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'te kort'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord moet minimaal 9 tekens lang zijn")

        # verboden reeks
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'handboogsport'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # NHB nummer in wachtwoord
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'yoho100001jaha'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat een verboden reeks")

        # keyboard walk 1
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'qwertyuiop'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # keyboard walk 2
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'asdfghjkl'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # keyboard walk 3
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'zxcvbnm,.'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # keyboard walk 4
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': '1234567890!'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # te weinig verschillende tekens 1
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'xxxxxxxxx'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 2
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'jaJAjaJAjaJA'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 3
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'Jo!Jo!Jo!Jo!Jo!'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 4
        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'helphelphelphelp'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

    def test_inactief(self):
        self.nhblid_100001.is_actief_lid = False
        self.nhblid_100001.save()

        resp = self.client.post('/schutter/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': self.nhblid_100001.email,
                                 'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Gebruik van NHB diensten is geblokkeerd. Neem contact op met de secretaris van je vereniging.')

# end of file
