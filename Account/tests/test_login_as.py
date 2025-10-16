# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from django.http import HttpResponseRedirect
from Account.middleware import SESSIONVAR_ACCOUNT_LOGIN_AS_DATE
from Account.plugin_manager import account_add_plugin_login_gate
from TijdelijkeCodes.models import TijdelijkeCode
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime
import time


class TestAccountLoginAs(E2EHelpers, TestCase):

    """ tests voor de Account applicatie, module Login-as """

    test_after = ('Account.tests.test_login.',)

    url_plein = '/plein/'
    url_wissel = '/account/account-wissel/'
    url_code_prefix = '/tijdelijke-codes/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def _login_plugin(self, request, from_ip, account):
        if self._login_plugin_mode == 1:
            return HttpResponseRedirect('/account/activiteit/')
        return None

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.mh', 'Normaal')

        self._login_plugin_mode = 0
        account_add_plugin_login_gate(10, self._login_plugin, False)

    def tearDown(self):
        self._login_plugin_mode = 0

    def test_zoek(self):
        # log een keer in als normaal om de voornaam/achternaam overgenomen te krijgen in het account_normaal
        self.e2e_login(self.account_normaal)
        self.e2e_logout()

        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # haal de account-wissel pagina op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-zoek.dtl', 'design/site_layout.dtl'))

        # probeer de zoek functie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel + '?zoekterm=normaal')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-zoek.dtl', 'design/site_layout.dtl'))

        # controleer aanwezigheid van Selecteer knop, bondsnummer en Vereniging naam
        self.assertNotContains(resp, "Niets gevonden")
        self.assertContains(resp, "normaal")
        self.assertContains(resp, "play_arrow")
        self.assertContains(resp, "do_selecteer")
        self.assertContains(resp, 'data-pk="%s"' % self.account_normaal.pk)

        # te lange zoekterm (max length = 50)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel + '?zoekterm=%s' % '1234567890' * 6)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

    def test_wissel_met_otp(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        self.assertTrue(self.account_normaal.otp_is_actief)

        # koppel de sporter aan een functie (anders wordt OTP niet overwogen)
        self.account_normaal.is_BB = True
        self.account_normaal.save(update_fields=['is_BB'])

        self.assertEqual(self._login_plugin_mode, 0)

        # deze test faalt als de datum verandert
        now = datetime.datetime.now()
        if now.hour == 23 and now.minute == 59 and now.second > 55:    # pragma: no cover
            print('Waiting until clock is past 23:59:59 .. ', end='')
            while now.second > 55:
                time.sleep(1)
                now = datetime.datetime.now()
            # while

        # selecteer de andere sporter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'design/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = self.extract_all_urls(resp, skip_external=False)
        urls = [url for url in urls if self.url_code_prefix in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find(self.url_code_prefix):]

        # volg de tijdelijke url om ingelogd te raken
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(tijdelijke_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(21):
            resp = self.client.post(post_url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Wissel van rol')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'design/site_layout.dtl'))

        # controleer dat de sporter uitgelogd wordt als de login-as datum verandert
        sessie = self.client.session
        sessie[SESSIONVAR_ACCOUNT_LOGIN_AS_DATE] = 'whatever'
        sessie.save()

        # bij uitzondering accepteren we de database operatie (op de sessie) tijdens een GET
        with self.assert_max_queries(20):
            with self.settings(DEBUG=True):
                # in de dev omgeving wordt de login-as-date niet geforceerd
                resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'design/site_layout.dtl'))

    def test_wissel_geen_otp(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        self.account_normaal.otp_is_actief = False
        self.account_normaal.save()

        # selecteer de andere schutter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'design/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = self.extract_all_urls(resp, skip_external=False)
        urls = [url for url in urls if self.url_code_prefix in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find(self.url_code_prefix):]

        # volg de tijdelijke url om ingelogd te raken
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(tijdelijke_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(30):
            resp = self.client.post(post_url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'design/site_layout.dtl'))
        self.assertNotContains(resp, 'Wissel van rol')

        # controleer dat tijdelijke URL maar 1x gebruikt kan worden
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assert_is_redirect(resp, '/plein/')

    def test_wissel_geblokkeerd(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # activeer de login-as blokkade
        self._login_plugin_mode = 1

        # selecteer de andere sporter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'design/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = self.extract_all_urls(resp, skip_external=False)
        urls = [url for url in urls if self.url_code_prefix in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find(self.url_code_prefix):]

        # volg de tijdelijke url om ingelogd te raken
        with self.assert_max_queries(20):
            resp = self.client.get(tijdelijke_url)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assert_is_redirect(resp, '/account/activiteit/')

    def test_wissel_bad(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # kleine tweak
        self.account_normaal.is_staff = True
        self.account_normaal.save()

        # upgrade naar is_staff account mag niet
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assert403(resp)

        # niet bestaand account
        resp = self.client.post(self.url_wissel, {'selecteer': 999999})
        self.assert404(resp, 'Account heeft geen e-mail')

    def test_bad_get(self):
        # niet ingelogd
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel)
        self.assert403(resp)

        # zonder is_staff rechten
        self.e2e_login_and_pass_otp(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel)
        self.assert403(resp)

    def test_bad_post(self):
        # niet ingelogd
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel)
        self.assert403(resp)

        # zonder is_staff rechten
        self.e2e_login_and_pass_otp(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel)
        self.assert403(resp)

    def test_wissel_verlopen(self):
        # controleer dat tijdelijke URL na 60 seconden verlopen is

        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # wis het tijdelijke urls geheugen zodat we makkelijk het nieuwe record kunnen vinden
        TijdelijkeCode.objects.all().delete()

        # selecteer de andere schutter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'design/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = self.extract_all_urls(resp, skip_external=False)
        urls = [url for url in urls if self.url_code_prefix in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find(self.url_code_prefix):]

        obj = TijdelijkeCode.objects.first()
        obj.geldig_tot = timezone.now() - datetime.timedelta(seconds=1)
        obj.save()

        # volg de tijdelijke url om ingelogd te raken
        with self.assert_max_queries(20):
            resp = self.client.get(tijdelijke_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('tijdelijkecodes/code-fout.dtl', 'design/site_layout.dtl'))

    def test_login_as_verloopt(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # een sessie variabele onthoudt op welke datum de login-as geldig is (maximaal 1 dag)
        # zet deze op op gisteren
        yesterday = timezone.now() - datetime.timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
        sessie = self.client.session
        sessie[SESSIONVAR_ACCOUNT_LOGIN_AS_DATE] = date_str
        sessie.save()

        resp = self.client.get(self.url_wissel)
        self.assert_is_redirect(resp, self.url_plein)   # na logout volgt redirect naar plein


# end of file
