# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import GESLACHT_ANDERS, ORGANISATIE_IFAA, ORGANISATIE_NHB, ORGANISATIE_WA
from NhbStructuur.models import NhbRegio, NhbVereniging
from .leeftijdsklassen import bereken_leeftijdsklassen_nhb
from .models import Sporter, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestSporterLeeftijdsklassen(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Leeftijdsklassen """

    url_leeftijdsklassen = '/sporter/leeftijden/persoonlijk/'
    url_leeftijdsgroepen = '/sporter/leeftijden/'

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

    def test_model(self):
        datum_wedstrijd_voor_verjaardag = datetime.date(2022, month=self.sporter1.geboorte_datum.month,
                                                        day=self.sporter1.geboorte_datum.day-1)
        datum_wedstrijd_op_verjaardag = datetime.date(2022, month=self.sporter1.geboorte_datum.month,
                                                      day=self.sporter1.geboorte_datum.day)
        datum_wedstrijd_na_verjaardag = datetime.date(2022, month=self.sporter1.geboorte_datum.month,
                                                      day=self.sporter1.geboorte_datum.day+1)

        # IFAA hanteert echte leeftijd
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_IFAA)
        self.assertEqual(n, 49)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_IFAA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_IFAA)
        self.assertEqual(n, 50)

        # WA en NHB hanteren kijken het hele jaar naar de leeftijd die je bereikt
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_WA)
        self.assertEqual(n, 50)

        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_voor_verjaardag, ORGANISATIE_NHB)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_op_verjaardag, ORGANISATIE_NHB)
        self.assertEqual(n, 50)
        n = self.sporter1.bereken_wedstrijdleeftijd(datum_wedstrijd_na_verjaardag, ORGANISATIE_NHB)
        self.assertEqual(n, 50)

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
                               ['Onder 12', 'Onder 12', 'Onder 12', 'Onder 14', 'Onder 14'],
                               'Onder 12'))

        # onder 18 / cadet (14..17)
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 13)
        self.assertEqual(tup, (huidige_jaar,
                               13,
                               ['Onder 14', 'Onder 14', 'Onder 18', 'Onder 18', 'Onder 18'],
                               ['Onder 14', 'Onder 18', 'Onder 18', 'Onder 18', 'Onder 18'],
                               'Onder 18'))

        # junior (18..20)
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 18)
        self.assertEqual(tup, (huidige_jaar,
                               18,
                               ['Onder 18', 'Onder 21', 'Onder 21', 'Onder 21', '21+'],
                               ['Onder 21', 'Onder 21', 'Onder 21', '21+', '21+'],
                               'Onder 21'))

        # senior
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 21)
        self.assertEqual(tup, (huidige_jaar,
                               21,
                               ['Onder 21', '21+', '21+', '21+', '21+'],
                               ['21+', '21+', '21+', '21+', '21+'],
                               '21+'))

        # master
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 50)
        self.assertEqual(tup, (huidige_jaar,
                               50,
                               ['21+', '50+', '50+', '50+', '50+'],
                               ['21+', '21+', '21+', '21+', '21+'],
                               '21+'))

        # veteraan
        tup = bereken_leeftijdsklassen_nhb(huidige_jaar - 60)
        self.assertEqual(tup, (huidige_jaar,
                               60,
                               ['50+', '60+', '60+', '60+', '60+'],
                               ['21+', '21+', '21+', '21+', '21+'],
                               '21+'))

    def test_persoonlijk(self):
        # zonder login
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assert403(resp)

        # inlog, geen NHB lid
        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assert403(resp)

        # sporter
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        # met voorkeuren
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        # met geslacht X, geen keuze gemaakt
        self.sporter1.geslacht = GESLACHT_ANDERS
        self.sporter1.save(update_fields=['geslacht'])
        voorkeur = self.sporter1.sportervoorkeuren_set.all()[0]
        voorkeur.wedstrijd_geslacht_gekozen = False
        voorkeur.save(update_fields=['wedstrijd_geslacht_gekozen'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsklassen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsklassen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_leeftijdsklassen)

        # redirect oud naar nieuw
        resp = self.client.get('/sporter/leeftijdsklassen/')
        self.assert_is_redirect(resp, '/sporter/leeftijden/persoonlijk/')

    def test_groepen(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leeftijdsgroepen)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/leeftijdsgroepen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_leeftijdsgroepen)


# end of file
