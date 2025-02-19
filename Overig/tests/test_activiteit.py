# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Account.models import Account
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Mailer.models import MailQueue
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestOverigActiviteit(E2EHelpers, TestCase):

    """ tests voor de Overig applicatie; module Activiteit """

    test_after = ('Account.tests.test_login',)

    url_activiteit = '/overig/activiteit/'
    url_loskoppelen = '/overig/otp-loskoppelen/'
    url_bondspas = '/sporter/bondspas/toon/van-lid/%s/'     # lid nr

    testdata = None
    huidige_jaar = 2020

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_100001 = self.e2e_create_account('100001', 'lid100001@test.com', 'Norma de Schutter')
        self.account_100002 = self.e2e_create_account('100002', 'lid100002@test.com', 'Pijl de Schutter')

        account = self.account_100001
        account.otp_controle_gelukt_op = account.last_login = timezone.now() - datetime.timedelta(days=1)
        account.otp_controle_gelukt_op += datetime.timedelta(seconds=30)
        account.save(update_fields=['last_login', 'otp_controle_gelukt_op'])

        account = self.account_100002
        account.email_is_bevestigd = True
        account.save(update_fields=['email_is_bevestigd'])

        now = timezone.now()
        self.huidige_jaar = now.year

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        self.sporter_100001 = Sporter(lid_nr=100001,
                                      voornaam='Norma',
                                      achternaam='de Sporter',
                                      unaccented_naam='Norma de Sporter',  # hier wordt op gezocht
                                      account=self.account_100001,
                                      geboorte_datum='1980-01-08',
                                      sinds_datum='2008-01-08',
                                      lid_tot_einde_jaar=self.huidige_jaar,
                                      bij_vereniging=self.ver1)
        self.sporter_100001.save()

        # maak nog een sporter aan die niet gekoppeld is aan een account
        self.sporter_100002 = Sporter(lid_nr=100002,
                                      voornaam='Andere',
                                      achternaam='Sporter',
                                      unaccented_naam='Andere Sporter',
                                      account=self.account_100002,
                                      geboorte_datum='1980-01-09',
                                      lid_tot_einde_jaar=self.huidige_jaar,
                                      sinds_datum='2008-01-09')
        self.sporter_100002.save()

        # maak nog een sporter aan die in de toekomst pas lid wordt
        Sporter(
                lid_nr=100003,
                voornaam='Speciaal',
                achternaam='Toekomstig',
                unaccented_naam='Speciaal Toekomstig',
                geboorte_datum='1980-01-09',
                sinds_datum='2080-01-09',
                is_actief_lid=False).save()

        # sporter die geen gebruik meer mag maken van MH
        Sporter(
                lid_nr=100004,
                voornaam='Speciaal',
                achternaam='Verlopen',
                unaccented_naam='Speciaal Verlopen',
                geboorte_datum='1980-01-09',
                sinds_datum='2008-01-01',
                is_actief_lid=False).save()

        # gast-account
        Sporter(
                lid_nr=100005,
                voornaam='Speciaal',
                achternaam='Gast',
                unaccented_naam='Speciaal Gast',
                geboorte_datum='1980-01-09',
                sinds_datum='2008-01-01',
                is_gast=True).save()

    def test_anon(self):
        # geen inlog = geen toegang
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assert403(resp)

        resp = self.client.post(self.url_loskoppelen)
        self.assert403(resp)

    def test_normaal(self):
        # inlog maar geen rechten
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assert403(resp)

    def test_bb(self):
        # inlog met rechten
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_activiteit)

    def test_zoek(self):
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # te korte zoekterm
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': 'x'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # erg lange zoekterm
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': 'ramon' * 50})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoek op naam, 0 hits want geen sporter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': 'normaal'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoek op naam, 1 hit
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': 'norm'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoek op naam, 1 hit
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': 'norm'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoek op naam --> 2 hits
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': 'sporter'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # status: actief vanaf
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': '100003'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # status: verlopen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': '100004'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertIn(self.url_bondspas % '100004', urls)

        # gast-account (geen bondspas)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': '100005'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(self.url_bondspas % '100005', urls)

        # maak wat wijzigingen
        account = self.account_100001
        account.email_is_bevestigd = False
        account.save(update_fields=['email_is_bevestigd'])

        self.e2e_account_accepteert_vhpg(self.account_100001)

        account = self.account_100001 = Account.objects.get(pk=self.account_100001.pk)
        account.otp_is_actief = False
        account.last_login -= datetime.timedelta(days=720)
        account.save(update_fields=['otp_is_actief', 'last_login'])

        # zoek op bondsnummer  --> geen functies, dus geen 2FA nodig
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit, {'zoekterm': '100001'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # maak nog wat wijzigingen
        functie = maak_functie('Test functie', 'HWL')
        functie.accounts.add(self.account_100001)

        # zoek op bondsnummer --> wel functie, dus wel 2FA nodig
        with self.assert_max_queries(23):
            resp = self.client.get(self.url_activiteit, {'zoekterm': '100001'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        vhpg = self.account_100001.vhpg
        vhpg.acceptatie_datum -= datetime.timedelta(days=365)
        vhpg.save()

        # zoek op naam, 2 hits --> VHPG verlopen
        with self.assert_max_queries(25):
            resp = self.client.get(self.url_activiteit, {'zoekterm': 'sporter'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # maak nog wat wijzigingen
        vhpg.delete()

        # zoek op bondsnummer --> geen VHPG record
        with self.assert_max_queries(23):
            resp = self.client.get(self.url_activiteit, {'zoekterm': '100001'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

    def test_hulp(self):
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        functie = maak_functie('Test functie 1', 'HWL')
        functie.accounts.add(self.account_100001)

        functie = maak_functie('Test functie 2', 'WL')
        functie.accounts.add(self.account_100001)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        self.account_100001.otp_is_actief = False
        self.account_100001.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

        # maak dat het account geen hulp nodig heeft: 2FA gekoppeld en VHPG geaccepteerd
        self.account_100001.otp_is_actief = True
        self.account_100001.save()

        self.e2e_account_accepteert_vhpg(self.account_100001)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

    def test_alle_rollen(self):
        # controleer dat de rollen van alle mogelijke functies weergegeven kunnen worden
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        functie = maak_functie('Test functie 1', 'MO')
        functie.accounts.add(self.account_100001)

        functie = maak_functie('Test functie 2', 'BKO')
        functie.accounts.add(self.account_100001)

        functie = maak_functie('Test functie 3', 'RKO')
        functie.accounts.add(self.account_100001)

        functie = maak_functie('Test functie 4', 'RCL')
        functie.accounts.add(self.account_100001)

        functie = maak_functie('Test functie 5', 'SEC')
        functie.accounts.add(self.account_100001)

        functie = maak_functie('Test functie 6', 'HWL')
        functie.accounts.add(self.account_100001)

        functie = maak_functie('Test functie 7', 'WL')
        functie.accounts.add(self.account_100001)

        # maak dat het account hulp nodig heeft en dus in de lijst komt te staan
        self.account_100001.otp_is_actief = False
        self.account_100001.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('overig/activiteit.dtl', 'plein/site_layout.dtl'))

    def test_loskoppelen(self):
        self.account_normaal.otp_is_actief = True
        self.account_normaal.otp_code = "ABCDEFGHIJKLMNOP"       # noqa
        self.account_normaal.save()

        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_logout()

        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        # loskoppelen via POST

        # bad input: geen parameters
        resp = self.client.post(self.url_loskoppelen, {})
        self.assert_is_redirect(resp, '/overig/activiteit/')

        # bad input: geen login parameter
        resp = self.client.post(self.url_loskoppelen, {'reset_tweede_factor': 1})
        self.assert404(resp, 'Niet gevonden')

        # bad input: niet bestaande login naam
        resp = self.client.post(self.url_loskoppelen, {'reset_tweede_factor': 1,
                                                       'inlog_naam': 'Jantje'})
        self.assert404(resp, 'Niet gevonden')

        # bad input: rare tekens in login naam
        resp = self.client.post(self.url_loskoppelen, {'reset_tweede_factor': 1,
                                                       'inlog_naam': '###'})
        self.assert404(resp, 'Niet gevonden')

        # bad input: geen login naam
        resp = self.client.post(self.url_loskoppelen, {'reset_tweede_factor': 1,
                                                       'inlog_naam': ''})
        self.assert404(resp, 'Niet gevonden')

        # echt loskoppelen
        resp = self.client.post(self.url_loskoppelen, {'reset_tweede_factor': 1,
                                                       'inlog_naam': self.account_normaal.username})
        self.assert_is_redirect(resp, '/overig/activiteit/?zoekterm=%s' % self.account_normaal.username)

        # controleer losgekoppeld
        account = Account.objects.get(username=self.account_normaal.username)
        self.assertFalse(account.otp_is_actief)

        # er moet nu een mail in de MailQueue staan met een single-use url
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_account/otp-is-losgekoppeld.dtl')
        self.assert_consistent_email_html_text(mail)

        # Account middleware forceert nieuwe OTP en reset de rol
        # dus nieuwe post is niet meer mogelijk

        # al losgekoppeld
        resp = self.client.post(self.url_loskoppelen, {'reset_tweede_factor': 1,
                                                       'inlog_naam': self.account_normaal.username})
        self.assert_is_redirect(resp, '/overig/activiteit/?zoekterm=%s' % self.account_normaal.username)

# end of file
