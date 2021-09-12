# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Functie.models import maak_functie
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, SCORE_WAARDE_VERWIJDERD
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdUitslag
from .operations import score_indiv_ag_opslaan
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestScoreGeschiedenis(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie, module Voorkeuren """

    url_geschiedenis = '/score/geschiedenis/'

    def _maak_uitslag(self, schutterboog):
        # maak 2x wedstrijd + uitslag + score voor deze schutterboog, met geschiedenis
        uur_00 = datetime.time(hour=0)
        uur_18 = datetime.time(hour=18)
        uur_19 = datetime.time(hour=19)
        uur_22 = datetime.time(hour=22)

        uitslag18 = CompetitieWedstrijdUitslag(max_score=300,
                                               afstand_meter=18)
        uitslag18.save()

        uitslag25 = CompetitieWedstrijdUitslag(max_score=250,
                                               afstand_meter=25)
        uitslag25.save()

        CompetitieWedstrijd(beschrijving='Test wedstrijdje 18m',
                            datum_wanneer=datetime.date(year=2020, month=10, day=10),
                            tijd_begin_aanmelden=uur_18,
                            tijd_begin_wedstrijd=uur_19,
                            tijd_einde_wedstrijd=uur_22,
                            uitslag=uitslag18,
                            vereniging=self.nhbver1).save()

        CompetitieWedstrijd(beschrijving='Test wedstrijdje 25m',
                            datum_wanneer=datetime.date(year=2020, month=10, day=11),
                            tijd_begin_aanmelden=uur_00,
                            tijd_begin_wedstrijd=uur_00,
                            tijd_einde_wedstrijd=uur_00,
                            uitslag=uitslag25).save()

        score = Score(schutterboog=schutterboog,
                      afstand_meter=18,
                      waarde=260)
        score.save()
        ScoreHist(score=score,
                  oude_waarde=0,
                  nieuwe_waarde=290,
                  door_account=self.account_hwl).save()
        ScoreHist(score=score,
                  oude_waarde=290,
                  nieuwe_waarde=260,
                  door_account=self.account_hwl).save()
        uitslag18.scores.add(score)

        score = Score(schutterboog=schutterboog,
                      afstand_meter=25,
                      waarde=234)
        score.save()
        ScoreHist(score=score,
                  oude_waarde=SCORE_WAARDE_VERWIJDERD,
                  nieuwe_waarde=234,
                  door_account=self.account_hwl).save()
        ScoreHist(score=score,
                  oude_waarde=0,
                  nieuwe_waarde=SCORE_WAARDE_VERWIJDERD,
                  door_account=self.account_hwl).save()
        ScoreHist(score=score,
                  oude_waarde=0,
                  nieuwe_waarde=1,
                  door_account=self.account_hwl).save()
        uitslag25.scores.add(score)

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_hwl = self.e2e_create_account('hwl', 'hwl@test.com', 'Secretaris')
        self.e2e_account_accepteert_vhpg(self.account_hwl)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        ver.save()
        self.nhbver1 = ver

        self.functie_hwl = maak_functie('HWL 1000', 'HWL')
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_hwl)

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

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.boog_c = BoogType.objects.get(afkorting='C')

        # maak 2 schutterboog aan
        schutterboog = SchutterBoog(nhblid=lid, boogtype=self.boog_c, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100001c = schutterboog

        schutterboog = SchutterBoog(nhblid=lid, boogtype=self.boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100001r = schutterboog

        # maak een AG aan
        score_indiv_ag_opslaan(schutterboog, 18, 9.123, None, 'test melding')

        score_indiv_ag_opslaan(schutterboog, 25, 9.251, self.account_hwl, 'test melding')

        self._maak_uitslag(schutterboog)

    def test_mag_niet(self):
        # moet BB zijn om de geschiedenis in te mogen zien
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_geschiedenis)
        self.assert403(resp)

    def test_bb(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_geschiedenis)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))

    def test_zoek(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        url = self.url_geschiedenis + '?zoekterm=%s' % self.nhblid1.nhb_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, self.nhblid1.volledige_naam())
        self.assertContains(resp, 'Recurve')
        self.assertContains(resp, 'Aanvangsgemiddelde')
        self.assertContains(resp, 'test melding')

    def test_zoek_bad(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        url = self.url_geschiedenis + '?zoekterm=999999'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Niets gevonden')

        url = self.url_geschiedenis + '?zoekterm=xx'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

# end of file
