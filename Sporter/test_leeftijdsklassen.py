# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from NhbStructuur.models import NhbRegio, NhbVereniging
from .leeftijdsklassen import bereken_leeftijdsklassen_nhb
from .models import Sporter, SporterVoorkeuren
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

        # check de 5 persoonlijke indicaties: -1 t/m +3 jaar ronde de huidige leeftijd

        # onder 12 / aspirant
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 9)
        self.assertEqual(tup, (huidige_jaar,
                               9,
                               # wedstrijden
                               ['Onder 12', 'Onder 12', 'Onder 12', 'Onder 12', 'Onder 14'],
                               # competitie (1 jaar opgeschoven)
                               ['Onder 12 (aspiranten)', 'Onder 12 (aspiranten)', 'Onder 12 (aspiranten)', 'Onder 14 (aspiranten)', 'Onder 14 (aspiranten)'],
                               'Onder 12'))

        # onder 18 / cadet (14..17)
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 13)
        self.assertEqual(tup, (huidige_jaar,
                               13,
                               ['Onder 14', 'Onder 14', 'Onder 18', 'Onder 18', 'Onder 18'],
                               ['Onder 14 (aspiranten)', 'Onder 18 (cadetten)', 'Onder 18 (cadetten)', 'Onder 18 (cadetten)', 'Onder 18 (cadetten)'],
                               'Onder 18'))

        # junior (18..20)
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 18)
        self.assertEqual(tup, (huidige_jaar,
                               18,
                               ['Onder 18', 'Onder 21', 'Onder 21', 'Onder 21', '21+'],
                               ['Onder 21 (junioren)', 'Onder 21 (junioren)', 'Onder 21 (junioren)', '21+ (senioren)', '21+ (senioren)'],
                               'Onder 21'))

        # senior
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 21)
        self.assertEqual(tup, (huidige_jaar,
                               21,
                               ['Onder 21', '21+', '21+', '21+', '21+'],
                               ['21+ (senioren)', '21+ (senioren)', '21+ (senioren)', '21+ (senioren)', '21+ (senioren)'],
                               '21+'))

        # master
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 50)
        self.assertEqual(tup, (huidige_jaar,
                               50,
                               ['21+', '50+', '50+', '50+', '50+'],
                               ['21+ (senioren)', '21+ (senioren)', '21+ (senioren)', '21+ (senioren)', '21+ (senioren)'],
                               '21+'))

        # veteraan
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 60)
        self.assertEqual(tup, (huidige_jaar,
                               60,
                               ['50+', '60+', '60+', '60+', '60+'],
                               ['21+ (senioren)', '21+ (senioren)', '21+ (senioren)', '21+ (senioren)', '21+ (senioren)'],
                               '21+'))

    def test_view(self):
        # zonder login
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/leeftijdsklassen/')
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

        # met voorkeuren
        voorkeur = SporterVoorkeuren(
                        sporter=self.sporter1)
        voorkeur.save()
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        # met geslacht X, geen keuze gemaakt
        voorkeur.wedstrijd_geslacht_gekozen = False
        voorkeur.save(update_fields=['wedstrijd_geslacht_gekozen'])
        with self.assert_max_queries(20):
            resp = self.client.get('/sporter/leeftijdsklassen/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported('/sporter/leeftijdsklassen/')

# end of file
