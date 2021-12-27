# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from NhbStructuur.models import NhbRegio, NhbVereniging
from .leeftijdsklassen import bereken_leeftijdsklassen
from .models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestSporterLeeftijdsklassen(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Leeftijdsklassen """

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
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_normaal
        sporter.email = sporter.account.email
        sporter.save()
        self.sporter1 = sporter

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

    def test_leeftijdsklassen(self):
        now = timezone.now()  # is in UTC
        now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
        huidige_jaar = now.year

        # aspirant
        tup = bereken_leeftijdsklassen(huidige_jaar - 9)
        self.assertEqual(tup, (huidige_jaar,
                               9,
                               ['Aspirant', 'Aspirant', 'Aspirant', 'Aspirant', 'Aspirant'],
                               ['Aspiranten <11 jaar', 'Aspiranten <11 jaar', 'Aspiranten <11 jaar', 'Aspiranten 11-12 jaar', 'Aspiranten 11-12 jaar'],
                               'Aspirant'))

        # cadet (14..17)
        tup = bereken_leeftijdsklassen(huidige_jaar - 13)
        self.assertEqual(tup, (huidige_jaar,
                               13,
                               ['Aspirant', 'Aspirant', 'Cadet', 'Cadet', 'Cadet'],
                               ['Aspiranten 11-12 jaar', 'Cadetten', 'Cadetten', 'Cadetten', 'Cadetten'],
                               'Cadet'))

        # junior (18..20)
        tup = bereken_leeftijdsklassen(huidige_jaar - 18)
        self.assertEqual(tup, (huidige_jaar,
                               18,
                               ['Cadet', 'Junior', 'Junior', 'Junior', 'Senior'],
                               ['Junioren', 'Junioren', 'Junioren', 'Senioren', 'Senioren'],
                               'Junior'))

        # senior
        tup = bereken_leeftijdsklassen(huidige_jaar - 21)
        self.assertEqual(tup, (huidige_jaar,
                               21,
                               ['Junior', 'Senior', 'Senior', 'Senior', 'Senior'],
                               ['Senioren', 'Senioren', 'Senioren', 'Senioren', 'Senioren'],
                               'Senior'))

        # master
        tup = bereken_leeftijdsklassen(huidige_jaar - 50)
        self.assertEqual(tup, (huidige_jaar,
                               50,
                               ['Senior', 'Master', 'Master', 'Master', 'Master'],
                               ['Senioren', 'Senioren', 'Senioren', 'Senioren', 'Senioren'],
                               'Senior'))

        # veteraan
        tup = bereken_leeftijdsklassen(huidige_jaar - 60)
        self.assertEqual(tup, (huidige_jaar,
                               60,
                               ['Master', 'Veteraan', 'Veteraan', 'Veteraan', 'Veteraan'],
                               ['Senioren', 'Senioren', 'Senioren', 'Senioren', 'Senioren'],
                               'Senior'))

    def test_view(self):
        # zonder login
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/leeftijdsklassen/', follow=True)
        self.assert403(resp)

        # inlog, geen NHB lid
        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/leeftijdsklassen/')
        self.assert403(resp)

        # schutter
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported('/sporter/leeftijdsklassen/')

# end of file
