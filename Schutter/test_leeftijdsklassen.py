# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from .leeftijdsklassen import bereken_leeftijdsklassen
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
        ver.ver_nr = "1000"
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

    def test_anon(self):
        # niet mogelijk om te bereiken via de views
        request = self.client
        request.user = SimpleNamespace()
        request.user.is_authenticated = False
        tup = bereken_leeftijdsklassen(request)
        self.assertEqual(tup, (None, None, False, None, None))

        # login met een gebruiker zonder NhbLid koppeling
        request.user = self.account_admin
        tup = bereken_leeftijdsklassen(request)
        self.assertEqual(tup, (None, None, False, None, None))

    def test_view(self):
        # zonder login --> terug naar het plein
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/leeftijdsklassen/', follow=True)
        self.assert403(resp)

        # met schutter-login wel toegankelijk
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(51):
            resp = self.client.get('/sporter/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported('/sporter/leeftijdsklassen/')

# end of file
