# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, DeelCompetitie, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog, KampioenschapSchutterBoog,
                               LAAG_REGIO, LAAG_BK)
from Competitie.test_fase import zet_competitie_fase
from Competitie.operations import competities_aanmaken, competitie_klassegrenzen_vaststellen
from NhbStructuur.models import NhbRegio, NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, SCORE_WAARDE_VERWIJDERD
from Score.operations import score_indiv_ag_opslaan
from Wedstrijden.models import CompetitieWedstrijd
from Overig.e2ehelpers import E2EHelpers
from .models import CompetitieKlasse
import datetime
import io


class TestCompetitieCliUpdTussenstand(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command regiocomp_upd_tussenstand """

    def _maak_competitie_aan(self):
        # maak de competitie aan
        competities_aanmaken()

        self.comp = comp_18 = Competitie.objects.get(afstand='18')
        comp_25 = Competitie.objects.get(afstand='25')

        score_indiv_ag_opslaan(self.schutterboog_100005, 18, 9.500, None, "Test")

        # klassegrenzen vaststellen
        competitie_klassegrenzen_vaststellen(comp_18)
        competitie_klassegrenzen_vaststellen(comp_25)

        self.deelcomp_r101 = DeelCompetitie.objects.filter(laag='Regio',
                                                           competitie=self.comp,
                                                           nhb_regio=self.regio_101)[0]

        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        # wissel naar RCL functie
        self.e2e_wissel_naar_functie(self.deelcomp_r101.functie)

        # maak een regioplanning aan met 2 wedstrijden
        self.client.post(self.url_planning_regio % self.deelcomp_r101.pk)
        ronde = DeelcompetitieRonde.objects.all()[0]

        # maak 7 wedstrijden aan
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})

        self.assertEqual(7, CompetitieWedstrijd.objects.count())
        wedstrijd_pks = CompetitieWedstrijd.objects.all().values_list('pk', flat=True)

        # laat de wedstrijd.uitslag aanmaken en pas de wedstrijd nog wat aan
        self.uitslagen = list()
        uur = 1
        for pk in wedstrijd_pks[:]:     # copy to ensure stable
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_uitslag_invoeren % pk)
            wedstrijd = CompetitieWedstrijd.objects.get(pk=pk)
            self.assertIsNotNone(wedstrijd.uitslag)
            wedstrijd.vereniging = self.ver
            wedstrijd.tijd_begin_wedstrijd = "%02d:00" % uur
            uur = (uur + 1) % 24
            wedstrijd.save()
            self.uitslagen.append(wedstrijd.uitslag)
        # for

        # maak nog een wedstrijd aan - die blijft zonder uitslag
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})

    def _maak_leden_aan(self):
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@nhb.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = self.ver
        self.account_lid = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.account = self.account_lid
        lid.save()
        self.lid_100001 = lid
        schutterboog = SchutterBoog(nhblid=self.lid_100001, boogtype=self.boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100001 = schutterboog

        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "het Testertje"
        lid.email = "rdetestertje@nhb.not"
        lid.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        lid.bij_vereniging = self.ver
        self.account_jeugdlid = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.account = self.account_jeugdlid
        lid.save()
        self.lid_100002 = lid
        schutterboog = SchutterBoog(nhblid=self.lid_100002, boogtype=self.boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100002 = schutterboog

        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "M"
        lid.voornaam = "Geen"
        lid.achternaam = "Vereniging"
        lid.email = "geenver@nhb.not"
        lid.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        # lid.bij_vereniging =
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 100004
        lid.geslacht = "V"
        lid.voornaam = "Juf"
        lid.achternaam = "de Schutter"
        lid.email = "jufschut@nhb.not"
        lid.geboorte_datum = datetime.date(year=1988, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = self.ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()
        self.lid_100004 = lid
        schutterboog = SchutterBoog(nhblid=self.lid_100004, boogtype=self.boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100004 = schutterboog

        lid = NhbLid()
        lid.nhb_nr = 100005
        lid.geslacht = "V"
        lid.voornaam = "Jans"
        lid.achternaam = "de Schutter"
        lid.email = "jufschut@nhb.not"
        lid.geboorte_datum = datetime.date(year=1977, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = self.ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()
        self.lid_100005 = lid
        schutterboog = SchutterBoog(nhblid=self.lid_100005, boogtype=self.boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100005 = schutterboog

    @staticmethod
    def _schrijf_in_voor_competitie(deelcomp, schuttersboog, skip=1):
        while len(schuttersboog):
            schutterboog = schuttersboog[0]

            # let op: de testen die een schutter doorschuiven vereisen dat schutter 100001 in klasse onbekend
            klassen = (CompetitieKlasse
                       .objects
                       .filter(competitie=deelcomp.competitie,
                               indiv__is_onbekend=(schutterboog.nhblid.nhb_nr == 100001),
                               indiv__boogtype=schutterboog.boogtype))

            aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                     schutterboog=schutterboog)
            aanmelding.bij_vereniging = aanmelding.schutterboog.nhblid.bij_vereniging

            if len(schuttersboog) < len(klassen):
                aanmelding.klasse = klassen[len(schuttersboog)]
            else:
                aanmelding.klasse = klassen[0]
            aanmelding.save()
            # print('ingeschreven: %s in klasse %s' % (aanmelding.schutterboog, aanmelding.klasse))

            schuttersboog = schuttersboog[skip:]
        # while

    def _sluit_alle_regiocompetities(self, comp):
        # deze functie sluit alle regiocompetities af zodat de competitie in fase G komt
        comp.bepaal_fase()
        # print(comp.fase)
        self.assertTrue('B' < comp.fase < 'G')
        for deelcomp in DeelCompetitie.objects.filter(competitie=comp, laag=LAAG_REGIO):
            if not deelcomp.is_afgesloten:      # pragma: no branch
                deelcomp.is_afgesloten = True
                deelcomp.save()
        # for

        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'G')

    def setUp(self):
        """ initialisatie van de test case """

        self.url_planning_regio = '/bondscompetities/planning/regio/%s/'                  # deelcomp_pk
        self.url_planning_regio_ronde = '/bondscompetities/planning/regio/ronde/%s/'      # ronde_pk
        self.url_uitslag_invoeren = '/bondscompetities/scores/uitslag-invoeren/%s/'       # wedstrijd_pk
        self.url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'               # comp_pk       # TODO: ongewenste dependency op Vereniging

        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)
        self.boog_r = BoogType.objects.get(afkorting='R')

        # maak een BB aan, nodig om de competitie defaults in te zien
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.plaats = "Boogstad"
        ver.ver_nr = 1000
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.ver = ver

        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self._maak_leden_aan()
        self._maak_competitie_aan()

        # schrijf de leden in
        schuttersboog = [self.schutterboog_100001, self.schutterboog_100002,
                         self.schutterboog_100004, self.schutterboog_100005]
        self._schrijf_in_voor_competitie(self.deelcomp_r101, schuttersboog)

        self.functie_bko = DeelCompetitie.objects.get(competitie=self.comp,
                                                      laag=LAAG_BK,
                                                      competitie__afstand=18).functie

        self.client.logout()

    @staticmethod
    def _score_opslaan(uitslag, schutterboog, waarde):
        score = Score(afstand_meter=18,
                      schutterboog=schutterboog,
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

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(100):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Klaar' in f2.getvalue())

    def test_twee(self):
        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(160):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        self.assertEqual(deelnemer.score1, 123)
        self.assertEqual(deelnemer.score2, 124)
        self.assertEqual(deelnemer.score3, 0)
        self.assertEqual(deelnemer.totaal, 247)
        self.assertEqual(deelnemer.aantal_scores, 2)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.gemiddelde), '4.117')

        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))

        # nog een keer - nu wordt er niets bijgewerkt omdat er geen nieuwe scores zijn
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(156):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 0 schuttersboog bijgewerkt' in f2.getvalue())

        # nog een keer met 'all'
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(157):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', '--all', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

    def test_zeven(self):
        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[1], self.schutterboog_100001, 124)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 125)
        self._score_opslaan(self.uitslagen[3], self.schutterboog_100001, 126)
        self._score_opslaan(self.uitslagen[4], self.schutterboog_100001, 127)
        self._score_opslaan(self.uitslagen[5], self.schutterboog_100001, 128)
        self._score_opslaan(self.uitslagen[6], self.schutterboog_100001, 129)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(165):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
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

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(160):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        self.assertEqual(deelnemer.score1, 123)
        self.assertEqual(deelnemer.score6, 128)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 753)
        self.assertEqual(deelnemer.aantal_scores, 6)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.gemiddelde), '4.183')

    def test_verplaats(self):
        # check het verplaatsen van een schutter uit klasse onbekend

        deelnemer = RegioCompetitieSchutterBoog.objects.filter(schutterboog=self.schutterboog_100001)[0]
        self.assertTrue(deelnemer.klasse.indiv.is_onbekend)

        # 100001: 4 scores, gebruik eerste 3
        # 100002: nog maar 2 scores
        # 100004: Al in hogere klasse geplaatst
        # 100005: AG > 0.001

        # verplaats 100004 naar Recurve klasse 4, Senioren Vrouwen
        # zodat deze straks niet verplaatst hoeft te worden
        klasse = None
        for obj in (CompetitieKlasse                    # pragma: no branch
                    .objects
                    .filter(competitie=self.comp,
                            indiv__is_onbekend=False,
                            indiv__boogtype__afkorting=self.boog_r.afkorting)):
            for lkl in (obj.indiv.leeftijdsklassen      # pragma: no branch
                        .filter(afkorting='SV')):
                klasse = obj
                break
            # for

            if klasse:                                  # pragma: no branch
                break
        # for

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100004)
        deelnemer.klasse = klasse
        deelnemer.save()

        # pas het AG van 100005 aan
        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100005)
        deelnemer.aanvangsgemiddelde = 9.000
        deelnemer.save()

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[1], self.schutterboog_100001, 124)
        self._score_opslaan(self.uitslagen[3], self.schutterboog_100001, 128)
        self._score_opslaan(self.uitslagen[4], self.schutterboog_100001, 120)

        self._score_opslaan(self.uitslagen[0], self.schutterboog_100002, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100002, 124)

        self._score_opslaan(self.uitslagen[0], self.schutterboog_100004, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100004, 124)
        self._score_opslaan(self.uitslagen[3], self.schutterboog_100004, 128)

        self._score_opslaan(self.uitslagen[4], self.schutterboog_100005, 128)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(185):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[INFO] Verplaats 100001 (18m) met nieuw AG 4.167 naar klasse Recurve klasse' in f2.getvalue())

    def test_verplaats_zeven(self):
        # check het verplaatsen van een schutter uit klasse onbekend

        deelnemer = RegioCompetitieSchutterBoog.objects.filter(schutterboog=self.schutterboog_100001)[0]
        self.assertTrue(deelnemer.klasse.indiv.is_onbekend)

        # 100001: 7 scores, gebruik eerste 3 voor bepalen AG voor overstap
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[1], self.schutterboog_100001, 124)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 125)
        self._score_opslaan(self.uitslagen[3], self.schutterboog_100001, 122)
        self._score_opslaan(self.uitslagen[4], self.schutterboog_100001, 121)
        self._score_opslaan(self.uitslagen[5], self.schutterboog_100001, 129)
        self._score_opslaan(self.uitslagen[6], self.schutterboog_100001, 128)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(180):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[INFO] Verplaats 100001 (18m) met nieuw AG 4.133 naar klasse Recurve klasse' in f2.getvalue())

    def test_overstap(self):
        # test schutters die overstappen naar een andere vereniging

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(160):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        self.assertEqual(deelnemer.bij_vereniging.ver_nr, self.ver.ver_nr)

        # maak een tweede vereniging aan
        regio_116 = NhbRegio.objects.get(regio_nr=116)
        ver = NhbVereniging()
        ver.naam = "Zuidelijke Club"
        ver.plaats = "Grensstad"
        ver.ver_nr = 1100
        ver.regio = regio_116
        # secretaris kan nog niet ingevuld worden
        ver.save()

        lid = deelnemer.schutterboog.nhblid
        lid.bij_vereniging = ver
        lid.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(161):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Verwerk overstap 100001: [101] [1000] Grote Club --> [116] [1100] Zuidelijke Club" in f2.getvalue())

        # overstap naar vereniging in zelfde regio
        self.ver.regio = regio_116
        self.ver.save()
        lid.bij_vereniging = self.ver
        lid.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(160):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Verwerk overstap 100001: [116] [1100] Zuidelijke Club --> [116] [1000] Grote Club" in f2.getvalue())

        # zet the competitie in een later fase zodat overschrijvingen niet meer gedaan worden
        for comp in Competitie.objects.all():
            zet_competitie_fase(comp, 'K')
            comp.bepaal_fase()
            self.assertEqual(comp.fase, 'K')
        # for
        lid.bij_vereniging = ver
        lid.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(153):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('Verwerk overstap' in f2.getvalue())

    def test_uitstap(self):
        # schutter schrijft zich uit

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(155):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        # schrijf een schutter uit
        lid = self.schutterboog_100001.nhblid
        lid.bij_vereniging = None
        lid.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(157, check_duration=False):        # 7 seconden is boven de limiet
            management.call_command('regiocomp_upd_tussenstand', '7', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        # controleer dat de schutter op zijn oude vereniging blijft staan
        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog__nhblid__nhb_nr=100001)
        self.assertIsNone(deelnemer.schutterboog.nhblid.bij_vereniging)
        self.assertIsNotNone(deelnemer.bij_vereniging)

    def test_rk_fase_overstap(self):
        # test schutters die overstappen naar een andere vereniging binnen het rayon, tijdens de RK fase

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100002, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100002, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(160):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100002)
        self.assertEqual(deelnemer.bij_vereniging.ver_nr, self.ver.ver_nr)

        deelnemer.aantal_scores = 6
        deelnemer.save()

        # BKO zet de competitie naar de RK fase
        zet_competitie_fase(self.comp, 'F')
        self._sluit_alle_regiocompetities(self.comp)
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko)
        url = '/bondscompetities/%s/doorzetten/rk/' % self.comp.pk
        self.client.post(url)

        # standaard vereniging is regio 101
        # maak een tweede vereniging aan in regio 102
        regio_102 = NhbRegio.objects.get(regio_nr=102)
        ver = NhbVereniging()
        ver.naam = "Polderclub"
        ver.plaats = "Polderstad"
        ver.ver_nr = 1100
        ver.regio = regio_102
        # secretaris kan nog niet ingevuld worden
        ver.save()

        lid = deelnemer.schutterboog.nhblid
        lid.bij_vereniging = ver
        lid.save()

        rk_deelnemer = KampioenschapSchutterBoog.objects.get(schutterboog=deelnemer.schutterboog)
        rk_deelnemer.bij_vereniging = None
        rk_deelnemer.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(133):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Verwerk overstap 100002: GEEN VERENIGING --> [102] [1100] Polderclub" in f2.getvalue())

        # overstap naar vereniging in buiten het rayon
        self.ver.regio = NhbRegio.objects.get(regio_nr=105)
        self.ver.save()
        lid.bij_vereniging = self.ver
        lid.save()

        rk_deelnemer = KampioenschapSchutterBoog.objects.get(schutterboog=deelnemer.schutterboog)
        rk_deelnemer.bij_vereniging = None
        rk_deelnemer.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(132):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Verwerk overstap naar ander rayon niet mogelijk voor 100002 in RK voor rayon 1: GEEN VERENIGING --> [105] [1000] Grote Club" in f2.getvalue())

        # schutter die nog niet helemaal overgestapt is
        lid.bij_vereniging = None
        lid.save()

        rk_deelnemer = KampioenschapSchutterBoog.objects.get(schutterboog=deelnemer.schutterboog)
        rk_deelnemer.bij_vereniging = None
        rk_deelnemer.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(128):
            management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)

        # corner case
        zet_competitie_fase(self.comp, 'L')
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(128):
            management.call_command('regiocomp_upd_tussenstand', '1', '--quick', stderr=f1, stdout=f2)

# end of file
