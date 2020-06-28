# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils.dateparse import parse_date
from django.utils import timezone
from django.test import TestCase
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Records.models import IndivRecord
from Competitie.models import Competitie, DeelCompetitie, RegioCompetitieSchutterBoog
from Score.models import Score, ScoreHist, aanvangsgemiddelde_opslaan
from Overig.e2ehelpers import E2EHelpers
from .models import SchutterVoorkeuren, SchutterBoog
import datetime


class TestSchutterProfiel(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie, module Profiel """

    test_after = ('NhbStructuur', 'HistComp', 'Competitie', 'Schutter.regiocompetitie')

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

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

        # geef dit account een record
        rec = IndivRecord()
        rec.discipline = '18'
        rec.volg_nr = 1
        rec.soort_record = "60p"
        rec.geslacht = lid.geslacht
        rec.leeftijdscategorie = 'J'
        rec.materiaalklasse = "R"
        rec.nhb_lid = lid
        rec.naam = "Ramon de Tester"
        rec.datum = parse_date('2011-11-11')
        rec.plaats = "Top stad"
        rec.score = 293
        rec.max_score = 300
        rec.save()

        # geef dit account een goede en een slechte HistComp record
        histcomp = HistCompetitie()
        histcomp.seizoen = "2009/2010"
        histcomp.comp_type = "18"
        histcomp.klasse = "don't care"
        histcomp.save()

        indiv = HistCompetitieIndividueel()
        indiv.histcompetitie = histcomp
        indiv.rank = 1
        indiv.schutter_nr = 100001
        indiv.schutter_naam = "Ramon de Tester"
        indiv.boogtype = "R"
        indiv.vereniging_nr = 1000
        indiv.vereniging_naam = "don't care"
        indiv.score1 = 123
        indiv.score2 = 234
        indiv.score3 = 345
        indiv.score4 = 456
        indiv.score5 = 0
        indiv.score6 = 666
        indiv.score7 = 7
        indiv.laagste_score_nr = 7
        indiv.totaal = 1234
        indiv.gemiddelde = 9.123
        indiv.save()

        indiv.pk = None
        indiv.boogtype = "??"   # bestaat niet, on purpose
        indiv.save()

        self.boog_R = BoogType.objects.get(afkorting='R')

        self.url_profiel = '/schutter/'
        self.url_voorkeuren = '/schutter/voorkeuren/'
        self.url_inschrijven = '/schutter/regiocompetitie/inschrijven/%s/%s/'   # deelcomp_pk, schutterboog_pk
        self.url_bevestig_inschrijven = self.url_inschrijven + 'bevestig/'
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

        # zet de inschrijving open
        now = timezone.now()
        for comp in Competitie.objects.all():
            comp.begin_aanmeldingen = now.date()
            comp.save()
        # for

    def test_compleet(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()
        self.client.logout()

        # zonder login --> terug naar het plein
        resp = self.client.get(self.url_profiel)
        self.assert_is_redirect(resp, '/plein/')

        # log in as schutter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf de schutter in voor de 18m Recurve
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, '2020-01-01', None, 'Test')
        self.assertTrue(res)
        url = self.url_inschrijven % (deelcomp.pk, schutterboog.pk)
        resp = self.client.post(url, {'opmerking': 'test van de 18m'})
        self.assert_is_redirect(resp, self.url_profiel)

        inschrijving = RegioCompetitieSchutterBoog.objects.get(schutterboog=schutterboog)
        url_uitschrijven_18r = self.url_uitschrijven % inschrijving.pk

        deelcomp = DeelCompetitie.objects.get(competitie__afstand='25', nhb_regio=self.nhbver.regio)
        url_inschrijven_25r = self.url_bevestig_inschrijven % (deelcomp.pk, schutterboog.pk)

        # zet de barebow boog 'aan' en schrijf in voor 25m BB
        schutterboog_bb = SchutterBoog.objects.get(boogtype__afkorting='BB')
        schutterboog_bb.voor_wedstrijd = True
        schutterboog_bb.save()
        url = self.url_inschrijven % (deelcomp.pk, schutterboog_bb.pk)
        resp = self.client.post(url, {'wil_in_team': 'on'})
        self.assert_is_redirect(resp, self.url_profiel)
        schutterboog_bb.voor_wedstrijd = False
        schutterboog_bb.save()
        inschrijving = RegioCompetitieSchutterBoog.objects.get(schutterboog=schutterboog)
        url_uitschrijven_25bb = self.url_uitschrijven % inschrijving.pk

        # haal de profiel pagina op
        with self.assertNumQueries(24):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/profiel.dtl', 'plein/site_layout.dtl'))

        # check inschrijf en uitschrijf knoppen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(url_inschrijven_25r in urls)
        self.assertTrue(url_uitschrijven_18r in urls)
        self.assertTrue(url_uitschrijven_25bb in urls)

        # zet aanvangsgemiddelden voor 18m en 25m
        Score.objects.all().delete()        # nieuw vastgestelde AG is van vandaag
        obj = SchutterBoog.objects.get(boogtype__afkorting='R')
        datum = datetime.date(year=2020, month=5, day=2)
        datum_str = "2 mei 2020"
        aanvangsgemiddelde_opslaan(obj, 18, 9.018, datum, None, 'Test opmerking A')
        aanvangsgemiddelde_opslaan(obj, 25, 2.5, datum, None, 'Test opmerking B')

        resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertContains(resp, "2,500")
        self.assertContains(resp, "9,018")
        self.assertContains(resp, "Test opmerking A")
        self.assertContains(resp, "Test opmerking B")
        self.assertContains(resp, datum_str)

        # variant met Score zonder ScoreHist
        ScoreHist.objects.all().delete()
        resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_profiel)

    def test_geen_wedstrijdbogen(self):
        # geen regiocompetities op profiel indien geen wedstrijdbogen

        # log in as schutter
        self.e2e_login(self.account_normaal)
        # self._prep_voorkeuren()       --> niet aanroepen, dan geen schutterboog

        # haal de profiel pagina op
        with self.assertNumQueries(24):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/profiel.dtl', 'plein/site_layout.dtl'))

        # check record
        self.assertContains(resp, 'Top stad')

        # check scores
        self.assertContains(resp, '666')

        # check the competities (geen)
        self.assertNotContains(resp, 'Regiocompetities')

    def test_geen_voorkeur_competities(self):
        # toon geen regiocompetities als de schutter geen interesse heeft

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()
        self.client.logout()

        # zonder login --> terug naar het plein
        resp = self.client.get(self.url_profiel)
        self.assert_is_redirect(resp, '/plein/')

        # log in as schutter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # met standaard voorkeuren worden de regiocompetities getoond
        voorkeuren, _ = SchutterVoorkeuren.objects.get_or_create(nhblid=self.nhblid1)
        self.assertTrue(voorkeuren.voorkeur_meedoen_competitie)
        resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Regiocompetities')

        # uitgezet worden de regiocompetities niet getoond
        voorkeuren.voorkeur_meedoen_competitie = False
        voorkeuren.save()
        resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Regiocompetities')

        # schrijf de schutter in voor de 18m Recurve
        schutterboog = SchutterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='18', nhb_regio=self.nhbver.regio)
        res = aanvangsgemiddelde_opslaan(schutterboog, 18, 8.18, '2020-01-01', None, 'Test')
        self.assertTrue(res)
        url = self.url_inschrijven % (deelcomp.pk, schutterboog.pk)
        resp = self.client.post(url, {'opmerking': 'test van de 18m'})
        self.assert_is_redirect(resp, self.url_profiel)

        # voorkeur net uitgezet, maar nog wel ingeschreven
        resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Regiocompetities')


# end of file
