# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.rol import SESSIONVAR_ROL_HUIDIGE, SESSIONVAR_ROL_MAG_WISSELEN, \
                        SESSIONVAR_ROL_PALLET_FUNCTIES, SESSIONVAR_ROL_PALLET_VAST,\
                        rol_mag_wisselen, rol_enum_pallet, \
                        rol_activeer_rol, rol_activeer_functie
from Functie.models import maak_functie, maak_cwz
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestFunctieRol(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie, diverse corner-cases """

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

    def test_maak_cwz(self):
        self.assertEqual(self.functie_cwz.accounts.count(), 0)
        added = maak_cwz(self.nhbver1, self.account_normaal)
        self.assertTrue(added)
        self.assertEqual(self.functie_cwz.accounts.count(), 1)

        # opnieuw toevoegen heeft geen effect
        added = maak_cwz(self.nhbver1, self.account_normaal)
        self.assertFalse(added)
        self.assertEqual(self.functie_cwz.accounts.count(), 1)

    def test_geen_sessie(self):
        # probeer beveiliging tegen afwezigheid sessie variabelen
        # typisch tweedelijns, want views checken user.is_authenticated

        request = self.client

        self.assertTrue(SESSIONVAR_ROL_MAG_WISSELEN not in request.session.keys())
        res = rol_mag_wisselen(request)
        self.assertFalse(res)

        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session.keys())
        rol_activeer_rol(request, 'schutter')
        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session.keys())

        rol_activeer_functie(request, 'geen getal')
        self.assertTrue(SESSIONVAR_ROL_PALLET_FUNCTIES not in request.session.keys())
        rol_activeer_functie(request, 0)

        self.assertTrue(SESSIONVAR_ROL_PALLET_VAST not in request.session.keys())
        pallet = [tup for tup in rol_enum_pallet(request)]
        self.assertEqual(len(pallet), 0)

    def test_plugin(self):
        # controleer het toekennen van rollen

        # TODO: finish
        # is_staff -->
        # is_BB -->
        # BKO functie -->
        # RKO functie -->
        # RCL functie -->
        # CWZ functie -->
        pass


# end of file
