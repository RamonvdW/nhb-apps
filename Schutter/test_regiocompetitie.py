# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import Competitie, DeelCompetitie, RegioCompetitieSchutterBoog, INSCHRIJF_METHODE_3
from Competitie.test_fase import zet_competitie_fase
from Overig.e2ehelpers import E2EHelpers
from Score.models import aanvangsgemiddelde_opslaan
from .models import SchutterBoog
import datetime


class TestSchutterRegiocompetitie(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie; module Aanmelden/Afmelden Regiocompetitie """

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
        ver.ver_nr = "1000"
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

        self.url_profiel = '/sporter/'
        self.url_voorkeuren = '/sporter/voorkeuren/'
        self.url_aanmelden = '/sporter/regiocompetitie/aanmelden/%s/%s/'   # deelcomp_pk, schutterboog_pk
        self.url_bevestig_aanmelden = self.url_aanmelden + 'bevestig/'
        self.url_afmelden = '/sporter/regiocompetitie/afmelden/%s/'        # regiocomp_pk

    def _prep_voorkeuren(self):
        # haal de voorkeuren op - hiermee worden de SchutterBoog records aangemaakt
        with self.assert_max_queries(20):
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
        url_overzicht = '/bondscompetities/'
        url_aanmaken = '/bondscompetities/aanmaken/'
        url_ag_vaststellen = '/bondscompetities/ag-vaststellen/'
        url_klassegrenzen_vaststellen = '/bondscompetities/%s/klassegrenzen/vaststellen/'   # comp_pk

        # competitie aanmaken
        with self.assert_max_queries(20):
            resp = self.client.post(url_aanmaken)
        self.assert_is_redirect(resp, url_overzicht)

        comp_18 = Competitie.objects.get(afstand='18')
        comp_25 = Competitie.objects.get(afstand='25')

        # aanvangsgemiddelden vaststellen
        with self.assert_max_queries(5):
            resp = self.client.post(url_ag_vaststellen)

        # klassegrenzen vaststellen
        with self.assert_max_queries(24):
            resp = self.client.post(url_klassegrenzen_vaststellen % comp_18.pk)
        with self.assert_max_queries(24):
            resp = self.client.post(url_klassegrenzen_vaststellen % comp_25.pk)

        comp_18 = Competitie.objects.get(pk=comp_18.pk)
        zet_competitie_fase(comp_18, 'B')

        comp_25 = Competitie.objects.get(pk=comp_25.pk)
        zet_competitie_fase(comp_25, 'B')

    def test_inschrijven(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf in voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Dutch Target')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertFalse(inschrijving.is_handmatig_ag)
        self.assertEqual(str(inschrijving.aanvangsgemiddelde), "8.180")
        self.assertEqual(inschrijving.deelcompetitie, deelcomp)
        self.assertEqual(inschrijving.schutterboog, schutterboog)
        self.assertEqual(inschrijving.bij_vereniging, schutterboog.nhblid.bij_vereniging)
        self.assertFalse(inschrijving.inschrijf_voorkeur_team)
        self.assertEqual(inschrijving.inschrijf_notitie, '')
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'GN')
        self.assertTrue(str(RegioCompetitieSchutterBoog) != '')     # coverage only

        # geen bevestig formulier indien al ingeschreven
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        # 18m IB voor extra coverage
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='IB')
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Dutch Target')

        # schakel over naar de 25m1pijl, barebow
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='25', nhb_regio=self.nhbver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Dutch Target')

        # schrijf in voor de 25m BB, zonder AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)

        # veroorzaak een dubbele inschrijving
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)

    def test_bad(self):
        # inschrijven als anon
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # inschrijven als BB (niet NHB lid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # haal de bevestig pagina op als BB
        url = self.url_bevestig_aanmelden % (0, 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # inschrijven als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geenlid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)

        # illegaal deelcomp nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (99999, schutterboog.pk))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (999999, schutterboog.pk))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # illegaal schutterboog nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (99999, 'hallo'))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (999999, 'hallo'))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # schutterboog hoort niet bij gebruiker
        self.client.logout()
        self.e2e_login(self.account_twee)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # mismatch diverse zaken
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=NhbRegio.objects.get(regio_nr=116))
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_afmelden(self):
        # afmelden als anon
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 0)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # afmelden als BB (niet NHB lid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 0)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # afmelden als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geenlid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 0)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # aanmelden voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog_18 = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog_18, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog_18.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        inschrijving_18 = RegioCompetitieSchutterBoog.objects.all()[0]

        # aanmelden voor de 25m BB, zonder AG
        schutterboog_25 = SchutterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='25', nhb_regio=self.nhbver.regio)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog_25.pk))
        self.assert_is_redirect(resp, self.url_profiel)

        # afmelden van de 18m
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving_18.pk)
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        # illegaal inschrijving nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # niet bestaand inschrijving nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 'hoi')
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # schutterboog hoort niet bij gebruiker
        inschrijving_25 = RegioCompetitieSchutterBoog.objects.all()[0]
        self.client.logout()
        self.e2e_login(self.account_twee)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving_25.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_afmelden_geen_voorkeur_meer(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # aanmelden voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog_18 = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog_18, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog_18.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        inschrijving_18 = RegioCompetitieSchutterBoog.objects.all()[0]

        # voorkeur boogtype uitzetten
        schutterboog_18.voor_wedstrijd = False
        schutterboog_18.save()

        # afmelden van de 18m
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving_18.pk)
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

    def test_inschrijven_team(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf in voor de 18m Recurve, met AG
        # geef ook team schieten en opmerking door
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'yes', 'opmerking': 'Hallo daar!'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertFalse(inschrijving.is_handmatig_ag)
        self.assertEqual(str(inschrijving.aanvangsgemiddelde), "8.180")
        self.assertEqual(inschrijving.deelcompetitie, deelcomp)
        self.assertEqual(inschrijving.schutterboog, schutterboog)
        self.assertEqual(inschrijving.bij_vereniging, schutterboog.nhblid.bij_vereniging)
        self.assertTrue(inschrijving.inschrijf_voorkeur_team)
        self.assertEqual(inschrijving.inschrijf_notitie, 'Hallo daar!')
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'GN')

        # schrijf in voor de 25m BB, zonder AG, als aspriant
        self.nhblid1.geboorte_datum = datetime.date(year=timezone.now().year - 12, month=1, day=1)
        self.nhblid1.save()
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='25', nhb_regio=self.nhbver.regio)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog.pk),
                                    {'wil_in_team': 'ja', 'opmerking': 'ben ik oud genoeg?'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)

        inschrijving = RegioCompetitieSchutterBoog.objects.filter(schutterboog=schutterboog).all()[0]
        self.assertEqual(inschrijving.inschrijf_notitie, 'ben ik oud genoeg?')
        self.assertFalse(inschrijving.inschrijf_voorkeur_team)

    def test_team_udvl(self):
        # controleer dat het filter voor uiterste datum van lidmaatschap werkt

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        comp = Competitie.objects.get(afstand='18')
        #   nhblid1.sinds_datum = datetime.date(year=2010, month=11, day=12)
        comp.uiterste_datum_lid = datetime.date(year=2010, month=11, day=11)
        comp.save()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf in voor de 18m Recurve, met AG
        # geef ook team schieten en opmerking door
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'yes'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertEqual(inschrijving.deelcompetitie, deelcomp)
        self.assertEqual(inschrijving.schutterboog, schutterboog)
        self.assertEqual(inschrijving.bij_vereniging, schutterboog.nhblid.bij_vereniging)
        self.assertFalse(inschrijving.inschrijf_voorkeur_team)      # belangrijkste testresultaat

    def test_inschrijven_methode3_twee_dagdelen(self):
        regio_105 = NhbRegio.objects.get(pk=105)
        self.nhbver.regio = regio_105
        self.nhbver.save()

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=regio_105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = 'ZA,ZO'
        deelcomp.save()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf in voor de 18m Recurve, met AG
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Dutch Target')
        self.assertContains(resp, 'Zaterdag')
        self.assertContains(resp, 'Zondag')
        self.assertNotContains(resp, 's Avonds')
        self.assertNotContains(resp, 'Weekend')

        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # schrijf in met een niet toegestaan dagdeel
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'dagdeel': 'AV'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

        # schrijf in met dagdeel, team schieten en opmerking door
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'on',
                                          'dagdeel': 'ZA',
                                          'opmerking': 'Hallo nogmaals!\n' * 50})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertTrue(inschrijving.inschrijf_voorkeur_team)
        self.assertTrue(len(inschrijving.inschrijf_notitie) > 480)
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'ZA')

        # bad dagdeel
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'dagdeel': 'XX'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

    def test_inschrijven_methode3_alle_dagdelen(self):
        regio_105 = NhbRegio.objects.get(pk=105)
        self.nhbver.regio = regio_105
        self.nhbver.save()

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=regio_105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = ''   # alles toegestaan
        deelcomp.save()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf in voor de 18m Recurve, met AG
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Dutch Target')
        self.assertContains(resp, 'Zaterdag')
        self.assertContains(resp, 'Zondag')
        self.assertContains(resp, 's Avonds')
        self.assertContains(resp, 'Weekend')

        # geef dagdeel door
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'dagdeel': 'AV'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertFalse(inschrijving.inschrijf_voorkeur_team)
        self.assertEqual(inschrijving.inschrijf_notitie, '')
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'AV')

    def test_inschrijven_aspirant(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter met een leeftijd waarbij het mis kan gaan
        # huidige: 2020
        # geboren: 2007
        # bereikt leeftijd: 2020-2007 = 13
        # wedstrijdleeftijd 2020: 13 --> Aspirant 11-12
        # wedstrijdleeftijd 2021: 14 --> Cadet
        # als het programma het goed doet, komt de schutter dus in de cadetten klasse
        self.nhblid1.geboorte_datum = datetime.date(year=timezone.now().year - 13, month=1, day=1)
        self.nhblid1.save()
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Aspirant')
        self.assertContains(resp, 'Cadet')

        # probeer in te schrijven en controleer daarna de wedstrijdklasse waarin de schutter geplaatst is
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertEqual(inschrijving.deelcompetitie, deelcomp)
        self.assertEqual(inschrijving.schutterboog, schutterboog)

        klasse = inschrijving.klasse.indiv
        self.assertFalse('Aspirant' in klasse.beschrijving)
        self.assertTrue('Cadet' in klasse.beschrijving)
        self.assertFalse(klasse.buiten_gebruik)
        self.assertEqual(klasse.boogtype, schutterboog.boogtype)

# end of file
