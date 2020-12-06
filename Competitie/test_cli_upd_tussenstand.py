# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, DeelCompetitie, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog, KampioenschapSchutterBoog,
                               AG_NUL, LAAG_REGIO, LAAG_BK)
from Competitie.test_fase import zet_competitie_fase
from NhbStructuur.models import NhbRegio, NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, SCORE_WAARDE_VERWIJDERD, aanvangsgemiddelde_opslaan
from Wedstrijden.models import Wedstrijd
from Overig.e2ehelpers import E2EHelpers
from .models import CompetitieKlasse
import datetime
import io


class TestCompetitieCliUpdTussenstand(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command regiocomp_upd_tussenstand """

    def _maak_competitie_aan(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competitie aan
        self.client.post(self.url_aanmaken)
        self.comp = Competitie.objects.all()[0]

        aanvangsgemiddelde_opslaan(self.schutterboog_100005, 18, 9.500, None, "Test")

        # klassegrenzen vaststellen
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = succes
        resp = self.client.post(self.url_klassegrenzen_vaststellen_25)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = succes

        self.deelcomp_r101 = DeelCompetitie.objects.filter(laag='Regio',
                                                           competitie=self.comp,
                                                           nhb_regio=self.regio_101)[0]

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

        self.assertEqual(7, Wedstrijd.objects.count())
        wedstrijd_pks = Wedstrijd.objects.all().values_list('pk', flat=True)

        # laat de wedstrijd.uitslag aanmaken en pas de wedstrijd nog wat aan
        self.uitslagen = list()
        uur = 1
        for pk in wedstrijd_pks[:]:     # copy to ensure stable
            resp = self.client.get(self.url_uitslag_invoeren % pk)
            wedstrijd = Wedstrijd.objects.get(pk=pk)
            self.assertIsNotNone(wedstrijd.uitslag)
            wedstrijd.vereniging = self.ver
            wedstrijd.tijd_begin_wedstrijd = "%02d:00" % uur
            uur = (uur + 1) % 24
            wedstrijd.save()
            self.uitslagen.append(wedstrijd.uitslag)
        # for

        # maak nog een wedstrijd aan - die blijft zonder uitslag
        self.client.post(self.url_planning_regio_ronde % ronde.pk, {})

    def _maak_import(self, aantal=5):
        # wissel naar RCL functie
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.deelcomp_r101.functie)
        self.e2e_check_rol('RCL')

        # maak er een paar rondes bij voor geïmporteerde uitslagen, elk met 1 wedstrijd
        for _ in range(aantal):
            self.client.post(self.url_planning_regio % self.deelcomp_r101.pk)

        top_pk = DeelcompetitieRonde.objects.latest('pk').pk - aantal + 1

        for nr in range(1, 1+aantal):
            # maak een wedstrijd aan (doen voordat de beschrijving aangepast wordt)
            resp = self.client.post(self.url_planning_regio_ronde % top_pk, {})
            self.assertTrue(resp.status_code < 400)

            ronde = DeelcompetitieRonde.objects.get(pk=top_pk)

            # wedstrijduitslag aanmaken
            wedstrijd = ronde.plan.wedstrijden.all()[0]
            resp = self.client.get(self.url_uitslag_invoeren % wedstrijd.pk)
            self.assertTrue(resp.status_code < 400)

            ronde.beschrijving = 'Ronde %s oude programma' % nr
            ronde.save()

            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
            self.uitslagen.append(wedstrijd.uitslag)

            top_pk += 1
        # for

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
            aanmelding = RegioCompetitieSchutterBoog()
            aanmelding.deelcompetitie = deelcomp
            aanmelding.schutterboog = schuttersboog[0]
            aanmelding.bij_vereniging = aanmelding.schutterboog.nhblid.bij_vereniging
            aanmelding.aanvangsgemiddelde = AG_NUL
            aanmelding.klasse = (CompetitieKlasse
                                 .objects
                                 .filter(competitie=deelcomp.competitie,
                                         indiv__boogtype=aanmelding.schutterboog.boogtype,
                                         indiv__is_onbekend=True)[0])
            aanmelding.save()

            schuttersboog = schuttersboog[skip:]
        # while

    def _sluit_alle_regiocompetities(self, comp):
        # deze functie sluit alle regiocompetities af zodat de competitie in fase G komt
        comp.zet_fase()
        # print(comp.fase)
        self.assertTrue('B' < comp.fase < 'G')
        for deelcomp in DeelCompetitie.objects.filter(competitie=comp, laag=LAAG_REGIO):
            if not deelcomp.is_afgesloten:      # pragma: no branch
                deelcomp.is_afgesloten = True
                deelcomp.save()
        # for

        comp.zet_fase()
        self.assertEqual(comp.fase, 'G')

    def setUp(self):
        """ initialisatie van de test case """

        self.url_aanmaken = '/competitie/aanmaken/'
        self.url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        self.url_klassegrenzen_vaststellen_25 = '/competitie/klassegrenzen/vaststellen/25/'
        self.url_planning_regio = '/competitie/planning/regiocompetitie/%s/'        # deelcomp_pk
        self.url_planning_regio_ronde = '/competitie/planning/regiocompetitie/ronde/%s/'  # ronde_pk
        self.url_uitslag_invoeren = '/competitie/wedstrijd/uitslag-invoeren/%s/'    # wedstrijd_pk
        self.url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'         # comp_pk

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
        ver.nhb_nr = 1000
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
        score = Score(is_ag=False,
                      afstand_meter=18,
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
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Klaar' in f2.getvalue())

    def test_twee(self):
        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        self.assertEqual(deelnemer.score1, 0)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 0)
        self.assertEqual(deelnemer.aantal_scores, 0)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(deelnemer.gemiddelde, 0.0)
        self.assertEqual(deelnemer.alt_score1, 123)
        self.assertEqual(deelnemer.alt_score2, 124)
        self.assertEqual(deelnemer.alt_score3, 0)
        self.assertEqual(deelnemer.alt_totaal, 247)
        self.assertEqual(deelnemer.alt_aantal_scores, 2)
        self.assertEqual(deelnemer.alt_laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.alt_gemiddelde), '4.117')
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        # print('alt_scores: %s %s %s %s %s %s %s, alt_laagste_nr=%s, alt_totaal=%s, alt_gem=%s' % (deelnemer.alt_score1, deelnemer.alt_score2, deelnemer.alt_score3, deelnemer.alt_score4, deelnemer.alt_score5, deelnemer.alt_score6, deelnemer.alt_score7, deelnemer.alt_laagste_score_nr, deelnemer.alt_totaal, deelnemer.alt_gemiddelde))

        # nog een keer - nu wordt er niets bijgewerkt omdat er geen nieuwe scores zijn
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 0 schuttersboog bijgewerkt' in f2.getvalue())

        # nog een keer met 'all'
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', '--all', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

    def test_zeven(self):
        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

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
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        # print('alt_scores: %s %s %s %s %s %s %s, alt_laagste_nr=%s, alt_totaal=%s, alt_gem=%s' % (deelnemer.alt_score1, deelnemer.alt_score2, deelnemer.alt_score3, deelnemer.alt_score4, deelnemer.alt_score5, deelnemer.alt_score6, deelnemer.alt_score7, deelnemer.alt_laagste_score_nr, deelnemer.alt_totaal, deelnemer.alt_gemiddelde))
        self.assertEqual(deelnemer.score1, 0)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 0)
        self.assertEqual(deelnemer.aantal_scores, 0)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(deelnemer.gemiddelde, 0.0)
        self.assertEqual(deelnemer.alt_score1, 123)
        self.assertEqual(deelnemer.alt_score6, 128)
        self.assertEqual(deelnemer.alt_score7, 129)
        self.assertEqual(deelnemer.alt_totaal, 759)           # som van 124..129 (123 is de laagste)
        self.assertEqual(deelnemer.alt_aantal_scores, 7)
        self.assertEqual(deelnemer.alt_laagste_score_nr, 1)   # eerste score is de laagste
        self.assertEqual(str(deelnemer.alt_gemiddelde), '4.217')

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
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        # print('alt_scores: %s %s %s %s %s %s %s, alt_laagste_nr=%s, alt_totaal=%s, alt_gem=%s' % (deelnemer.alt_score1, deelnemer.alt_score2, deelnemer.alt_score3, deelnemer.alt_score4, deelnemer.alt_score5, deelnemer.alt_score6, deelnemer.alt_score7, deelnemer.alt_laagste_score_nr, deelnemer.alt_totaal, deelnemer.alt_gemiddelde))
        self.assertEqual(deelnemer.score1, 0)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 0)
        self.assertEqual(deelnemer.aantal_scores, 0)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(deelnemer.gemiddelde, 0.0)
        self.assertEqual(deelnemer.alt_score1, 123)
        self.assertEqual(deelnemer.alt_score6, 128)
        self.assertEqual(deelnemer.alt_score7, 0)
        self.assertEqual(deelnemer.alt_totaal, 753)           # som van 123..128 (6 scores)
        self.assertEqual(deelnemer.alt_aantal_scores, 6)
        self.assertEqual(deelnemer.alt_laagste_score_nr, 0)   # geen schrap-score
        self.assertEqual(str(deelnemer.alt_gemiddelde), '4.183')

    def test_mix(self):
        self._maak_import()     # 5 nieuwe rondes: 7..11

        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[1], self.schutterboog_100001, 124)
        self._score_opslaan(self.uitslagen[7], self.schutterboog_100001, 125)       # import
        self._score_opslaan(self.uitslagen[8], self.schutterboog_100001, 126)       # import
        self._score_opslaan(self.uitslagen[9], self.schutterboog_100001, 137)       # import
        self._score_opslaan(self.uitslagen[5], self.schutterboog_100001, 128)
        self._score_opslaan(self.uitslagen[6], self.schutterboog_100001, 129)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        # print('alt_scores: %s %s %s %s %s %s %s, alt_laagste_nr=%s, alt_totaal=%s, alt_gem=%s' % (deelnemer.alt_score1, deelnemer.alt_score2, deelnemer.alt_score3, deelnemer.alt_score4, deelnemer.alt_score5, deelnemer.alt_score6, deelnemer.alt_score7, deelnemer.alt_laagste_score_nr, deelnemer.alt_totaal, deelnemer.alt_gemiddelde))
        self.assertEqual(deelnemer.score1, 125)
        self.assertEqual(deelnemer.score2, 126)
        self.assertEqual(deelnemer.score3, 137)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 388)
        self.assertEqual(deelnemer.aantal_scores, 3)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.gemiddelde), '4.311')
        self.assertEqual(deelnemer.alt_score1, 123)
        self.assertEqual(deelnemer.alt_score4, 129)
        self.assertEqual(deelnemer.alt_totaal, 504)
        self.assertEqual(deelnemer.alt_aantal_scores, 4)
        self.assertEqual(deelnemer.alt_laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.alt_gemiddelde), '4.200')

    def test_import(self):
        # verwijder bestaande rondes zodat er alleen import komt
        DeelcompetitieRonde.objects.all().delete()
        self.uitslagen = list()

        self._maak_import()     # 5 nieuwe rondes: 7..11

        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 125)       # import
        self._score_opslaan(self.uitslagen[1], self.schutterboog_100001, 126)       # import
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 137)       # import
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        # print('alt_scores: %s %s %s %s %s %s %s, alt_laagste_nr=%s, alt_totaal=%s, alt_gem=%s' % (deelnemer.alt_score1, deelnemer.alt_score2, deelnemer.alt_score3, deelnemer.alt_score4, deelnemer.alt_score5, deelnemer.alt_score6, deelnemer.alt_score7, deelnemer.alt_laagste_score_nr, deelnemer.alt_totaal, deelnemer.alt_gemiddelde))
        self.assertEqual(deelnemer.score1, 125)
        self.assertEqual(deelnemer.score2, 126)
        self.assertEqual(deelnemer.score3, 137)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 388)
        self.assertEqual(deelnemer.laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.gemiddelde), '4.311')
        self.assertEqual(deelnemer.alt_score1, 0)
        self.assertEqual(deelnemer.alt_totaal, 0)
        self.assertEqual(deelnemer.alt_laagste_score_nr, 0)
        self.assertEqual(str(deelnemer.alt_gemiddelde), '0.000')

    def test_verplaats(self):
        # check het verplaatsen van een schutter uit klasse onbekend

        self._maak_import()     # 5 nieuwe rondes: 7..11

        # schrijf een paar mensen in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        post_params['lid_100002_boogtype_%s' % self.boog_r.pk] = 'on'
        post_params['lid_100004_boogtype_%s' % self.boog_r.pk] = 'on'
        post_params['lid_100005_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

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
                        .filter(geslacht='V',
                                min_wedstrijdleeftijd__gt=20)):
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
        self._score_opslaan(self.uitslagen[7], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[8], self.schutterboog_100001, 124)
        self._score_opslaan(self.uitslagen[10], self.schutterboog_100001, 128)
        self._score_opslaan(self.uitslagen[11], self.schutterboog_100001, 120)

        self._score_opslaan(self.uitslagen[7], self.schutterboog_100002, 123)
        self._score_opslaan(self.uitslagen[9], self.schutterboog_100002, 124)

        self._score_opslaan(self.uitslagen[7], self.schutterboog_100004, 123)
        self._score_opslaan(self.uitslagen[9], self.schutterboog_100004, 124)
        self._score_opslaan(self.uitslagen[10], self.schutterboog_100004, 128)

        self._score_opslaan(self.uitslagen[11], self.schutterboog_100005, 128)

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[INFO] Verplaats 100001 (18m) met nieuw AG 4.167 naar klasse Recurve klasse' in f2.getvalue())

    def test_verplaats_zeven(self):
        # check het verplaatsen van een schutter uit klasse onbekend

        self._maak_import(aantal=7)     # 7 nieuwe rondes: 7..13

        # schrijf een paar mensen in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # 100001: 7 scores, gebruik eerste 3 voor bepalen AG voor overstap

        self._score_opslaan(self.uitslagen[7], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[8], self.schutterboog_100001, 124)
        self._score_opslaan(self.uitslagen[9], self.schutterboog_100001, 125)
        self._score_opslaan(self.uitslagen[10], self.schutterboog_100001, 122)
        self._score_opslaan(self.uitslagen[11], self.schutterboog_100001, 121)
        self._score_opslaan(self.uitslagen[12], self.schutterboog_100001, 129)
        self._score_opslaan(self.uitslagen[13], self.schutterboog_100001, 128)

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[INFO] Verplaats 100001 (18m) met nieuw AG 4.133 naar klasse Recurve klasse' in f2.getvalue())

    def test_overstap(self):
        # test schutters die overstappen naar een andere vereniging

        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        self.assertEqual(deelnemer.bij_vereniging.nhb_nr, self.ver.nhb_nr)

        # maak een tweede vereniging aan
        regio_116 = NhbRegio.objects.get(regio_nr=116)
        ver = NhbVereniging()
        ver.naam = "Zuidelijke Club"
        ver.plaats = "Grensstad"
        ver.nhb_nr = 1100
        ver.regio = regio_116
        # secretaris kan nog niet ingevuld worden
        ver.save()

        lid = deelnemer.schutterboog.nhblid
        lid.bij_vereniging = ver
        lid.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Verwerk overstap 100001: [101] [1000] Grote Club --> [116] [1100] Zuidelijke Club" in f2.getvalue())

        # overstap naar vereniging in zelfde regio
        self.ver.regio = regio_116
        self.ver.save()
        lid.bij_vereniging = self.ver
        lid.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Verwerk overstap 100001: [116] [1100] Zuidelijke Club --> [116] [1000] Grote Club" in f2.getvalue())

        # zet the competitie in een later fase zodat overschrijvingen niet meer gedaan worden
        for comp in Competitie.objects.all():
            zet_competitie_fase(comp, 'K')
            comp.zet_fase()
            self.assertEqual(comp.fase, 'K')
        # for
        lid.bij_vereniging = ver
        lid.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('Verwerk overstap' in f2.getvalue())

    def test_uitstap(self):
        # schutter schrijft zich uit

        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        # schrijf een schutter uit
        lid = self.schutterboog_100001.nhblid
        lid.bij_vereniging = None
        lid.save()
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '7', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Uitstapper: 100001 [101] [1000] Grote Club (actief=True)" in f2.getvalue())

    def test_rk_fase_overstap(self):
        # test schutters die overstappen naar een andere vereniging binnen het rayon, tijdens de RK fase

        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven % self.comp.pk, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        self.assertEqual(deelnemer.bij_vereniging.nhb_nr, self.ver.nhb_nr)

        deelnemer.aantal_scores = 6
        deelnemer.save()

        # BKO zet de competitie naar de RK fase
        zet_competitie_fase(self.comp, 'F')
        self._sluit_alle_regiocompetities(self.comp)
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko)
        url = '/competitie/planning/doorzetten/%s/rk/' % self.comp.pk
        self.client.post(url)

        # standaard vereniging is regio 101
        # maak een tweede vereniging aan in regio 102
        regio_102 = NhbRegio.objects.get(regio_nr=102)
        ver = NhbVereniging()
        ver.naam = "Polderclub"
        ver.plaats = "Polderstad"
        ver.nhb_nr = 1100
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
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Verwerk overstap 100001: GEEN VERENIGING --> [102] [1100] Polderclub" in f2.getvalue())

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
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Verwerk overstap naar ander rayon niet mogelijk voor 100001 in RK voor rayon 1: GEEN VERENIGING --> [105] [1000] Grote Club" in f2.getvalue())

        # schutter die nog niet helemaal overgestapt is
        lid.bij_vereniging = None
        lid.save()

        rk_deelnemer = KampioenschapSchutterBoog.objects.get(schutterboog=deelnemer.schutterboog)
        rk_deelnemer.bij_vereniging = None
        rk_deelnemer.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '2', '--quick', stderr=f1, stdout=f2)

        # corner case
        zet_competitie_fase(self.comp, 'L')
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_upd_tussenstand', '1', '--quick', stderr=f1, stdout=f2)

# end of file
