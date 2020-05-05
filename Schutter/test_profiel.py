# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils.dateparse import parse_date
from django.test import TestCase
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Records.models import IndivRecord
from Competitie.models import DeelCompetitie, RegioCompetitieSchutterBoog
from Score.models import aanvangsgemiddelde_opslaan
from Overig.e2ehelpers import E2EHelpers
from .models import SchutterBoog
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
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_normaal
        lid.save()

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

    def test_profiel_compleet(self):
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
        resp = self.client.post(self.url_inschrijven % (deelcomp.pk, schutterboog.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        inschrijving = RegioCompetitieSchutterBoog.objects.get(schutterboog=schutterboog)
        url_uitschrijven_18r = self.url_uitschrijven % inschrijving

        # zet de BB tijdelijk 'aan' en schrijf in voor 25m BB
        deelcomp = DeelCompetitie.objects.get(competitie__afstand='25', nhb_regio=self.nhbver.regio)
        url_inschrijven_25r = self.url_inschrijven % (deelcomp.pk, schutterboog.pk)
        schutterboog_bb = SchutterBoog.objects.get(boogtype__afkorting='BB')
        schutterboog_bb.voor_wedstrijd = True
        schutterboog_bb.save()
        resp = self.client.post(self.url_inschrijven % (deelcomp.pk, schutterboog_bb.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        schutterboog_bb.voor_wedstrijd = False
        schutterboog_bb.save()
        inschrijving = RegioCompetitieSchutterBoog.objects.get(schutterboog=schutterboog)
        url_inschrijven_25bb = self.url_uitschrijven % inschrijving

        # haal de profiel pagina op
        resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/profiel.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(self.url_profiel)

        # check inschrijf en uitschrijf knoppen
        urls = self.extract_all_urls(resp)
        self.assertTrue(url_inschrijven_25r in urls)
        self.assertTrue(url_uitschrijven_18r in urls)
        self.assertTrue(url_uitschrijven_25bb in urls)

    def test_profile_geen_competities(self):

        # log in as schutter
        self.e2e_login(self.account_normaal)
        # self._prep_voorkeuren()       --> niet aanroepen, dan geen schutterboog

        # haal de profiel pagina op
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


# end of file
