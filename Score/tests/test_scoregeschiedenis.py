# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, CompetitieMatch
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Score.definities import SCORE_WAARDE_VERWIJDERD, SCORE_TYPE_GEEN
from Score.models import Score, ScoreHist, Uitslag
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestScoreGeschiedenis(E2EHelpers, TestCase):

    """ tests voor de Score applicatie, functie Score Geschiedenis """

    url_geschiedenis = '/score/geschiedenis/'

    def _maak_uitslag(self, sporterboog):
        # maak 2x wedstrijd + uitslag + score voor deze sporter-boog, met geschiedenis
        uur_00 = datetime.time(hour=0)
        uur_19 = datetime.time(hour=19)

        uitslag18 = Uitslag(max_score=300,
                            afstand=18)
        uitslag18.save()

        uitslag25 = Uitslag(max_score=250,
                            afstand=25)
        uitslag25.save()

        comp = Competitie(
                    begin_jaar=2000)
        comp.save()

        CompetitieMatch(competitie=comp,
                        beschrijving='Test wedstrijdje 18m',
                        datum_wanneer=datetime.date(year=2020, month=10, day=10),
                        tijd_begin_wedstrijd=uur_19,
                        uitslag=uitslag18,
                        vereniging=self.ver1).save()

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
        # niet in een uitslag stoppen
        # uitslag18.scores.add(score)

        score = Score(sporterboog=sporterboog,
                      afstand_meter=18,
                      waarde=289)
        score.save()
        ScoreHist(score=score,
                  oude_waarde=260,
                  nieuwe_waarde=289,
                  door_account=self.account_hwl).save()
        uitslag18.scores.add(score)

        # verwijderde score
        score = Score(sporterboog=sporterboog,
                      afstand_meter=18,
                      waarde=SCORE_WAARDE_VERWIJDERD)
        score.save()
        ScoreHist(score=score,
                  oude_waarde=289,
                  nieuwe_waarde=SCORE_WAARDE_VERWIJDERD,
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
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

        self.functie_hwl = maak_functie('HWL 1000', 'HWL')
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_hwl)

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_normaal,
                    email=self.account_normaal.email)
        sporter.save()
        self.sporter_100001 = sporter

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.boog_c = BoogType.objects.get(afkorting='C')

        # maak 2 sporter-boog aan
        sporterboog = SporterBoog(sporter=sporter, boogtype=self.boog_c, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001c = sporterboog

        sporterboog = SporterBoog(sporter=sporter, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001r = sporterboog

        # maak een AG aan
        score_indiv_ag_opslaan(sporterboog, 30, 8.123, None, 'raar')        # geeft extra coverage
        score_indiv_ag_opslaan(sporterboog, 18, 9.123, None, 'test melding')

        score_indiv_ag_opslaan(sporterboog, 25, 9.251, self.account_hwl, 'test melding')
        score_indiv_ag_opslaan(sporterboog, 25, 9.152, self.account_hwl, 'correctie')

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

        uitslag = Uitslag.objects.first()
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

        score = Score.objects.first()
        self.assertTrue(str(score) != '')

        score.type = SCORE_TYPE_GEEN
        self.assertTrue('(geen score)' in str(score))

        hist = ScoreHist.objects.first()
        self.assertTrue(str(hist) != '')

        hist = ScoreHist.objects.filter(score__sporterboog__sporter=self.sporter_100001)[0]
        hist.door_account = None
        hist.save(update_fields=['door_account'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))

    def test_zoek_bad(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        url = self.url_geschiedenis + '?zoekterm=999999'
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
