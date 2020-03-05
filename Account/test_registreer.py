# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Account, AccountEmail
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from Overig.models import SiteTijdelijkeUrl
import datetime


CORRECT_WACHTWOORD = "qewretrytuyi"


class TestAccountRegistreer(TestCase):
    """ unit tests voor de Account applicatie; module Registreer """

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

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

    def test_registreer_get(self):
        # test registratie via het formulier
        resp = self.client.get('/account/registreer/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))

    def test_registreer_partialfields(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Niet alle velden zijn ingevuld')

    def test_registreer_invalidfields(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100678',
                                 'email': 'is geen email',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De gegevens worden niet geaccepteerd')

    def test_registreer_nhb_bad_nr(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': 'hallo!',
                                 'email': 'test@test.not',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Onbekend NHB nummer')

    def test_registreer_nhb_nonexisting_nr(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '999999',
                                 'email': 'test@test.not',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Onbekend NHB nummer')

    def test_registreer_nhb_geen_email(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100002',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Geen email adres bekend. Neem contact op met de secretaris van je vereniging.')

    def test_registreer_nhb_verkeerde_email(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.yes',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    def test_registreer_nhb(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/aangemaakt.dtl', 'plein/site_layout.dtl'))

        # controleer dat het email adres obfuscated is
        self.assertNotContains(resp, 'rdetester@gmail.not')
        self.assertContains(resp, 'r@gmail.not')     # iets van r######r@gmail.not

        # volg de link om de email te bevestigen
        objs = SiteTijdelijkeUrl.objects.all().order_by('-aangemaakt_op')       # nieuwste eerst
        self.assertTrue(len(objs) > 0)
        obj = objs[0]
        self.assertEqual(obj.hoortbij_accountemail.nieuwe_email, 'rdetester@gmail.not')
        self.assertFalse(obj.hoortbij_accountemail.email_is_bevestigd)
        url = '/overig/url/' + obj.url_code + '/'
        resp = self.client.get(url, follow=True)    # temporary url redirects
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/bevestigd.dtl', 'plein/site_layout.dtl'))

        account = Account.objects.filter(username='100001')[0]
        accmail = AccountEmail.objects.filter(account=account)[0]
        self.assertTrue(accmail.email_is_bevestigd)

        self.assertEqual(account.get_email(), 'rdetester@gmail.not')
        self.assertEqual(account.get_real_name(), 'Ramon de Tester')

    def test_registreer_nhb_bestaat_al(self):
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/aangemaakt.dtl', 'plein/site_layout.dtl'))

        # tweede poging
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': CORRECT_WACHTWOORD},
                                follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp, 'form', None, 'Account bestaat al')

    def test_registreer_zwak_wachtwoord(self):
        # te kort
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'te kort'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord moet minimaal 9 tekens lang zijn")

        # verboden reeks
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'handboogsport'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # NHB nummer in wachtwoord
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'yoho100001jaha'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat een verboden reeks")

        # keyboard walk 1
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'qwertyuiop'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # keyboard walk 2
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'asdfghjkl'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # keyboard walk 3
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'zxcvbnm,.'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # keyboard walk 4
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': '1234567890!'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord is niet sterk genoeg")

        # te weinig verschillende tekens 1
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'xxxxxxxxx'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 2
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'jaJAjaJAjaJA'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 3
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'Jo!Jo!Jo!Jo!Jo!'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 4
        resp = self.client.post('/account/registreer/',
                                {'nhb_nummer': '100001',
                                 'email': 'rdetester@gmail.not',
                                 'nieuw_wachtwoord': 'helphelphelphelp'},
                                follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/registreer.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wachtwoord bevat te veel gelijke tekens")

    def test_direct_aangemaakt(self):
        # test rechtstreeks de 'aangemaakt' pagina ophalen, zonder registratie stappen
        resp = self.client.get('/account/aangemaakt/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect
        self.assertEqual(resp.url, '/plein/')

    def test_email_bevestigd(self):
        # haal de bevestigd view direct op

        # uitgelogged --> login knop moet aanwezig zijn
        self.client.logout()
        resp = self.client.get('/account/bevestigd/')
        self.assertTrue('show_login' in resp.context)

        # al ingelogged
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        resp = self.client.get('/account/bevestigd/')
        self.assertFalse('show_login' in resp.context)

        assert_other_http_commands_not_supported(self, '/account/bevestigd/')

# end of file
