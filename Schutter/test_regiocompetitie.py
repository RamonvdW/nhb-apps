# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import (Competitie, DeelCompetitie, RegioCompetitieSchutterBoog,
                               DeelcompetitieRonde, INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3)
from Competitie.test_fase import zet_competitie_fase
from Competitie.test_competitie import maak_competities_en_zet_fase_b, competities_aanmaken
from Functie.models import Functie
from Overig.e2ehelpers import E2EHelpers
from Score.models import Score, ScoreHist, SCORE_TYPE_INDIV_AG
from Score.operations import score_indiv_ag_opslaan
from Wedstrijden.models import CompetitieWedstrijd
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
        lid.account = self.account_geenlid
        lid.email = lid.account.email
        lid.save()

        self.url_profiel = '/sporter/'
        self.url_voorkeuren = '/sporter/voorkeuren/'
        self.url_aanmelden = '/sporter/regiocompetitie/aanmelden/%s/%s/'         # deelcomp_pk, schutterboog_pk
        self.url_bevestig_aanmelden = self.url_aanmelden + 'bevestig/'
        self.url_afmelden = '/sporter/regiocompetitie/afmelden/%s/'              # regiocomp_pk
        self.url_schietmomenten = '/sporter/regiocompetitie/%s/schietmomenten/'  # deelnemer_pk
        self.url_planning_regio = '/bondscompetities/planning/regio/%s/'         # deelcomp_pk
        self.url_planning_regio_ronde_methode1 = '/bondscompetities/planning/regio/regio-wedstrijden/%s/'  # ronde_pk
        self.url_wijzig_wedstrijd = '/bondscompetities/planning/regio/wedstrijd/wijzig/%s/'                # wedstrijd_pk
        self.url_inschrijven_hwl = '/vereniging/leden-aanmelden/competitie/%s/'  # comp_pk

    def _prep_voorkeuren(self, nhb_nr):
        # haal de voorkeuren op - hiermee worden de SchutterBoog records aangemaakt
        with self.assert_max_queries(20):
            self.client.get(self.url_voorkeuren)

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R', nhblid__nhb_nr=nhb_nr)
        schutterboog.voor_wedstrijd = True
        schutterboog.heeft_interesse = False
        schutterboog.save()

        for boog in ('C', 'IB', 'LB'):
            schutterboog = SchutterBoog.objects.get(boogtype__afkorting=boog, nhblid__nhb_nr=nhb_nr)
            schutterboog.heeft_interesse = False
            schutterboog.save()
        # for

    def _competitie_aanmaken(self):
        maak_competities_en_zet_fase_b()

    def test_inschrijven(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = score_indiv_ag_opslaan(schutterboog, 18, 8.18, None, 'Test')
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
        self.assertEqual(str(inschrijving.ag_voor_indiv), "8.180")
        self.assertEqual(str(inschrijving.ag_voor_team), "8.180")
        self.assertFalse(inschrijving.ag_voor_team_mag_aangepast_worden)
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
        self.assert404(resp)     # 404 = Not found
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

        # uitzondering: AG score zonder hist
        res = score_indiv_ag_opslaan(schutterboog, 18, 7.18, None, 'Test 2')
        self.assertTrue(res)
        scores = Score.objects.filter(schutterboog=schutterboog,
                                      type=SCORE_TYPE_INDIV_AG,
                                      afstand_meter=deelcomp.competitie.afstand)
        ScoreHist.objects.filter(score=scores[0]).delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))

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
        self.assert404(resp)     # 404 = Not found
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)

        # competitie in verkeerde fase
        comp = deelcomp.competitie    # Competitie.objects.get(pk=deelcomp.competitie.pk)
        zet_competitie_fase(comp, 'K')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assert404(resp)     # 404 = Not found

    def test_bad(self):
        # inschrijven als anon
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assert404(resp)     # 404 = Not found

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # inschrijven als BB (niet NHB lid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assert404(resp)     # 404 = Not found

        # haal de bevestig pagina op als BB
        url = self.url_bevestig_aanmelden % (0, 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # inschrijven als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geenlid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assert404(resp)     # 404 = Not found

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)

        # illegaal deelcomp nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (99999, schutterboog.pk))
        self.assert404(resp)     # 404 = Not found
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (999999, schutterboog.pk))
        self.assert404(resp)     # 404 = Not found

        # illegaal schutterboog nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (99999, 'hallo'))
        self.assert404(resp)     # 404 = Not found
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (999999, 'hallo'))
        self.assert404(resp)     # 404 = Not found

        # schutterboog hoort niet bij gebruiker
        self.client.logout()
        self.e2e_login(self.account_twee)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assert404(resp)     # 404 = Not found

        # mismatch diverse zaken
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=NhbRegio.objects.get(regio_nr=116))
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk))
        self.assert404(resp)     # 404 = Not found

        # schietmomenten
        url = self.url_schietmomenten % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

    def test_afmelden(self):
        # afmelden als anon
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 0)
        self.assert404(resp)     # 404 = Not found

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # afmelden als BB (niet NHB lid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 0)
        self.assert404(resp)     # 404 = Not found

        # afmelden als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geenlid)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 0)
        self.assert404(resp)     # 404 = Not found

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # aanmelden voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog_18 = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = score_indiv_ag_opslaan(schutterboog_18, 18, 8.18, None, 'Test')
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
        self.assert404(resp)     # 404 = Not found

        # niet bestaand inschrijving nummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 'hoi')
        self.assert404(resp)     # 404 = Not found

        # schutterboog hoort niet bij gebruiker
        inschrijving_25 = RegioCompetitieSchutterBoog.objects.all()[0]
        self.client.logout()
        self.e2e_login(self.account_twee)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving_25.pk)
        self.assert403(resp)

    def test_afmelden_geen_voorkeur_meer(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # aanmelden voor de 18m Recurve, met AG
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog_18 = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = score_indiv_ag_opslaan(schutterboog_18, 18, 8.18, None, 'Test')
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
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        # geef ook team schieten en opmerking door
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = score_indiv_ag_opslaan(schutterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'yes', 'opmerking': 'Hallo daar!'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertEqual(str(inschrijving.ag_voor_indiv), "8.180")
        self.assertEqual(str(inschrijving.ag_voor_team), "8.180")
        self.assertFalse(inschrijving.ag_voor_team_mag_aangepast_worden)
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
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        # geef ook team schieten en opmerking door
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = score_indiv_ag_opslaan(schutterboog, 18, 8.18, None, 'Test')
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
        deelcomp.toegestane_dagdelen = 'ZAT,ZOm'
        deelcomp.save()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

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
        self.assertContains(resp, 'Zondagmiddag')
        self.assertNotContains(resp, 's Avonds')
        self.assertNotContains(resp, 'Weekend')

        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        res = score_indiv_ag_opslaan(schutterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # schrijf in met een niet toegestaan dagdeel
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'dagdeel': 'AV'})
        self.assert404(resp)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

        # schrijf in met dagdeel, team schieten en opmerking door
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'on',
                                          'dagdeel': 'ZAT',
                                          'opmerking': 'Hallo nogmaals!\n' * 50})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertTrue(inschrijving.inschrijf_voorkeur_team)
        self.assertTrue(len(inschrijving.inschrijf_notitie) > 480)
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'ZAT')

        # bad dagdeel
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'dagdeel': 'XX'})
        self.assert404(resp)     # 404 = Not allowed
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
        self._prep_voorkeuren(100001)

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
        res = score_indiv_ag_opslaan(schutterboog, 18, 8.18, None, 'Test')
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

        self.assertEqual(str(inschrijving.ag_voor_indiv), "8.180")
        self.assertEqual(str(inschrijving.ag_voor_team), "8.180")
        self.assertFalse(inschrijving.ag_voor_team_mag_aangepast_worden)

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
        self.nhblid1.geboorte_datum = datetime.date(year=timezone.now().year - 13, month=1, day=2)
        self.nhblid1.save()
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

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

    def test_inschrijven_methode1(self):
        regio_101 = NhbRegio.objects.get(pk=101)
        self.nhbver.regio = regio_101
        self.nhbver.save()

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=regio_101)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        # maak een aantal wedstrijden aan, als RCL van Regio 101
        functie_rcl101 = Functie.objects.get(rol='RCL', comp_type='18', nhb_regio=regio_101)
        self.e2e_wissel_naar_functie(functie_rcl101)

        url = self.url_planning_regio % deelcomp.pk

        # haal de (lege) planning op. Dit maakt ook meteen de enige ronde aan
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # converteer de enige ronde naar een import ronde
        ronde_oud = DeelcompetitieRonde.objects.filter(deelcompetitie=deelcomp)[0]
        ronde_oud.beschrijving = "Ronde 42 oude programma"
        ronde_oud.save()

        # haal de planning op (maakt opnieuw een ronde aan)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        ronde_pk = DeelcompetitieRonde.objects.exclude(pk=ronde_oud.pk).filter(deelcompetitie=deelcomp)[0].pk

        # haal de ronde planning op
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url_ronde)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # maak een wedstrijd aan
        self.assertEqual(CompetitieWedstrijd.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)

        wedstrijd_pk = CompetitieWedstrijd.objects.all()[0].pk

        # wijzig de instellingen van deze wedstrijd
        url_wed = self.url_wijzig_wedstrijd % wedstrijd_pk
        with self.assert_max_queries(26):
            resp = self.client.post(url_wed, {'nhbver_pk': self.nhbver.pk,
                                              'wanneer': '2020-12-11', 'aanvang': '12:34'})
        self.assert_is_redirect(resp, url_ronde)

        # maak nog een paar wedstrijden aan (voor later gebruik)
        for lp in range(7):
            with self.assert_max_queries(20):
                resp = self.client.post(url_ronde)
            self.assert_is_redirect_not_plein(resp)
        # for

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Dutch Target')
        self.assertContains(resp, 'Kies wanneer je wilt schieten')
        self.assertContains(resp, '11 december 2020 om 12:34')

        # special: zet het vastgestelde AG op 0.000
        score_indiv_ag_opslaan(schutterboog, 18, 0.0, None, 'Test')

        # doe de inschrijving
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % wedstrijd_pk: 'on',
                                          'wedstrijd_99999': 'on'})     # is ignored
        self.assert_is_redirect(resp, self.url_profiel)

        aanmelding = RegioCompetitieSchutterBoog.objects.get(schutterboog=schutterboog)
        self.assertEqual(aanmelding.ag_voor_indiv, 0.0)
        self.assertEqual(aanmelding.ag_voor_team, 0.0)
        self.assertTrue(aanmelding.ag_voor_team_mag_aangepast_worden)

        # doe nog een inschrijving
        self.e2e_login(self.account_twee)
        self._prep_voorkeuren(100002)

        schutterboog2 = SchutterBoog.objects.get(nhblid__nhb_nr=100002, boogtype__afkorting='R')

        # doe de inschrijving
        url = self.url_aanmelden % (deelcomp.pk, schutterboog2.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % wedstrijd_pk: 'on'})
        self.assert_is_redirect(resp, self.url_profiel)

        aanmelding2 = RegioCompetitieSchutterBoog.objects.get(schutterboog=schutterboog2)

        # terug naar de eerste sporter
        self.e2e_login(self.account_normaal)

        # probeer de schietmomenten van een andere schutter aan te passen
        url = self.url_schietmomenten % aanmelding2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # pas de schietmomenten aan
        url = self.url_schietmomenten % aanmelding.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/schietmomenten.dtl', 'plein/site_layout.dtl'))

        # wedstrijd behouden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % wedstrijd_pk: 'on'})
        self.assert_is_redirect(resp, self.url_profiel)

        # wedstrijd verwijderen
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_profiel)

        # wedstrijd toevoegen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % wedstrijd_pk: 'on'})
        self.assert_is_redirect(resp, self.url_profiel)

        # te veel wedstrijden toevoegen
        args = dict()
        for obj in CompetitieWedstrijd.objects.all():
            args['wedstrijd_%s' % obj.pk] = 'on'
        # for
        with self.assert_max_queries(20):
            resp = self.client.post(url, args)
        self.assert_is_redirect(resp, self.url_profiel)

        # bad deelnemer_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_schietmomenten % 999999)
        self.assert404(resp)

        # special: probeer inschrijving met competitie in verkeerde fase
        zet_competitie_fase(deelcomp.competitie, 'K')
        url = self.url_aanmelden % (deelcomp.pk, schutterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % wedstrijd_pk: 'on'})
        self.assert404(resp)

# end of file
