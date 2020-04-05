# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.rechten import account_rechten_login_gelukt, account_rechten_otp_controle_gelukt
from Functie.rol import Rollen, SESSIONVAR_ROL_HUIDIGE, SESSIONVAR_ROL_MAG_WISSELEN, SESSIONVAR_ROL_PALLET_FUNCTIES,\
                        rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle, \
                        rol_mag_wisselen, rol_zet_plugins, \
                        rol_get_huidige, rol_get_huidige_functie, \
                        rol_activeer_rol, rol_activeer_functie, rol_evalueer_opnieuw, \
                        rol_get_beschrijving, rol_enum_pallet, \
                        roltest_park_plugins, roltest_restore_plugins
from Functie.models import maak_functie, maak_cwz
from Functie.views import account_vhpg_is_geaccepteerd
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
from types import SimpleNamespace
import datetime


class TestFunctieRol(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie, diverse corner-cases """

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

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')

        self.functie_bko = maak_functie("BKO test", "BKO")
        self.functie_rko = maak_functie("RKO test", "RKO")  # TODO: zet nhb_rayon
        self.functie_rcl = maak_functie("RCL test", "RCL")  # TODO: zet nhb_regio
        self.functie_cwz = maak_functie("CWZ test", "CWZ")
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
        self.nhbver1 = ver

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

        roltest_park_plugins()
        self._expansie_functie = 0
        rol_zet_plugins(self._rol_expansie)

    def tearDown(self):
        roltest_restore_plugins()

    def test_maak_cwz(self):
        self.assertEqual(len(self.functie_cwz.accounts.all()), 0)
        added = maak_cwz(self.nhbver1, self.account_normaal)
        self.assertTrue(added)
        self.assertEqual(len(self.functie_cwz.accounts.all()), 1)

        # opnieuw toevoegen heeft geen effect
        added = maak_cwz(self.nhbver1, self.account_normaal)
        self.assertFalse(added)
        self.assertEqual(len(self.functie_cwz.accounts.all()), 1)

    def test_rol_geen_sessie(self):
        # probeer beveiliging tegen afwezigheid sessie variabelen
        # typisch tweedelijns, want views checken user.is_authenticated

        request = self.client

        self.assertTrue(SESSIONVAR_ROL_MAG_WISSELEN not in request.session)
        res = rol_mag_wisselen(request)
        self.assertFalse(res)

        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session)
        rol_activeer_rol(request, 'schutter')
        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session)

        rol_activeer_functie(request, 'geen getal')
        self.assertTrue(SESSIONVAR_ROL_PALLET_FUNCTIES not in request.session)
        rol_activeer_functie(request, 0)

        self.assertTrue(SESSIONVAR_ROL_PALLET_FUNCTIES not in request.session)
        rol_enum_pallet(request)

    def test_plugin(self):
        # controleer get toekennen van rollen

        # TODO: finish
        # is_staff -->
        # is_BB -->
        # BKO functie -->
        # RKO functie -->
        # RCL functie -->
        # CWZ functie -->
        pass


    def NOT_test_activeer_rol(self):
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

        # niet aan nhblid gekoppeld schutter account
        account.is_staff = False
        account.is_BB = False
        request.session = dict()
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_NONE)
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
        self.nhblid1.account = account
        self.nhblid1.save()
        request.session = dict()
        account_rechten_login_gelukt(request)
        rol_zet_sessionvars_na_login(account, request)
        self.assertFalse(rol_mag_wisselen(request))
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
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
        request.session = dict()
        account_rechten_otp_controle_gelukt(request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        self.assertTrue(rol_mag_wisselen(request))

        account_vhpg_is_geaccepteerd(account)
        account_rechten_otp_controle_gelukt(request)
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)

        rol_activeer_rol(request, 'schutter')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'beheerder')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_SCHUTTER)
        rol_activeer_rol(request, 'BB')
        self.assertEqual(rol_get_huidige(request), Rollen.ROL_BB)
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
        print("admin.nhblid_set: %s" % repr(account.nhblid_set.all()))
        request.session = dict()
        request.user = account
        #account_vhpg_is_geaccepteerd(account)
        account_rechten_otp_controle_gelukt(request)
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

    def NOT_test_rol_functie_bko(self):
        self._expansie_functie = 0
        self.functie_bko.accounts.add(self.account_admin)

        self.e2e_login_and_pass_otp(self.account_admin)

        rol_activeer_functie(self.client, self.functie_bko.pk)

        rol = rol_get_huidige(self.client)
        self.assertEqual(rol, Rollen.ROL_BKO)

        rol, functie = rol_get_huidige_functie(self.client)
        self.assertEqual(rol, Rollen.ROL_BKO)
        self.assertEqual(functie, self.functie_bko)
        self.assertTrue(rol_get_beschrijving(self.client), "BKO test")

        self.e2e_logout()
        self.assertTrue(rol_get_beschrijving(self.client), "?")

        # corner-case coverage
        self.assertTrue(str(self.functie_bko) != "")

    def NOT_test_rol_functie_rko(self):
        self._expansie_functie = 0
        self.functie_rko.accounts.add(self.account_admin)

        self.e2e_login_and_pass_otp(self.account_admin)

        rol_activeer_functie(self.client, self.functie_rko.pk)
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_RKO)

        self.assertTrue(rol_get_beschrijving(self.client), "RKO test")

    def NOT_test_rol_functie_rcl(self):
        self.functie_rcl.accounts.add(self.account_admin)

        self.e2e_login_and_pass_otp(self.account_admin)

        self.assertNotEqual(rol_get_huidige(self.client), Rollen.ROL_RCL)
        rol_activeer_functie(self.client, self.functie_rcl.pk)
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_RCL)

    def NOT_test_rol_functie_cwz(self):
        self._expansie_functie = 0
        self.functie_cwz.accounts.add(self.account_admin)
        self.functie_tst.accounts.add(self.account_admin)

        self.e2e_login_and_pass_otp(self.account_admin)

        rol_activeer_functie(self.client, self.functie_cwz.pk)
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_CWZ)

    def NOT_test_rol_expansie(self):
        self._expansie_functie = 2

        self.e2e_login_and_pass_otp(self.account_admin)

        # activeer zijn ingebouwde rol
        self.e2e_wisselnaarrol_bb()
        # TODO: check of we BB zijn

        # activeer zijn door expansie gekregen functie
        self.e2e_wissel_naar_functie(self.functie_bko)
        # TODO: check of we BKO zijn

    def NOT_test_rol_expansie_bad1(self):
        self._expansie_functie = 1

        # controleer dat afwezigheid van bepaalde sessie variabelen afgehandeld wordt
        self.e2e_logout()
        rol_activeer_functie(self.client, self.functie_rko.pk)
        rol_activeer_rol(self.client, "BB")
        rol_activeer_rol(self.client, "huh")

        self.e2e_login_and_pass_otp(self.account_admin)

        rol_activeer_rol(self.client, 'BB')
        self.assertTrue(rol_is_BB(self.client))

        # CWZ is geen vaste rol, dus mag niet --> behoud oude rol
        rol_activeer_rol(self.client, 'CWZ')
        self.assertTrue(rol_is_BB(self.client))

        # nu moet deze rol ook de functie bko hebben
        rol_activeer_functie(self.client, "jek")
        self.assertTrue(rol_is_BB(self.client))

        # RKO is niet geëxpandeerd vanuit BB, dus niet toegestaan --> behoud oude rol
        rol_activeer_functie(self.client, self.functie_rko.pk)
        self.assertTrue(rol_is_BB(self.client))

    def NOT_test_rol_enum_pallet(self):
        self._expansie_functie = 0
        self.e2e_logout()
        rollen = [tup for tup in rol_enum_pallet(self.client)]
        self.assertEqual(len(rollen), 0)

        self.e2e_login_and_pass_otp(self.account_admin)
        rol_activeer_rol(self.client, 'BB')

        rollen = [tup for tup in rol_enum_pallet(self.client)]
        #print("rollen: %s" % repr(rollen))
        # 3 rollen: IT beheerder, BB, Gebruiker
        self.assertEqual(len(rollen), 3)

        self._expansie_functie = 2
        self.e2e_logout()
        self.e2e_login_and_pass_otp(self.account_admin)
        rol_activeer_rol(self.client, 'BB')

        rollen = [tup for tup in rol_enum_pallet(self.client)]
        #print("rollen: %s" % repr(rollen))
        # 5 rollen: IT beheerder, BB, Gebruiker, BKO, RKO
        self.assertEqual(len(rollen), 5)

# end of file
