# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from Account.models import Account, account_zet_sessionvars_na_login
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.helpers import assert_html_ok, assert_template_used, assert_other_http_commands_not_supported
from Functie.rol import Rollen, rol_zet_sessionvars_na_login, rol_get_huidige
from .leeftijdsklassen import leeftijdsklassen_zet_sessionvars_na_login, \
                              get_sessionvars_leeftijdsklassen
from types import SimpleNamespace
import datetime


class TestSchutterLeeftijdsklassen(TestCase):
    """ unit tests voor de Schutter applicatie, module Leeftijdsklassen """

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
        self.account_normaal.nhblid = lid
        self.account_normaal.save()

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

    def test_leeftijdsklassen(self):
        # unit-tests voor de 'leeftijdsklassen' module

        # simuleer de normale inputs
        account = SimpleNamespace()
        request = SimpleNamespace()
        nhblid = SimpleNamespace()
        nhblid.geboorte_datum = SimpleNamespace()
        nhblid.geboorte_datum.year = 0
        request.session = dict()

        # session vars niet gezet
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertIsNone(huidige_jaar)
        self.assertIsNone(leeftijd)
        self.assertFalse(is_jong)
        self.assertIsNone(wlst)
        self.assertIsNone(clst)

        # geen nhblid
        account.nhblid = None
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertIsNone(huidige_jaar)
        self.assertIsNone(leeftijd)
        self.assertFalse(is_jong)
        self.assertIsNone(wlst)
        self.assertIsNone(clst)

        # test met verschillende leeftijdsklassen van een nhblid
        # noteer: afhankelijk van BasisTypen: init_leeftijdsklasse_2018
        account.nhblid = nhblid
        now_jaar = timezone.now().year  # TODO: should stub, for more reliable test

        # nhblid, aspirant (<= 13)
        nhb_leeftijd = 11
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Aspirant', 'Aspirant', 'Aspirant', 'Aspirant', 'Cadet'))
        #                        -1=10       0=11        +1=12       +2=13       +3=14
        self.assertEqual(clst, ('Aspirant', 'Aspirant', 'Aspirant', 'Cadet', 'Cadet'))

        # nhblid, cadet (14, 15, 16, 17)
        nhb_leeftijd = 14
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Aspirant', 'Cadet', 'Cadet', 'Cadet', 'Cadet'))
        #                        -1=13       0=14     +1=15    +2=16    +3=17
        self.assertEqual(clst, ('Cadet', 'Cadet', 'Cadet', 'Cadet', 'Junior'))

        # nhblid, junior (18, 19, 20)
        nhb_leeftijd = 18
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Cadet', 'Junior', 'Junior', 'Junior', 'Senior'))
        #                        -1=17    0=18     +1=19      +2=20     +3=21
        self.assertEqual(clst, ('Junior', 'Junior', 'Junior', 'Senior', 'Senior'))

        # nhblid, senior (>= 21)
        nhb_leeftijd = 30
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertFalse(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Senior', 'Senior', 'Senior', 'Senior', 'Senior'))
        self.assertEqual(clst, wlst)

        # nhblid, master (zelfde als senior, for now)
        nhb_leeftijd = 50
        nhblid.geboorte_datum.year = now_jaar - nhb_leeftijd
        leeftijdsklassen_zet_sessionvars_na_login(account, request)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertFalse(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Senior', 'Senior', 'Senior', 'Senior', 'Senior'))
        self.assertEqual(clst, wlst)

    def test_view(self):
        # zonder login --> terug naar het plein
        resp = self.client.get('/schutter/leeftijdsklassen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        # met schutter-login wel toegankelijk
        account = self.account_normaal
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(account, self.client).save()
        leeftijdsklassen_zet_sessionvars_na_login(account, self.client).save()
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_SCHUTTER)

        resp = self.client.get('/schutter/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('schutter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))
        assert_other_http_commands_not_supported(self, '/schutter/leeftijdsklassen/')

# end of file
