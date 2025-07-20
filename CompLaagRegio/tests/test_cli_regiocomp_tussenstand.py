# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_BK
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieMatch,
                               Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog,
                               Kampioenschap)
from Competitie.operations import competities_aanmaken, competitie_klassengrenzen_vaststellen
from Competitie.test_utils.tijdlijn import zet_competitie_fases
from Geo.models import Regio
from Score.definities import SCORE_WAARDE_VERWIJDERD
from Score.models import Score, ScoreHist
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime
import json
import time


class TestCompLaagRegioCliRegiocompTussenstand(E2EHelpers, TestCase):

    """ unittests voor de CompLaagRegio applicatie, management command regiocomp_tussenstand """

    url_planning_regio = '/bondscompetities/regio/planning/%s/'                  # deelcomp_pk
    url_planning_regio_ronde = '/bondscompetities/regio/planning/ronde/%s/'      # ronde_pk
    url_uitslag_invoeren = '/bondscompetities/scores/uitslag-invoeren/%s/'       # match_pk
    url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/'          # comp_pk
    url_uitslag_opslaan = '/bondscompetities/scores/dynamic/scores-opslaan/'

    def _maak_competitie_aan(self):
        # maak de competitie aan
        competities_aanmaken()

        self.comp = comp_18 = Competitie.objects.get(afstand='18')
        comp_25 = Competitie.objects.get(afstand='25')

        score_indiv_ag_opslaan(self.sporterboog_100005, 18, 9.500, None, "Test")

        # klassengrenzen vaststellen
        competitie_klassengrenzen_vaststellen(comp_18)
        competitie_klassengrenzen_vaststellen(comp_25)

        self.deelcomp_r101 = Regiocompetitie.objects.filter(competitie=self.comp,
                                                            regio=self.regio_101)[0]

        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        # wissel naar RCL functie
        self.e2e_wissel_naar_functie(self.deelcomp_r101.functie)

        # maak een regioplanning aan met 2 wedstrijden
        self.client.post(self.url_planning_regio % self.deelcomp_r101.pk)
        ronde = RegiocompetitieRonde.objects.first()

        # maak 7 wedstrijden aan
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})

        self.assertEqual(7, CompetitieMatch.objects.count())
        match_pks = CompetitieMatch.objects.all().values_list('pk', flat=True)

        # laat de wedstrijd.uitslag aanmaken en pas de wedstrijd nog wat aan
        self.uitslagen = list()
        uur = 1
        for match_pk in match_pks[:]:     # copy to ensure stable
            # maak de data set
            json_data = {'wedstrijd_pk': match_pk}
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_uitslag_opslaan,
                                        json.dumps(json_data),
                                        content_type='application/json')
            json_data = self.assert200_json(resp)
            self.assertEqual(json_data['done'], 1)

            match = CompetitieMatch.objects.get(pk=match_pk)
            self.assertIsNotNone(match.uitslag)
            match.vereniging = self.ver
            match.tijd_begin_wedstrijd = "%02d:00" % uur
            uur = (uur + 1) % 24
            match.save()
            self.uitslagen.append(match.uitslag)
        # for

        # maak nog een wedstrijd aan - die blijft zonder uitslag
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})

    def _maak_leden_aan(self):
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver)
        self.account_lid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_lid
        sporter.save()
        self.sporter_100001 = sporter

        sporterboog = SporterBoog(sporter=self.sporter_100001, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001 = sporterboog

        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="het Testertje",     # noqa
                    email="rdetestertje@test.not",
                    geboorte_datum=datetime.date(year=2008, month=3, day=4),
                    sinds_datum=datetime.date(year=2015, month=11, day=12),
                    bij_vereniging=self.ver)
        self.account_jeugdlid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_jeugdlid
        sporter.save()
        self.sporter_100002 = sporter

        sporterboog = SporterBoog(sporter=self.sporter_100002, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100002 = sporterboog

        sporter = Sporter(
                    lid_nr=100003,
                    geslacht="M",
                    voornaam="Geen",
                    achternaam="Vereniging",
                    email="geenver@test.not",
                    geboorte_datum=datetime.date(year=2008, month=3, day=4),
                    sinds_datum=datetime.date(year=2015, month=11, day=12))
        # lid.bij_vereniging =
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()

        sporter = Sporter(
                    lid_nr=100004,
                    geslacht="V",
                    voornaam="Juf",
                    achternaam="de Schutter",
                    email="jufschut@test.not",
                    geboorte_datum=datetime.date(year=1988, month=12, day=4),
                    sinds_datum=datetime.date(year=2015, month=7, day=15),
                    bij_vereniging=self.ver)
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()
        self.sporter_100004 = sporter

        sporterboog = SporterBoog(sporter=self.sporter_100004, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100004 = sporterboog

        sporter = Sporter(
                    lid_nr=100005,
                    geslacht="V",
                    voornaam="Jans",
                    achternaam="de Schutter",
                    email="jufschut@test.not",
                    geboorte_datum=datetime.date(year=1977, month=12, day=4),
                    sinds_datum=datetime.date(year=2015, month=7, day=15),
                    bij_vereniging=self.ver)
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()
        self.sporter_100005 = sporter

        sporterboog = SporterBoog(sporter=self.sporter_100005, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100005 = sporterboog

    @staticmethod
    def _schrijf_in_voor_competitie(deelcomp, sportersboog, skip=1):
        while len(sportersboog):
            sporterboog = sportersboog[0]

            # let op: de testen die een schutter doorschuiven vereisen dat schutter 100001 in klasse onbekend
            klassen = (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=deelcomp.competitie,
                               is_onbekend=(sporterboog.sporter.lid_nr == 100001),
                               boogtype=sporterboog.boogtype)
                       .order_by('volgorde'))

            aanmelding = RegiocompetitieSporterBoog(regiocompetitie=deelcomp,
                                                    sporterboog=sporterboog)
            aanmelding.bij_vereniging = aanmelding.sporterboog.sporter.bij_vereniging

            if len(sportersboog) < len(klassen):
                aanmelding.indiv_klasse = klassen[len(sportersboog)]
            else:
                aanmelding.indiv_klasse = klassen[0]
            aanmelding.save()

            sportersboog = sportersboog[skip:]
        # while

    def setUp(self):
        """ initialisatie van de test case """

        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = Regio.objects.get(regio_nr=101)
        self.boog_r = BoogType.objects.get(afkorting='R')

        # maak een BB aan, nodig om de competitie defaults in te zien
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    plaats="Boogstad",
                    ver_nr=1000,
                    regio=self.regio_101)
        ver.save()
        self.ver = ver

        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self._maak_leden_aan()
        self._maak_competitie_aan()

        # schrijf de leden in
        schuttersboog = [self.sporterboog_100001, self.sporterboog_100002,
                         self.sporterboog_100004, self.sporterboog_100005]
        self._schrijf_in_voor_competitie(self.deelcomp_r101, schuttersboog)

        self.functie_bko = Kampioenschap.objects.get(competitie=self.comp,
                                                     deel=DEEL_BK,
                                                     competitie__afstand=18).functie

        self.client.logout()

    @staticmethod
    def _score_opslaan(uitslag, sporterboog, waarde):
        score = Score(afstand_meter=18,
                      sporterboog=sporterboog,
                      waarde=waarde)
        score.save()

        hist = ScoreHist(score=score,
                         oude_waarde=0,
                         nieuwe_waarde=waarde)
        hist.save()

        uitslag.scores.add(score)

    def test_leeg(self):
        ScoreHist.objects.all().delete()
        Score.objects.all().delete()

        with self.assert_max_queries(115):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Klaar' in f2.getvalue())

    def test_twee(self):
        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.sporterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.sporterboog_100001, 124)

        with self.assert_max_queries(176):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        self.assertTrue('Scores voor 1 deelnemers bijgewerkt' in f2.getvalue())

        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_100001)
        self.assertEqual(deelnemer.score1, 123)
        self.assertEqual(deelnemer.score2, 124)
        self.assertEqual(deelnemer.score3, 0)
        self.assertEqual(deelnemer.totaal, 247)
        self.assertEqual(deelnemer.aantal_scores, 2)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.gemiddelde), '4.117')

        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (
        #           deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5,
        #           deelnemer.score6, deelnemer.score7,
        #           deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))

        # nog een keer - nu wordt er niets bijgewerkt omdat er geen nieuwe scores zijn
        with self.assert_max_queries(173):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        self.assertTrue('Scores voor 0 deelnemers bijgewerkt' in f2.getvalue())

        # nog een keer met 'all'
        with self.assert_max_queries(174):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick', '--all')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 deelnemers bijgewerkt' in f2.getvalue())

    def test_zeven(self):
        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.sporterboog_100001, 123)
        self._score_opslaan(self.uitslagen[1], self.sporterboog_100001, 124)
        self._score_opslaan(self.uitslagen[2], self.sporterboog_100001, 125)
        self._score_opslaan(self.uitslagen[3], self.sporterboog_100001, 126)
        self._score_opslaan(self.uitslagen[4], self.sporterboog_100001, 127)
        self._score_opslaan(self.uitslagen[5], self.sporterboog_100001, 128)
        self._score_opslaan(self.uitslagen[6], self.sporterboog_100001, 129)
        with self.assert_max_queries(182):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 deelnemers bijgewerkt' in f2.getvalue())

        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_100001)
        self.assertEqual(deelnemer.score1, 123)
        self.assertEqual(deelnemer.score7, 129)
        self.assertEqual(deelnemer.totaal, 759)
        self.assertEqual(deelnemer.aantal_scores, 7)
        self.assertEqual(deelnemer.laagste_score_nr, 1)
        self.assertEqual(str(deelnemer.gemiddelde), '4.217')

        # verwijder een schutter uit een uitslag door de score op VERWIJDERD te zetten
        score = ScoreHist.objects.latest('pk').score
        hist = ScoreHist(score=score,
                         oude_waarde=score.waarde,
                         nieuwe_waarde=SCORE_WAARDE_VERWIJDERD,
                         notitie="Foutje, bedankt!")
        hist.save()
        score.waarde = SCORE_WAARDE_VERWIJDERD
        score.save()

        with self.assert_max_queries(176):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 deelnemers bijgewerkt' in f2.getvalue())

        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_100001)
        self.assertEqual(deelnemer.score1, 123)
        self.assertEqual(deelnemer.score6, 128)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 753)
        self.assertEqual(deelnemer.aantal_scores, 6)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.gemiddelde), '4.183')

    def test_verplaats(self):
        # check het verplaatsen van een schutter uit klasse onbekend

        deelnemer = RegiocompetitieSporterBoog.objects.filter(sporterboog=self.sporterboog_100001)[0]
        self.assertTrue(deelnemer.indiv_klasse.is_onbekend)

        # 100001: 4 scores, gebruik eerste 3
        # 100002: nog maar 2 scores
        # 100004: Al in hogere klasse geplaatst
        # 100005: AG > 0.001

        # verplaats 100004 naar Recurve klasse 4, Senioren Vrouwen
        # zodat deze straks niet verplaatst hoeft te worden
        klasse = None
        for obj in (CompetitieIndivKlasse               # pragma: no branch
                    .objects
                    .filter(competitie=self.comp,
                            is_onbekend=False,
                            boogtype__afkorting=self.boog_r.afkorting)
                    .prefetch_related('leeftijdsklassen')):

            if obj.leeftijdsklassen.filter(afkorting='SA').count() > 0:     # pragma: no branch
                klasse = obj
                break
        # for

        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_100004)
        deelnemer.indiv_klasse = klasse
        deelnemer.save()

        # pas het AG van 100005 aan
        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_100005)
        deelnemer.aanvangsgemiddelde = 9.000
        deelnemer.save()

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.sporterboog_100001, 123)
        self._score_opslaan(self.uitslagen[1], self.sporterboog_100001, 124)
        self._score_opslaan(self.uitslagen[3], self.sporterboog_100001, 128)
        self._score_opslaan(self.uitslagen[4], self.sporterboog_100001, 120)

        self._score_opslaan(self.uitslagen[0], self.sporterboog_100002, 123)
        self._score_opslaan(self.uitslagen[2], self.sporterboog_100002, 124)

        self._score_opslaan(self.uitslagen[0], self.sporterboog_100004, 123)
        self._score_opslaan(self.uitslagen[2], self.sporterboog_100004, 124)
        self._score_opslaan(self.uitslagen[3], self.sporterboog_100004, 128)

        self._score_opslaan(self.uitslagen[4], self.sporterboog_100005, 128)

        with self.assert_max_queries(191):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[INFO] Verplaats 100001 (18m) met nieuw AG 4.167 naar klasse Recurve klasse' in f2.getvalue())

    def test_verplaats_zeven(self):
        # check het verplaatsen van een schutter uit klasse onbekend

        deelnemer = RegiocompetitieSporterBoog.objects.filter(sporterboog=self.sporterboog_100001)[0]
        # print('deelnemer: %s (leeftijd: %s)' % (deelnemer, deelnemer.sporterboog.sporter.geboorte_datum))
        self.assertTrue(deelnemer.indiv_klasse.is_onbekend)
        # print('huidige klasse: %s (pk=%s)' % (deelnemer.indiv_klasse, deelnemer.indiv_klasse.pk))

        # 100001: 7 scores, gebruik eerste 3 voor bepalen AG voor overstap
        self._score_opslaan(self.uitslagen[0], self.sporterboog_100001, 123)
        self._score_opslaan(self.uitslagen[1], self.sporterboog_100001, 124)
        self._score_opslaan(self.uitslagen[2], self.sporterboog_100001, 125)
        self._score_opslaan(self.uitslagen[3], self.sporterboog_100001, 122)
        self._score_opslaan(self.uitslagen[4], self.sporterboog_100001, 121)
        self._score_opslaan(self.uitslagen[5], self.sporterboog_100001, 129)
        self._score_opslaan(self.uitslagen[6], self.sporterboog_100001, 128)

        with self.assert_max_queries(182):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[INFO] Verplaats 100001 (18m) met nieuw AG 4.133 naar klasse Recurve klasse' in f2.getvalue())

    def test_overstap(self):
        # test schutters die overstappen naar een andere vereniging

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.sporterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.sporterboog_100001, 124)

        with self.assert_max_queries(176):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        self.assertTrue('Scores voor 1 deelnemers bijgewerkt' in f2.getvalue())

        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_100001)
        self.assertEqual(deelnemer.bij_vereniging.ver_nr, self.ver.ver_nr)
        sporter = self.sporterboog_100001.sporter

        # zet de sporter tijdelijk 'zwevend', ook al voorkomt de CRM import deze situatie tegenwoordig
        sporter.bij_vereniging = None
        sporter.save(update_fields=['bij_vereniging'])

        with self.assert_max_queries(174):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--all', '--quick')
        self.assertFalse("[INFO] Verwerk overstap" in f2.getvalue())

        # maak een tweede vereniging aan
        regio_116 = Regio.objects.get(regio_nr=116)
        ver = Vereniging(
                    naam="Zuidelijke Club",
                    plaats="Grensstad",
                    ver_nr=1100,
                    regio=regio_116)
        ver.save()

        sporter.bij_vereniging = ver
        sporter.save(update_fields=['bij_vereniging'])

        with self.assert_max_queries(178):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        self.assertTrue("[INFO] Verwerk overstap 100001: [101] [1000] Grote Club --> [116] [1100] Zuidelijke Club"
                        in f2.getvalue())

        # overstap naar vereniging in zelfde regio
        self.ver.regio = regio_116
        self.ver.save()
        sporter.bij_vereniging = self.ver
        sporter.save(update_fields=['bij_vereniging'])

        with self.assert_max_queries(178):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        self.assertTrue("[INFO] Verwerk overstap 100001: [116] [1100] Zuidelijke Club --> [116] [1000] Grote Club"
                        in f2.getvalue())

        # zet the competitie in een later fase zodat overschrijvingen niet meer gedaan worden
        for comp in Competitie.objects.all():
            zet_competitie_fases(comp, 'K', 'K')
            comp.bepaal_fase()
            self.assertEqual(comp.fase_indiv, 'K')
        # for
        sporter.bij_vereniging = ver
        sporter.save()
        with self.assert_max_queries(173):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('Verwerk overstap' in f2.getvalue())

    def test_uitstap(self):
        # schutter schrijft zich uit

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.sporterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.sporterboog_100001, 124)
        with self.assert_max_queries(176):
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '2', '--quick')
        self.assertTrue('Scores voor 1 deelnemers bijgewerkt' in f2.getvalue())

        # schrijf een schutter uit
        sporter = self.sporterboog_100001.sporter
        sporter.bij_vereniging = None
        sporter.save()
        with self.assert_max_queries(176, check_duration=False):        # 7 seconden is boven de limiet
            f1, f2 = self.run_management_command('regiocomp_tussenstand', '7', '--quick')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        # controleer dat de sporter op zijn oude vereniging blijft staan
        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog__sporter__lid_nr=100001)
        self.assertIsNone(deelnemer.sporterboog.sporter.bij_vereniging)
        self.assertIsNotNone(deelnemer.bij_vereniging)

    def test_stop_exactly(self):
        now = datetime.datetime.now()
        if now.minute == 0:                             # pragma: no cover
            print('Waiting until clock is past xx:00 .. ', end='')
            while now.minute == 0:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        now = datetime.datetime.now()
        if now.second > 55:                             # pragma: no cover
            print('Waiting until clock is past xx:xx:59 .. ', end='')
            while now.second > 55:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the current minute
        f1, f2 = self.run_management_command('regiocomp_tussenstand', '1', '--quick',
                                             '--stop_exactly=%s' % now.minute)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # trigger the negative case
        f1, f2 = self.run_management_command('regiocomp_tussenstand', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute - 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        now = datetime.datetime.now()
        if now.minute == 59:                             # pragma: no cover
            print('Waiting until clock is past xx:59 .. ', end='')
            while now.minute == 59:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the positive case
        f1, f2 = self.run_management_command('regiocomp_tussenstand', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute + 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

    # TODO: test garantie dat overstapper na fase G niet meer verwerkt wordt en vereniging voor RK rayon bevroren is

# end of file
