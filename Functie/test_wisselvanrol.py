# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Functie.rol import rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle
from Functie.models import maak_functie
from Account.models import Account,\
                    account_zet_sessionvars_na_login,\
                    account_zet_sessionvars_na_otp_controle,\
                    account_vhpg_is_geaccepteerd
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
import datetime


class TestFunctieWisselVanRol(TestCase):
    """ unit tests voor de Functie applicatie, module Wissel van Rol """

    def setUp(self):

        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        self.functie_rcl = maak_functie("RCL test", "RCL")
        self.functie_rcl.nhb_regio = regio_111
        self.functie_rcl.save()

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

        # maak een test vereniging zonder CWZ rol
        ver2 = NhbVereniging()
        ver2.naam = "Grote Club"
        ver2.nhb_nr = "1001"
        ver2.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver2.save()

    def test_admin(self):
        # controleer dat de link naar het wisselen van rol op de pagina staat
        self.account_admin.otp_is_actief = False
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, 'IT beheerder')
        self.assertNotContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Controle met een tweede factor is verplicht voor gebruikers met toegang tot persoonsgegevens')

        self.client.logout()

        # controleer dat de link naar de OTP controle en VHPG op de pagina staan
        self.account_admin.otp_is_actief = True
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, 'IT beheerder')
        self.assertNotContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Voordat je aan de slag kan moeten we eerst een paar afspraken maken over het omgaan met persoonsgegevens.')
        self.assertContains(resp, 'Een aantal rollen komt beschikbaar nadat de controle van de tweede factor uitgevoerd is.')

        # controleer dat de complete keuzemogelijkheden op de pagina staan
        account_vhpg_is_geaccepteerd(self.account_admin)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertContains(resp, 'IT beheerder')
        self.assertContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')

        assert_template_used(self, resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        assert_other_http_commands_not_supported(self, '/functie/wissel-van-rol/')
        self.client.logout()

    def test_normaal(self):
        self.account_normaal.nhblid = self.nhblid1
        self.account_normaal.save()
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()

        # controleer dat de wissel-van-rol pagina niet aanwezig is voor deze normale gebruiker
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to plein)
        self.client.logout()

    def test_normaal_met_rol(self):
        # voeg de gebruiker toe aan een groep waardoor wissel-van-rol actief wordt
        self.account_normaal.nhblid = self.nhblid1
        self.account_normaal.save()
        self.account_normaal.functies.add(self.functie_rcl)
        account_vhpg_is_geaccepteerd(self.account_normaal)

        self.client.logout()
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_normaal, self.client).save()

        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, "BKO test")
        self.assertNotContains(resp, "RKO test")
        self.assertContains(resp, "RCL test")
        self.assertNotContains(resp, "CWZ test")

        # activeer nu de rol van RCL
        # dan komen de CWZ rollen te voorschijn
        resp = self.client.get('/functie/wissel-van-rol/functie/%s/' % self.functie_rcl.pk)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect

        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, "BKO test")
        self.assertNotContains(resp, "RKO test")
        self.assertContains(resp, "RCL test")
        self.assertContains(resp, "CWZ test")

        assert_other_http_commands_not_supported(self, '/functie/wissel-van-rol/')

    def test_rolwissel(self):
        self.client.login(username=self.account_admin.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(self.account_admin)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()

        resp = self.client.get('/functie/wissel-van-rol/BB/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Manager competitiezaken")

        resp = self.client.get('/functie/wissel-van-rol/beheerder/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        # controleer dat een niet valide rol wissel geen effect heeft
        # dit raakt een exception in Account.rol:rol_activeer
        resp = self.client.get('/functie/wissel-van-rol/huh/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        # controleer dat een rol wissel die met een functie moet geen effect heeft
        resp = self.client.get('/functie/wissel-van-rol/BKO/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        resp = self.client.get('/functie/wissel-van-rol/geen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Gebruiker")

        self.client.logout()

    def test_geen_rolwissel(self):
        # dit raakt de exceptie in Account.rol:rol_mag_wisselen
        self.client.logout()
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

        # probeer van rol te wisselen
        resp = self.client.get('/functie/wissel-van-rol/beheerder/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)


# end of file
