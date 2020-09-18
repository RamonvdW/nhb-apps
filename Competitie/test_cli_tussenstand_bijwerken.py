# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.utils import timezone
from BasisTypen.models import BoogType
from Competitie.models import Competitie, DeelCompetitie, DeelcompetitieRonde, RegioCompetitieSchutterBoog, AG_NUL
from NhbStructuur.models import NhbRegio, NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist
from Wedstrijden.models import Wedstrijd
from Overig.e2ehelpers import E2EHelpers
from .models import CompetitieKlasse
import datetime
import io


class TestRecordsCliTussenstandBijwerken(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command competitie_tussenstand_bijwerken """

    def _maak_competitie_aan(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competitie aan
        self.client.post(self.url_aanmaken)
        self.comp = Competitie.objects.all()[0]
        self.url_inschrijven = '/vereniging/leden-inschrijven/competitie/%s/' % self.comp.pk

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
        for pk in wedstrijd_pks[:]:     # copy to ensure stable
            resp = self.client.get(self.url_uitslag_invoeren % pk)
            wedstrijd = Wedstrijd.objects.get(pk=pk)
            self.assertIsNotNone(wedstrijd.uitslag)
            wedstrijd.vereniging = self.ver
            wedstrijd.tijd_begin_wedstrijd = "%02d:00" % pk
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

        # maak een schutterboog aan voor het jeugdlid (nodig om aan te melden)
        schutterboog = SchutterBoog(nhblid=self.lid_100001, boogtype=self.boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100001 = schutterboog

        self._schrijf_in_voor_competitie(self.deelcomp_r101, [self.schutterboog_100001], 1)

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

        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "M"
        lid.voornaam = "Geen"
        lid.achternaam = "Vereniging"
        lid.email = "geenver@nhb.not"
        lid.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        #lid.bij_vereniging =
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

    @staticmethod
    def _schrijf_in_voor_competitie(deelcomp, schuttersboog, skip):
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

    def setUp(self):
        """ initialisatie van de test case """

        self.url_aanmaken = '/competitie/aanmaken/'
        self.url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        self.url_klassegrenzen_vaststellen_25 = '/competitie/klassegrenzen/vaststellen/25/'
        self.url_planning_regio = '/competitie/planning/regiocompetitie/%s/'    # deelcomp_pk
        self.url_planning_regio_ronde = '/competitie/planning/regiocompetitie/ronde/%s/'        # ronde_pk
        self.url_uitslag_invoeren = '/competitie/uitslagen-invoeren/wedstrijd/%s/'  # wedstrijd_pk

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

        self._maak_competitie_aan()
        self._maak_leden_aan()

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
                         nieuwe_waarde=waarde,
                         when=timezone.now())
        hist.save()

        uitslag.scores.add(score)

    def test_leeg(self):
        self.assertEqual(Score.objects.count(), 0)
        self.assertEqual(ScoreHist.objects.count(), 0)

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('competitie_tussenstand_bijwerken', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('Klaar' in f2.getvalue())

    def test_uitslagen_twee(self):
        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven, post_params)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect = succes

        # maak een paar score + scorehist
        self._score_opslaan(self.uitslagen[0], self.schutterboog_100001, 123)
        self._score_opslaan(self.uitslagen[2], self.schutterboog_100001, 124)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('competitie_tussenstand_bijwerken', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        self.assertEqual(deelnemer.score1, 0)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 0)
        self.assertEqual(deelnemer.laagste_score_nr, 7)
        self.assertEqual(deelnemer.gemiddelde, 0.0)
        self.assertEqual(deelnemer.alt_score1, 123)
        self.assertEqual(deelnemer.alt_score2, 124)
        self.assertEqual(deelnemer.alt_score3, 0)
        self.assertEqual(deelnemer.alt_totaal, 247)
        self.assertEqual(deelnemer.alt_laagste_score_nr, 7)
        self.assertEqual(str(deelnemer.alt_gemiddelde), '4.117')
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        # print('alt_scores: %s %s %s %s %s %s %s, alt_laagste_nr=%s, alt_totaal=%s, alt_gem=%s' % (deelnemer.alt_score1, deelnemer.alt_score2, deelnemer.alt_score3, deelnemer.alt_score4, deelnemer.alt_score5, deelnemer.alt_score6, deelnemer.alt_score7, deelnemer.alt_laagste_score_nr, deelnemer.alt_totaal, deelnemer.alt_gemiddelde))

        # nog een keer - nu wordt er niets bijgewerkt omdat er geen nieuwe scores zijn
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('competitie_tussenstand_bijwerken', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 0 schuttersboog bijgewerkt' in f2.getvalue())

        # nog een keer met 'all'
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('competitie_tussenstand_bijwerken', '2', '--quick', '--all', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

    def test_uitslagen_zeven(self):
        # schrijf iemand in
        post_params = dict()
        post_params['lid_100001_boogtype_%s' % self.boog_r.pk] = 'on'
        resp = self.client.post(self.url_inschrijven, post_params)
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
        management.call_command('competitie_tussenstand_bijwerken', '2', '--quick', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('Scores voor 1 schuttersboog bijgewerkt' in f2.getvalue())

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog=self.schutterboog_100001)
        self.assertEqual(deelnemer.score1, 0)
        self.assertEqual(deelnemer.score7, 0)
        self.assertEqual(deelnemer.totaal, 0)
        self.assertEqual(deelnemer.laagste_score_nr, 7)
        self.assertEqual(deelnemer.gemiddelde, 0.0)
        self.assertEqual(deelnemer.alt_score1, 123)
        self.assertEqual(deelnemer.alt_score7, 129)
        self.assertEqual(deelnemer.alt_totaal, 759)           # som van 124..129 (123 is de laagste)
        self.assertEqual(deelnemer.alt_laagste_score_nr, 1)   # eerste score is de laagste
        self.assertEqual(str(deelnemer.alt_gemiddelde), '4.217')
        # print('scores: %s %s %s %s %s %s %s, laagste_nr=%s, totaal=%s, gem=%s' % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7, deelnemer.laagste_score_nr, deelnemer.totaal, deelnemer.gemiddelde))
        # print('alt_scores: %s %s %s %s %s %s %s, alt_laagste_nr=%s, alt_totaal=%s, alt_gem=%s' % (deelnemer.alt_score1, deelnemer.alt_score2, deelnemer.alt_score3, deelnemer.alt_score4, deelnemer.alt_score5, deelnemer.alt_score6, deelnemer.alt_score7, deelnemer.alt_laagste_score_nr, deelnemer.alt_totaal, deelnemer.alt_gemiddelde))


# end of file
