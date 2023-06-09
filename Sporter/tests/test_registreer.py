# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from Functie.models import Functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Sporter.models import Sporter
from Vereniging.models import Secretaris
import datetime


class TestSporterRegistreer(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie; module Registreer """

    test_after = ('Account',)

    url_tijdelijk = '/tijdelijke-codes/%s/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()
        self.nhbver = ver

        # maak de SEC functie aan
        functie = Functie(rol='SEC', nhb_ver=ver, beschrijving='SEC vereniging 1000')
        functie.save()

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100001 = sporter

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100002 = sporter

    def test_get(self):
        # test registratie via het formulier
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/registreer/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))

    def test_partial_fields(self):
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': ''})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Niet alle velden zijn ingevuld')

    def test_invalid_fields(self):
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100678',
                                     'email': 'is geen email',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'De gegevens worden niet geaccepteerd')

    def test_bad_lid_nr(self):
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': 'hallo!',
                                     'email': 'test@test.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Onbekend NHB nummer')

    def test_non_existing_nr(self):
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '999999',
                                     'email': 'test@test.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Onbekend NHB nummer')

    def test_geen_email(self):
        # vul de sec in
        sec = Secretaris(vereniging=self.nhbver)
        sec.save()
        sec.sporters.add(self.sporter_100001)

        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100002',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-geen-email.dtl', 'plein/site_layout.dtl'))

    def test_geen_email_geen_sec(self):
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100002',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-geen-email.dtl', 'plein/site_layout.dtl'))

    def test_geen_email_geen_ver(self):
        self.sporter_100002.bij_vereniging = None
        self.sporter_100002.save(update_fields=['bij_vereniging'])
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100002',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-geen-email.dtl', 'plein/site_layout.dtl'))

    def test_verkeerde_email(self):
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.yes',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    def test_registreer(self):
        # maak een andere sporter secretaris van de vereniging
        sec = Secretaris(vereniging=self.nhbver)
        sec.save()
        sec.sporters.add(self.sporter_100002)

        # doorloop de registratie
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rDeTester@gmail.not',    # dekt case-insensitive e-mailadres
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-aangemaakt.dtl', 'plein/site_layout.dtl'))

        # controleer dat het email adres obfuscated is
        self.assertNotContains(resp, 'rdetester@gmail.not')
        self.assertContains(resp, 'r@gmail.not')     # iets van r######r@gmail.not

        # controleer dat de volledige naam meteen al overgenomen is
        account = Account.objects.get(username='100001')
        self.assertEqual(account.volledige_naam(), 'Ramon de Tester')

        # verander de naam, om te testen dat de volledige naam later uit het Sporter overgenomen wordt
        account.first_name = '100001'
        account.last_name = ''
        account.save()
        self.assertEqual(account.volledige_naam(), '100001')

        sporter = Sporter.objects.get(lid_nr=self.sporter_100001.lid_nr)
        self.assertEqual(sporter.account, account)

        # volg de link om de email te bevestigen
        # (dit test een stukje functionaliteit aangeboden door Account)
        objs = TijdelijkeCode.objects.all().order_by('-aangemaakt_op')       # nieuwste eerst
        self.assertTrue(len(objs) > 0)
        obj = objs[0]
        self.assertEqual(obj.hoortbij_account.nieuwe_email, 'rdetester@gmail.not')
        self.assertFalse(obj.hoortbij_account.email_is_bevestigd)
        url = self.url_tijdelijk % obj.url_code
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/email-bevestigd.dtl', 'plein/site_layout.dtl'))

        account = Account.objects.get(username='100001')
        self.assertTrue(account.email_is_bevestigd)
        self.assertEqual(account.bevestigde_email, 'rdetester@gmail.not')

        # tijdens inlog wordt de volledige naam overgenomen
        self.e2e_login(account)
        account = Account.objects.get(username='100001')
        self.assertEqual(account.volledige_naam(), 'Ramon de Tester')

    def test_bestaat_al(self):
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-aangemaakt.dtl', 'plein/site_layout.dtl'))

        # tweede poging
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Account bestaat al')

    def test_zwak_wachtwoord(self):
        # te kort
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'te kort'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is te kort")

        # verboden reeks
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'handboogsport'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is niet sterk genoeg")

        # NHB nummer in wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'yoho100001jaha'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord bevat een verboden reeks")

        # keyboard walk 1
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'qwertyuiop'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is niet sterk genoeg")

        # keyboard walk 2
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'asdfghjkl'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is niet sterk genoeg")

        # keyboard walk 3
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'zxcvbnm,.'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is niet sterk genoeg")

        # keyboard walk 4
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': '1234567890!'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord is niet sterk genoeg")

        # te weinig verschillende tekens 1
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'xxxxxxxxx'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 2
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'jaJAjaJAjaJA'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 3
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'Jo!Jo!Jo!Jo!Jo!'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord bevat te veel gelijke tekens")

        # te weinig verschillende tekens 4
        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': 'helphelphelphelp'},
                                    follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "wachtwoord bevat te veel gelijke tekens")

    def test_inactief(self):
        self.sporter_100001.is_actief_lid = False
        self.sporter_100001.save()

        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': self.sporter_100001.email,
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Gebruik van NHB diensten is geblokkeerd. Neem contact op met de secretaris van je vereniging.')

    def test_sec(self):
        # lid dat zich registreert, is secretaris van een vereniging
        # en wordt meteen gekoppeld aan de SEC rol

        sec = Secretaris(vereniging=self.nhbver)
        sec.save()
        sec.sporters.add(self.sporter_100001)

        functie = Functie.objects.get(rol='SEC', nhb_ver=self.nhbver)
        self.assertEqual(functie.accounts.count(), 0)

        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': 'rdetester@gmail.not',
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-aangemaakt.dtl', 'plein/site_layout.dtl'))

        self.sporter_100001 = Sporter.objects.get(pk=self.sporter_100001.pk)   # refresh

        # sporter is nog niet gekoppeld aan de functie
        # dat wordt gedaan door de CRM import
        self.assertEqual(functie.accounts.count(), 0)

        # sporter is wel gekoppeld aan Secretaris
        self.assertEqual(sec.sporters.count(), 1)
        self.assertEqual(sec.sporters.all()[0], self.sporter_100001)

    def test_geen_ver(self):
        self.sporter_100001.bij_vereniging = None
        self.sporter_100001.save()

        with self.assert_max_queries(20):
            resp = self.client.post('/sporter/registreer/',
                                    {'nhb_nummer': '100001',
                                     'email': self.sporter_100001.email,
                                     'nieuw_wachtwoord': E2EHelpers.WACHTWOORD},
                                    follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/registreer-nhb-account.dtl', 'plein/site_layout.dtl'))
        self.assertFormError(resp.context['form'], None, 'Gebruik van NHB diensten is geblokkeerd. Neem contact op met de secretaris van je vereniging.')


# end of file
