# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from .rol import Rollen, rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle,\
                         rol_mag_wisselen, rol_is_beheerder, rol_zet_plugins, \
                         rol_get_huidige, rol_activeer_rol, rol_activeer_functie, \
                         rol_get_beschrijving, rol_enum_pallet, \
                         rol_is_BB, rol_is_BKO, rol_is_RKO, rol_is_CWZ
from .models import Account,\
                    account_zet_sessionvars_na_login,\
                    account_zet_sessionvars_na_otp_controle,\
                    account_vhpg_is_geaccepteerd
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.tests import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
import datetime
from types import SimpleNamespace


class TestAccountRol(TestCase):
    """ unit tests voor de Account applicatie """

    def _rol_expansie(self, rol_in, group_in):
        #print("_rol_expansie: expansie_functie=%s, rol_in=%s, group_in=%s" % (self._expansie_functie, repr(rol_in), repr(group_in)))
        if self._expansie_functie >= 1:
            if rol_in == Rollen.ROL_BB:
                yield (Rollen.ROL_BKO, self.group_bko.pk)

        if self._expansie_functie >= 2:
            if rol_in == Rollen.ROL_BKO:
                yield (Rollen.ROL_RKO, self.group_rko.pk)
                yield (Rollen.ROL_RKO, self.group_rko.pk)       # trigger dupe filter


    def setUp(self):
        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

        self.group_bko, _ = Group.objects.get_or_create(name="BKO test voor de DIT VALT WEG")
        self.group_rko, _ = Group.objects.get_or_create(name="RKO test")
        self.group_rcl, _ = Group.objects.get_or_create(name="RCL test")
        self.group_cwz, _ = Group.objects.get_or_create(name="CWZ test")
        self.group_tst, _ = Group.objects.get_or_create(name="Test test")

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

        self._expansie_functie = 0
        rol_zet_plugins(self._rol_expansie)

    def test_rol(self):
        # unit-tests voor de 'rol' module

        # simuleer de normale inputs
        account = self.account_normaal
        request = SimpleNamespace()
        request.session = dict()
        request.user = account

        # no session vars / not logged in
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertFalse(rol_mag_wisselen(request))
        rol_activeer_rol(request, 'bestaat niet')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertFalse(rol_is_beheerder(request))

        # niet aan nhblid gekoppeld schutter account
        account.is_staff = False
        account.is_BB = False
        account.nhblid = None
        request.session = dict()
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertFalse(rol_is_beheerder(request))
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)

        # schutter
        account.is_staff = False
        account.is_BB = False
        account.nhblid = self.nhblid1
        request.session = dict()
        account_zet_sessionvars_na_login(request)
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        self.assertFalse(rol_is_beheerder(request))
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'BKO')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)

        # bb
        account.is_staff = False
        account.is_BB = True
        account.nhblid = self.nhblid1
        request.session = dict()
        account_zet_sessionvars_na_otp_controle(request)
        rol_zet_sessionvars_na_otp_controle(account, request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        self.assertTrue(rol_mag_wisselen(request))
        self.assertFalse(rol_is_beheerder(request))        # ivm VHPG niet geaccepteerd

        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(request)
        rol_zet_sessionvars_na_otp_controle(account, request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        self.assertFalse(rol_is_beheerder(request))

        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'BB')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        self.assertTrue(rol_is_beheerder(request))
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'BB')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        rol_activeer_rol(request, 'BKO')        # kan niet, moet via functie
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)

        # beheerder
        account = self.account_admin
        request.session = dict()
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(request)
        rol_zet_sessionvars_na_otp_controle(account, request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        self.assertTrue(rol_mag_wisselen(request))

        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)
        rol_activeer_rol(request, 'BB')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
        rol_activeer_rol(request, 'geen')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)
        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_IT)

    def test_wisselvanrol_pagina_admin(self):
        # controleer dat de link naar het wisselen van rol op de pagina staat
        self.account_admin.otp_is_actief = False
        self.account_admin.save()
        self.client.login(username='admin', password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_admin, self.client).save()
        resp = self.client.get('/account/wissel-van-rol/')
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
        resp = self.client.get('/account/wissel-van-rol/')
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
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertContains(resp, 'IT beheerder')
        self.assertContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')

        assert_template_used(self, resp, ('account/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        assert_other_http_commands_not_supported(self, '/account/wissel-van-rol/')
        self.client.logout()

    def test_wisselvanrol_pagina_normaal(self):
        self.account_normaal.nhblid = self.nhblid1
        self.account_normaal.save()
        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(self.account_normaal, self.client).save()

        # controleer dat de wissel-van-rol pagina niet aanwezig is voor deze normale gebruiker
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 403)     # 403 = Forbidden
        self.client.logout()

    def test_wisselvanrol_pagina_normaal_met_rol(self):
        # voeg de gebruiker toe aan een groep waardoor wissel-van-rol actief wordt
        self.account_normaal.nhblid = self.nhblid1
        self.account_normaal.save()
        self.account_normaal.groups.add(self.group_rcl)
        account_vhpg_is_geaccepteerd(self.account_normaal)

        self.client.login(username=self.account_normaal.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_normaal, self.client).save()

        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        self.assertNotContains(resp, "BKO")
        self.assertNotContains(resp, "RKO")
        self.assertContains(resp, "RCL")     # TODO: RKO moet RCL kunnen helpen
        self.assertNotContains(resp, "CWZ")

    def test_rolwissel(self):
        self.client.login(username=self.account_admin.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(self.account_admin)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_admin, self.client).save()

        resp = self.client.get('/account/wissel-van-rol/BB/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Manager competitiezaken")

        resp = self.client.get('/account/wissel-van-rol/beheerder/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        # controleer dat een niet valide rol wissel geen effect heeft
        # dit raakt een exception in Account.rol:rol_activeer
        resp = self.client.get('/account/wissel-van-rol/huh/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        # controleer dat een rol wissel die met een functie moet geen effect heeft
        resp = self.client.get('/account/wissel-van-rol/BKO/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: IT beheerder")

        resp = self.client.get('/account/wissel-van-rol/geen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Rol: Gebruiker")

        self.client.logout()

    def test_rol_functie_bko(self):
        account = self.account_admin
        account.groups.add(self.group_bko)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertFalse(rol_is_BKO(self.client))
        rol_activeer_functie(self.client, self.group_bko.pk).save()
        self.assertTrue(rol_is_BKO(self.client))

        # check dat "voor de DIT VALT WEG" weggehaald is
        self.assertTrue(rol_get_beschrijving(self.client), "BKO test")

    def test_rol_functie_rko(self):
        account = self.account_admin
        account.groups.add(self.group_rko)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertFalse(rol_is_RKO(self.client))
        rol_activeer_functie(self.client, self.group_rko.pk).save()
        self.assertTrue(rol_is_RKO(self.client))

        self.assertTrue(rol_get_beschrijving(self.client), "RKO test")

    def test_rol_functie_rcl(self):
        account = self.account_admin
        account.groups.add(self.group_rcl)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertNotEqual(rol_get_huidige(self.client), Rollen.ROL_RCL)
        rol_activeer_functie(self.client, self.group_rcl.pk).save()
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_RCL)

    def test_rol_functie_cwz(self):
        account = self.account_admin
        account.groups.add(self.group_cwz)
        account.groups.add(self.group_tst)      # voor coverage (geen functie)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertFalse(rol_is_CWZ(self.client))
        rol_activeer_functie(self.client, self.group_cwz.pk).save()
        self.assertTrue(rol_is_CWZ(self.client))

    def test_geen_rolwissel(self):
        # dit raakt de exceptie in Account.rol:rol_mag_wisselen
        self.client.logout()
        resp = self.client.get('/account/wissel-van-rol/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

    def test_rol_expansie(self):
        self._expansie_functie = 2

        account = self.account_admin

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        # activeer zijn ingebouwde rol
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_BB(self.client))

        # activeer zijn door expansie gekregen functie
        rol_activeer_functie(self.client, self.group_bko.pk).save()
        self.assertTrue(rol_is_BKO(self.client))

        # restore
        self._expansie_functie = 0

    def test_rol_expansie_bad(self):
        self._expansie_functie = 1

        # controleer dat afwezigheid van bepaalde sessie variabelen afgehandeld wordt
        self.client.logout()
        rol_activeer_functie(self.client, self.group_rko.pk).save()
        rol_activeer_rol(self.client, "BB").save()
        rol_activeer_rol(self.client, "huh").save()

        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_BB(self.client))

        # CWZ is geen vaste rol, dus mag niet --> behoud oude rol
        rol_activeer_rol(self.client, 'CWZ').save()
        self.assertTrue(rol_is_BB(self.client))

        # nu moet deze rol ook de functie group_bko hebben
        rol_activeer_functie(self.client, "jek").save()
        self.assertTrue(rol_is_BB(self.client))

        # RKO is niet geexpandeerd vanuit BB, dus niet toegestaan --> behoud oude rol
        rol_activeer_functie(self.client, self.group_rko.pk).save()
        self.assertTrue(rol_is_BB(self.client))

        # restore
        self._expansie_functie = 0

    def test_rol_enum_pallet(self):
        self.client.logout()
        rollen = [tup for tup in rol_enum_pallet(self.client)]
        self.assertEqual(len(rollen), 0)

        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()

        rollen = [tup for tup in rol_enum_pallet(self.client)]
        #print("rollen: %s" % repr(rollen))
        # 3 rollen: IT beheerder, BB, Gebruiker (NONE)
        self.assertEqual(len(rollen), 3)



# end of file
