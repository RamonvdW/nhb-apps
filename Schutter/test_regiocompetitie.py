# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import DeelCompetitie, RegioCompetitieSchutterBoog
from Overig.e2ehelpers import E2EHelpers
from Score.models import aanvangsgemiddelde_opslaan
from .models import SchutterBoog
import datetime


class TestSchutterRegiocompetitie(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie; module Inschrijven/Uitschrijven Regiocompetitie """

    test_after = ('Account', 'NhbStructuur', 'Competitie')

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@test.com', 'Geen')
        self.account_twee = self.e2e_create_account('twee', 'twee@test.com', 'Twee')

        # afhankelijk van de rayon/regio's aangemaakt door NhbStructuur migratie

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver = ver

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
        lid.voornaam = "Twee"
        lid.achternaam = "de Tester"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_twee
        lid.email = lid.account.email
        lid.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Geen"
        lid.achternaam = "Lid"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        #lid.bij_vereniging =
        lid.account = self.account_geenlid
        lid.email = lid.account.email
        lid.save()

        self.url_profiel = '/schutter/'
        self.url_voorkeuren = '/schutter/voorkeuren/'
        self.url_inschrijven = '/schutter/regiocompetitie/inschrijven/%s/%s/'   # deelcomp_pk, schutterboog_pk
        self.url_uitschrijven = '/schutter/regiocompetitie/uitschrijven/%s/'    # regiocomp_pk

    def _prep_voorkeuren(self):
        # haal de voorkeuren op - hiermee worden de SchutterBoog records aangemaakt
        self.client.get(self.url_voorkeuren)

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        schutterboog.voor_wedstrijd = True
        schutterboog.heeft_interesse = False
        schutterboog.save()

        for boog in ('C', 'IB', 'LB'):
            schutterboog = SchutterBoog.objects.get(boogtype__afkorting=boog)
            schutterboog.heeft_interesse = False
            schutterboog.save()
        # for

    def _competitie_aanmaken(self):
        url_overzicht = '/competitie/'
        url_aanmaken = '/competitie/aanmaken/'
        url_ag_vaststellen = '/competitie/ag-vaststellen/'
        url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        url_klassegrenzen_vaststellen_25 = '/competitie/klassegrenzen/vaststellen/25/'

        # competitie aanmaken
        resp = self.client.post(url_aanmaken)
        self.assert_is_redirect(resp, url_overzicht)

        # aanvangsgemiddelden vaststellen
        resp = self.client.post(url_ag_vaststellen)

        # klassegrenzen vaststellen
        resp = self.client.post(url_klassegrenzen_vaststellen_18)
        resp = self.client.post(url_klassegrenzen_vaststellen_25)

    def test_inschrijven(self):
        # inschrijven als anon
        resp = self.client.post(self.url_inschrijven % (0, 0))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # inschrijven als BB (niet NHB lid)
        resp = self.client.post(self.url_inschrijven % (0, 0))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # inschrijven als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geenlid)
        resp = self.client.post(self.url_inschrijven % (0, 0))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf in voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, '2020-01-01', None, 'Test')
        self.assertTrue(res)
        resp = self.client.post(self.url_inschrijven % (deelcomp.pk, schutterboog.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        # illegaal deelcomp nummer
        resp = self.client.post(self.url_inschrijven % (99999, schutterboog.pk))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # illegaal schutterboog nummer
        resp = self.client.post(self.url_inschrijven % (99999, 'hallo'))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # schrijf in voor de 25m BB, zonder AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='25', nhb_regio=self.nhbver.regio)
        resp = self.client.post(self.url_inschrijven % (deelcomp.pk, schutterboog.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)

        # schutterboog hoort niet bij gebruiker
        self.client.logout()
        self.e2e_login(self.account_twee)
        resp = self.client.post(self.url_inschrijven % (deelcomp.pk, schutterboog.pk))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_uitschrijven(self):
        # uitschrijven als anon
        resp = self.client.post(self.url_uitschrijven % 0)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # uitschrijven als BB (niet NHB lid)
        resp = self.client.post(self.url_uitschrijven % 0)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # uitschrijven als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geenlid)
        resp = self.client.post(self.url_uitschrijven % 0)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf in voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog_18 = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog_18, 18, 8.18, '2020-01-01', None, 'Test')
        self.assertTrue(res)
        resp = self.client.post(self.url_inschrijven % (deelcomp.pk, schutterboog_18.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        inschrijving_18 = RegioCompetitieSchutterBoog.objects.all()[0]

        # schrijf in voor de 25m BB, zonder AG
        schutterboog_25 = SchutterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='25', nhb_regio=self.nhbver.regio)
        resp = self.client.post(self.url_inschrijven % (deelcomp.pk, schutterboog_25.pk))
        self.assert_is_redirect(resp, self.url_profiel)

        # schrijf uit van de 18m
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)
        resp = self.client.post(self.url_uitschrijven % inschrijving_18.pk)
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        # illegaal inschrijving nummer
        resp = self.client.post(self.url_uitschrijven % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # niet bestaand inschrijving nummer
        resp = self.client.post(self.url_uitschrijven % 'hoi')
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # schutterboog hoort niet bij gebruiker
        inschrijving_25 = RegioCompetitieSchutterBoog.objects.all()[0]
        self.client.logout()
        self.e2e_login(self.account_twee)
        resp = self.client.post(self.url_uitschrijven % inschrijving_25.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found


# end of file
