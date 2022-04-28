# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Competitie.models import Competitie, CompetitieMatch
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from .models import Score, ScoreHist, Uitslag, SCORE_WAARDE_VERWIJDERD
from .operations import score_indiv_ag_opslaan
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestScoreGeschiedenis(E2EHelpers, TestCase):

    """ tests voor de Score applicatie, functie Score Geschiedenis """

    url_geschiedenis = '/score/geschiedenis/'

    def _maak_uitslag(self, sporterboog):
        # maak 2x wedstrijd + uitslag + score voor deze schutterboog, met geschiedenis
        uur_00 = datetime.time(hour=0)
        uur_19 = datetime.time(hour=19)

        now = timezone.now()
        einde_jaar = datetime.date(year=now.year, month=12, day=31)

        uitslag18 = Uitslag(max_score=300,
                            afstand=18)
        uitslag18.save()

        uitslag25 = Uitslag(max_score=250,
                            afstand=25)
        uitslag25.save()

        comp = Competitie(
                    begin_jaar=2000,
                    uiterste_datum_lid=datetime.date(year=2000, month=1, day=1),
                    begin_aanmeldingen=einde_jaar,
                    einde_aanmeldingen=einde_jaar,
                    einde_teamvorming=einde_jaar,
                    eerste_wedstrijd=einde_jaar,
                    laatst_mogelijke_wedstrijd=einde_jaar,
                    datum_klassengrenzen_rk_bk_teams=einde_jaar,
                    rk_eerste_wedstrijd=einde_jaar,
                    rk_laatste_wedstrijd=einde_jaar,
                    bk_eerste_wedstrijd=einde_jaar,
                    bk_laatste_wedstrijd=einde_jaar)
        comp.save()

        CompetitieMatch(competitie=comp,
                        beschrijving='Test wedstrijdje 18m',
                        datum_wanneer=datetime.date(year=2020, month=10, day=10),
                        tijd_begin_wedstrijd=uur_19,
                        uitslag=uitslag18,
                        vereniging=self.nhbver1).save()

        CompetitieMatch(competitie=comp,
                        beschrijving='Test wedstrijdje 25m',
                        datum_wanneer=datetime.date(year=2020, month=10, day=11),
                        tijd_begin_wedstrijd=uur_00,
                        uitslag=uitslag25).save()

        score = Score(sporterboog=sporterboog,
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

        score = Score(sporterboog=sporterboog,
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
        self.sporter_100001 = sporter

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.boog_c = BoogType.objects.get(afkorting='C')

        # maak 2 schutterboog aan
        sporterboog = SporterBoog(sporter=sporter, boogtype=self.boog_c, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001c = sporterboog

        sporterboog = SporterBoog(sporter=sporter, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001r = sporterboog

        # maak een AG aan
        score_indiv_ag_opslaan(sporterboog, 18, 9.123, None, 'test melding')

        score_indiv_ag_opslaan(sporterboog, 25, 9.251, self.account_hwl, 'test melding')

        self._maak_uitslag(sporterboog)

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

        uitslag = Uitslag.objects.all()[0]
        self.assertTrue(str(uitslag) != '')
        uitslag.is_bevroren = True
        self.assertTrue(str(uitslag) != '')

    def test_zoek(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        url = self.url_geschiedenis + '?zoekterm=%s' % self.sporter_100001.lid_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, self.sporter_100001.volledige_naam())
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
