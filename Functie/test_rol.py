# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Functie.rol import Rollen, rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle, \
                         rol_mag_wisselen, rol_is_beheerder, rol_zet_plugins, \
                         rol_get_huidige, rol_get_huidige_functie, \
                         rol_activeer_rol, rol_activeer_functie, rol_evalueer_opnieuw, \
                         rol_get_beschrijving, rol_enum_pallet, \
                         rol_is_BB, rol_is_BKO, rol_is_RKO, rol_is_CWZ
from Functie.rol import roltest_park_plugins, roltest_restore_plugins
from Functie.models import maak_functie
from Account.models import Account,\
                    account_zet_sessionvars_na_login,\
                    account_zet_sessionvars_na_otp_controle,\
                    account_vhpg_is_geaccepteerd
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from types import SimpleNamespace
import datetime


class TestFunctieRol(TestCase):
    """ unit tests voor de Functie applicatie, module Rol """

    def _rol_expansie(self, rol_in, functie_in):
        if self._expansie_functie >= 1:
            if rol_in == Rollen.ROL_BB:
                yield Rollen.ROL_BKO, self.functie_bko.pk

        if self._expansie_functie >= 2:
            if rol_in == Rollen.ROL_BKO:
                yield Rollen.ROL_RKO, self.functie_rko.pk
                yield Rollen.ROL_RKO, self.functie_rko.pk       # trigger dupe filter

    def setUp(self):
        """ initialisatie van de test case """

        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

        self.functie_bko = maak_functie("BKO test", "BKO")
        self.functie_rko = maak_functie("RKO test", "RKO")  # TODO: zet nhb_rayon
        self.functie_rcl = maak_functie("RCL test", "RCL")  # TODO: zet nhb_regio
        self.functie_cwz = maak_functie("CWZ test", "CWZ")  # TODO: zet nhb_ver
        self.functie_tst = maak_functie("Test test", "x")

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

        roltest_park_plugins()
        self._expansie_functie = 0
        rol_zet_plugins(self._rol_expansie)

    def tearDown(self):
        roltest_restore_plugins()

    def test_rol(self):
        # unit-tests voor de 'rol' module
        self._expansie_functie = 0

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

        rol, functie = rol_get_huidige_functie(request)
        self.assertEqual(rol, Rollen.ROL_IT)
        self.assertEqual(functie, None)

    def test_rol_functie_bko(self):
        self._expansie_functie = 0
        account = self.account_admin
        account.functies.add(self.functie_bko)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertFalse(rol_is_BKO(self.client))
        rol_activeer_functie(self.client, self.functie_bko.pk).save()
        self.assertTrue(rol_is_BKO(self.client))

        rol, functie = rol_get_huidige_functie(self.client)
        self.assertEqual(rol, Rollen.ROL_BKO)
        self.assertEqual(functie, self.functie_bko)
        self.assertTrue(rol_get_beschrijving(self.client), "BKO test")

        self.client.logout()
        self.assertTrue(rol_get_beschrijving(self.client), "?")

        # corner-case coverage
        self.assertTrue(str(self.functie_bko) != "")

    def test_rol_functie_rko(self):
        self._expansie_functie = 0
        account = self.account_admin
        account.functies.add(self.functie_rko)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertFalse(rol_is_RKO(self.client))
        rol_activeer_functie(self.client, self.functie_rko.pk).save()
        self.assertTrue(rol_is_RKO(self.client))

        self.assertTrue(rol_get_beschrijving(self.client), "RKO test")

    def test_rol_functie_rcl(self):
        account = self.account_admin
        account.functies.add(self.functie_rcl)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertNotEqual(rol_get_huidige(self.client), Rollen.ROL_RCL)
        rol_activeer_functie(self.client, self.functie_rcl.pk).save()
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_RCL)

    def test_rol_functie_cwz(self):
        self._expansie_functie = 0
        account = self.account_admin
        account.functies.add(self.functie_cwz)
        account.functies.add(self.functie_tst)      # voor coverage (geen functie)

        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()

        self.assertFalse(rol_is_CWZ(self.client))
        rol_activeer_functie(self.client, self.functie_cwz.pk).save()
        self.assertTrue(rol_is_CWZ(self.client))

    def test_geen_rolwissel(self):
        # dit raakt de exceptie in Account.rol:rol_mag_wisselen
        self._expansie_functie = 0
        self.client.logout()
        resp = self.client.get('/functie/wissel-van-rol/')
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
        rol_activeer_functie(self.client, self.functie_bko.pk).save()
        self.assertTrue(rol_is_BKO(self.client))

    def test_rol_expansie_bad1(self):
        self._expansie_functie = 1

        # controleer dat afwezigheid van bepaalde sessie variabelen afgehandeld wordt
        self.client.logout()
        rol_activeer_functie(self.client, self.functie_rko.pk).save()
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

        # nu moet deze rol ook de functie bko hebben
        rol_activeer_functie(self.client, "jek").save()
        self.assertTrue(rol_is_BB(self.client))

        # RKO is niet geëxpandeerd vanuit BB, dus niet toegestaan --> behoud oude rol
        rol_activeer_functie(self.client, self.functie_rko.pk).save()
        self.assertTrue(rol_is_BB(self.client))

    def test_rol_enum_pallet(self):
        self._expansie_functie = 0
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
        # 3 rollen: IT beheerder, BB, Gebruiker
        self.assertEqual(len(rollen), 3)


        self._expansie_functie = 2
        self.client.logout()
        self.client.login(username=account.username, password='wachtwoord')
        account_vhpg_is_geaccepteerd(account)
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()

        rollen = [tup for tup in rol_enum_pallet(self.client)]
        #print("rollen: %s" % repr(rollen))
        # 5 rollen: IT beheerder, BB, Gebruiker, BKO, RKO
        self.assertEqual(len(rollen), 5)

    def test_rol_account_gebruiker(self):
        account = self.account_normaal
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(account, self.client).save()
        self.assertEqual(rol_get_beschrijving(self.client), 'Gebruiker')
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_NONE)

    def test_rol_account_cwz(self):
        account = self.account_normaal
        account.functies.add(self.functie_cwz)
        account_vhpg_is_geaccepteerd(account)
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        rol_activeer_functie(self.client, self.functie_cwz.pk).save()
        self.assertEqual(rol_get_beschrijving(self.client), 'CWZ test')
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_CWZ)

    def test_rol_evalueer_opnieuw(self):
        account = self.account_normaal
        account_vhpg_is_geaccepteerd(account)
        self.client.user = account
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        self.assertEqual(rol_get_beschrijving(self.client), 'Gebruiker')
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_NONE)

        # kan niet cwz worden
        rol_activeer_functie(self.client, self.functie_cwz.pk).save()
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_NONE)

        # voeg CWZ rechten toe
        account.functies.add(self.functie_cwz)

        # kan niet cwz worden
        rol_activeer_functie(self.client, self.functie_cwz.pk).save()
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_NONE)

        # opnieuw evalueren
        rol_evalueer_opnieuw(self.client)
        rol_activeer_functie(self.client, self.functie_cwz.pk).save()
        self.assertEqual(rol_get_beschrijving(self.client), 'CWZ test')
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_CWZ)

        # opnieuw evalueren inclusief her-activatie van CWZ rol
        rol_evalueer_opnieuw(self.client)
        self.assertEqual(rol_get_beschrijving(self.client), 'CWZ test')
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_CWZ)

        # voeg RKO rechten toe
        account.functies.add(self.functie_rko)

        # kan niet rko worden
        rol_activeer_functie(self.client, self.functie_rko.pk).save()
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_CWZ)

        # opnieuw evalueren inclusief her-activatie van CWZ rol
        rol_evalueer_opnieuw(self.client)
        self.assertEqual(rol_get_beschrijving(self.client), 'CWZ test')
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_CWZ)

        # kan nu wel RKO worden
        rol_activeer_functie(self.client, self.functie_rko.pk).save()
        self.assertEqual(rol_get_beschrijving(self.client), 'RKO test')
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_RKO)


# end of file
