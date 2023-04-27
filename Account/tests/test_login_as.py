# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from django.http import HttpResponseRedirect
from Overig.models import SiteTijdelijkeUrl
from Account.plugins import account_add_plugin_login
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestAccountLoginAs(E2EHelpers, TestCase):

    """ tests voor de Account applicatie, module Login-as """

    test_after = ('Account.tests.test_login.',)

    url_wissel = '/account/account-wissel/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts()

    def _login_plugin(self, request, from_ip, account):
        if self._login_plugin_mode == 1:
            return HttpResponseRedirect('/account/activiteit/')
        return None

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')

        self._login_plugin_mode = 0
        account_add_plugin_login(10, self._login_plugin, False)

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
        self.assert_template_used(resp, ('account/login-as-zoek.dtl', 'plein/site_layout.dtl'))

        # probeer de zoek functie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel + '?zoekterm=normaal')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-zoek.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van Selecteer knop, NHB nummer en Vereniging naam
        self.assertNotContains(resp, "Niets gevonden")
        self.assertContains(resp, "normaal")
        self.assertContains(resp, "play_arrow")
        self.assertContains(resp, "do_selecteer")
        self.assertContains(resp, 'data-pk="%s"' % self.account_normaal.pk)

        # te lange zoekterm (max length = 50)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel + '?zoekterm=%s' % '1234567890' * 6)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

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
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in self.extract_all_urls(resp) if '/overig/url/' in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find('/overig/url/'):]

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
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Wissel van Rol')

        # controleer dat tijdelijke URL maar 1x gebruikt kan worden
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assert_is_redirect(resp, '/plein/')

    def test_wissel_met_otp(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # activeer een rol + vhpg voor de schutter
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.e2e_assert_other_http_commands_not_supported(self.url_wissel, post=False)

        # selecteer de andere schutter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in self.extract_all_urls(resp) if '/overig/url/' in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find('/overig/url/'):]

        # volg de tijdelijke url om ingelogd te raken
        with self.assert_max_queries(20):
            resp = self.client.get(tijdelijke_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(34):
            resp = self.client.post(post_url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wissel van rol')

        # controleer dat OTP controle niet nodig is
        # FUTURE: ongewenste dependency op Functie --> verplaats deze check naar Functie
        with self.assert_max_queries(23):
            resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Manager Competitiezaken')

    def test_wissel_geblokkeerd(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        # activeer de login-as blokkade
        self._login_plugin_mode = 1

        # selecteer de andere schutter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in self.extract_all_urls(resp) if '/overig/url/' in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find('/overig/url/'):]

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
        with self.assert_max_queries(20):
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
        SiteTijdelijkeUrl.objects.all().delete()

        # selecteer de andere schutter
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in self.extract_all_urls(resp) if '/overig/url/' in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find('/overig/url/'):]

        obj = SiteTijdelijkeUrl.objects.all()[0]
        obj.geldig_tot = timezone.now() - datetime.timedelta(seconds=1)
        obj.save()

        # volg de tijdelijke url om ingelogd te raken
        with self.assert_max_queries(20):
            resp = self.client.get(tijdelijke_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('overig/tijdelijke-url-fout.dtl', 'plein/site_layout.dtl'))

# end of file
