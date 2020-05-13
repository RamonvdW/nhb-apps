# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from .leeftijdsklassen import leeftijdsklassen_plugin_na_login, get_sessionvars_leeftijdsklassen
from types import SimpleNamespace
import datetime


class TestSchutterLeeftijdsklassen(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie, module Leeftijdsklassen """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@test.com', 'Geen')

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
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_normaal
        lid.email = lid.account.email
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

    def test_leeftijdsklassen(self):
        # unit-tests voor de 'leeftijdsklassen' module

        # simuleer de normale inputs
        request = SimpleNamespace()
        request.session = dict()

        # session vars niet gezet
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertIsNone(huidige_jaar)
        self.assertIsNone(leeftijd)
        self.assertFalse(is_jong)
        self.assertIsNone(wlst)
        self.assertIsNone(clst)

        # geen nhblid
        leeftijdsklassen_plugin_na_login(request, "from_ip", self.account_geenlid)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertIsNone(huidige_jaar)
        self.assertIsNone(leeftijd)
        self.assertFalse(is_jong)
        self.assertIsNone(wlst)
        self.assertIsNone(clst)

        # test met verschillende leeftijdsklassen van een nhblid
        # noteer: afhankelijk van BasisTypen: init_leeftijdsklasse_2018
        account = self.account_normaal
        nhblid = self.nhblid1
        now_jaar = timezone.now().year  # TODO: should stub, for more reliable test

        # nhblid, aspirant (<= 13)
        nhb_leeftijd = 11
        nhblid.geboorte_datum = datetime.date(year=now_jaar-nhb_leeftijd, month=1, day=1)
        nhblid.save()
        leeftijdsklassen_plugin_na_login(request, "from_ip", account)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Aspirant', 'Aspirant', 'Aspirant', 'Aspirant', 'Cadet'))
        #                        -1=10       0=11        +1=12       +2=13       +3=14
        self.assertEqual(clst, ('Aspirant', 'Aspirant', 'Aspirant', 'Cadet', 'Cadet'))

        # nhblid, cadet (14, 15, 16, 17)
        nhb_leeftijd = 14
        nhblid.geboorte_datum = datetime.date(year=now_jaar-nhb_leeftijd, month=1, day=1)
        nhblid.save()
        leeftijdsklassen_plugin_na_login(request, "from_ip", account)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Aspirant', 'Cadet', 'Cadet', 'Cadet', 'Cadet'))
        #                        -1=13       0=14     +1=15    +2=16    +3=17
        self.assertEqual(clst, ('Cadet', 'Cadet', 'Cadet', 'Cadet', 'Junior'))

        # nhblid, junior (18, 19, 20)
        nhb_leeftijd = 18
        nhblid.geboorte_datum = datetime.date(year=now_jaar-nhb_leeftijd, month=1, day=1)
        nhblid.save()
        leeftijdsklassen_plugin_na_login(request, "from_ip", account)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertTrue(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Cadet', 'Junior', 'Junior', 'Junior', 'Senior'))
        #                        -1=17    0=18     +1=19      +2=20     +3=21
        self.assertEqual(clst, ('Junior', 'Junior', 'Junior', 'Senior', 'Senior'))

        # nhblid, senior (>= 21)
        nhb_leeftijd = 30
        nhblid.geboorte_datum = datetime.date(year=now_jaar-nhb_leeftijd, month=1, day=1)
        nhblid.save()
        leeftijdsklassen_plugin_na_login(request, "from_ip", account)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertFalse(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Senior', 'Senior', 'Senior', 'Senior', 'Senior'))
        self.assertEqual(clst, wlst)

        # nhblid, master (zelfde als senior, for now)
        nhb_leeftijd = 50
        nhblid.geboorte_datum = datetime.date(year=now_jaar-nhb_leeftijd, month=1, day=1)
        nhblid.save()
        leeftijdsklassen_plugin_na_login(request, "from_ip", account)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(request)
        self.assertEquals(huidige_jaar, now_jaar)
        self.assertEqual(leeftijd, nhb_leeftijd)
        self.assertFalse(is_jong)        # onder 30 == jong
        self.assertEqual(wlst, ('Senior', 'Senior', 'Senior', 'Senior', 'Senior'))
        self.assertEqual(clst, wlst)

    def test_login(self):
        self.e2e_login(self.account_normaal)
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(self.client)
        self.assertFalse(is_jong)
        self.assertGreaterEqual(leeftijd, 48)    # in 2020-1972 = 48

    def test_view(self):
        # zonder login --> terug naar het plein
        resp = self.client.get('/schutter/leeftijdsklassen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        # met schutter-login wel toegankelijk
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/schutter/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported('/schutter/leeftijdsklassen/')

# end of file
