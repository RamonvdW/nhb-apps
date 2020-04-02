# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from Functie.rol import rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle
from Functie.models import maak_functie
from Account.models import Account, AccountEmail, account_create, \
                    account_zet_sessionvars_na_login,\
                    account_zet_sessionvars_na_otp_controle,\
                    account_vhpg_is_geaccepteerd
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.helpers import extract_all_href_urls, assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from Overig.models import SiteTijdelijkeUrl
import datetime


class TestFunctieSelecteerSchutter(TestCase):
    """ unit tests voor de Functie applicatie, module SelecteerSchutter """

    def setUp(self):
        """ initialisatie van de test case """

        usermodel = get_user_model()
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        account_vhpg_is_geaccepteerd(self.account_admin)

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

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
        self.nhblid = lid

        account_create('normaal', 'wachtwoord', 'normaal@test.com', 'Normaal')
        self.account_normaal = Account.objects.get(username='normaal')
        self.account_normaal.nhblid = lid
        self.account_normaal.save()

    def test_zoek(self):
        # login als admin
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        # wordt IT beheerder
        resp = self.client.get('/functie/wissel-van-rol/beheerder/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirecet

        # check aanwezigheid Selecteer Schutter knop
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "IT beheerder")
        urls = [url for url in extract_all_href_urls(resp) if url.startswith('/functie/wissel-van-rol/')]
        self.assertIn('/functie/wissel-van-rol/selecteer-schutter/', urls)

        # haal de selecteer-schutter pagina op
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/selecteer-schutter.dtl', 'plein/site_layout.dtl'))

        # probeer de zoek functie
        resp = self.client.get(url + '?zoekterm=ramon')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/selecteer-schutter.dtl', 'plein/site_layout.dtl'))

        # controleer aanwezigheid van Selecteer knop, NHB nummer en Vereniging naam
        self.assertNotContains(resp, "Niets gevonden")
        self.assertContains(resp, self.nhblid.voornaam)
        self.assertContains(resp, self.nhblid.achternaam)
        self.assertContains(resp, self.nhblid.bij_vereniging.naam)
        self.assertContains(resp, "Selecteer")
        self.assertContains(resp, "do_selecteer")
        self.assertContains(resp, 'data-pk="%s"' % self.account_normaal.pk)

    def test_wissel(self):
        # login als admin
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        # wordt IT beheerder
        resp = self.client.get('/functie/wissel-van-rol/beheerder/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect

        # selecteer de andere schutter
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.post(url, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/selecteer-schutter-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in extract_all_href_urls(resp) if '/overig/url/' in url]
        # hak het https deel eraf
        url = urls[0][urls[0].find('/overig/url/'):]

        # volg de tijdelijke url om ingelogd te raken
        self.client.logout()
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-schutter.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Wissel van Rol')

        # controleer dat tijdelijke URL maar 1x gebruikt kan worden
        self.client.logout()
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_wissel_met_otp(self):
        # login als admin
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        # wordt IT beheerder
        resp = self.client.get('/functie/wissel-van-rol/beheerder/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect

        # activeer een rol + otp voor de schutter
        self.account_normaal.functies.add(self.functie_cwz)
        self.account_normaal.otp_is_actief = True
        self.account_normaal.save()
        account_vhpg_is_geaccepteerd(self.account_normaal)

        # selecteer de andere schutter
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.post(url, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/selecteer-schutter-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in extract_all_href_urls(resp) if '/overig/url/' in url]
        # hak het https deel eraf
        url = urls[0][urls[0].find('/overig/url/'):]

        # volg de tijdelijke url om ingelogd te raken
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-schutter.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wissel van rol')

        # controleer dat OTP controle niet nodig is
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        #print('resp: %s' % repr(resp.content).replace('>', '>\n'))
        self.assertContains(resp, 'Schutter')
        self.assertContains(resp, 'CWZ test')

    def test_wissel_bad(self):
        # login als admin
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        # wordt IT beheerder
        resp = self.client.get('/functie/wissel-van-rol/beheerder/')
        self.assertEqual(resp.status_code, 302)     # 302 = redirect

        # kleine tweak
        self.account_normaal.is_staff = True
        self.account_normaal.save()

        # upgrade naar is_staff account mag niet
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.post(url, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 404)     # 404 = not allowed

        # niet bestaand account
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.post(url, {'selecteer': 999999})
        self.assertEqual(resp.status_code, 404)     # 404 = not allowed

    def test_bad_get(self):
        # niet ingelogd
        self.client.logout()
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = not allowed

        # login als normaal
        account = self.account_normaal
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = not allowed

    def test_bad_post(self):
        # niet ingelogd
        self.client.logout()
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)     # 404 = not allowed

        # login als normaal
        account = self.account_normaal
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = not allowed

    def test_wissel_verlopen(self):
        # controleer dat tijdelijke URL na 60 seconden verlopen is

        # login als admin
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        # wordt IT beheerder
        resp = self.client.get('/functie/wissel-van-rol/beheerder/')
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect

        # wis het tijdelijke urls geheugen zodat we makkelijk het nieuwe record kunnen vinden
        SiteTijdelijkeUrl.objects.all().delete()

        # selecteer de andere schutter
        url = '/functie/wissel-van-rol/selecteer-schutter/'
        resp = self.client.post(url, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('functie/selecteer-schutter-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in extract_all_href_urls(resp) if '/overig/url/' in url]
        # hak het https deel eraf
        url = urls[0][urls[0].find('/overig/url/'):]

        obj = SiteTijdelijkeUrl.objects.all()[0]
        obj.geldig_tot = timezone.now() - datetime.timedelta(seconds=1)
        obj.save()

        # volg de tijdelijke url om ingelogd te raken
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed


# end of file
