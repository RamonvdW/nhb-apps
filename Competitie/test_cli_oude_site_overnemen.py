# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, CompetitieKlasse,
                               DeelCompetitie, LAAG_REGIO, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog,)
from Competitie.test_fase import zet_competitie_fase
from NhbStructuur.models import NhbRegio, NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, SCORE_TYPE_INDIV_AG, SCORE_TYPE_SCORE, score_indiv_ag_opslaan
from Wedstrijden.models import WedstrijdenPlan
from Overig.e2ehelpers import E2EHelpers
import datetime
import io


class TestCompetitieCliOudeSiteOvernemen(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command oude_site_overnemen """

    test_after = ('Competitie.test_cli_oude_site_maak_json',)

    def _maak_competitie_aan(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competitie aan
        self.client.post(self.url_aanmaken)

        comp_18 = Competitie.objects.get(afstand='18')
        comp_25 = Competitie.objects.get(afstand='25')

        # klassegrenzen vaststellen
        self.client.post(self.url_klassegrenzen_vaststellen % comp_18.pk)
        self.client.post(self.url_klassegrenzen_vaststellen % comp_25.pk)

        # competitieklassen vaststellen

        # verander de minimale aanvangsgemiddelde voor Recurve Klasse 2 naar 9.5
        klasse = CompetitieKlasse.objects.get(competitie__afstand='18',
                                              indiv__beschrijving='Recurve klasse 2')
        klasse.min_ag = 9.5
        klasse.save()
        self.klasse = klasse

        zet_competitie_fase(comp_18, 'E')
        zet_competitie_fase(comp_25, 'E')

    def _maak_leden_aan(self):
        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = regio = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Oude Club"
        ver.plaats = "Boogdrop"
        ver.ver_nr = 1002
        ver.regio = regio
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.plaats = "Boogstad"
        ver.ver_nr = 1000
        ver.regio = regio
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.ver_1000 = ver

        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@nhb.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        self.account_lid = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.account = self.account_lid
        lid.save()
        self.lid_100001 = lid

        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "het Testertje"
        lid.email = "rdetestertje@nhb.not"
        lid.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        lid.bij_vereniging = ver
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
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 100005
        lid.geslacht = "V"
        lid.voornaam = "Jean"
        lid.achternaam = "van de Schut"
        lid.email = "jeanvdschut@nhb.not"
        lid.geboorte_datum = datetime.date(year=1988, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 100006
        lid.geslacht = "V"
        lid.voornaam = "Jans"
        lid.achternaam = "van Schoot"
        lid.email = "jansvschut@nhb.not"
        lid.geboorte_datum = datetime.date(year=1988, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 100007
        lid.geslacht = "V"
        lid.voornaam = "Petra"
        lid.achternaam = "Jans"
        lid.email = "pjans@nhb.not"
        lid.geboorte_datum = datetime.date(year=1988, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 100008
        lid.geslacht = "M"
        lid.voornaam = "Eerste"
        lid.achternaam = "Exlid"
        lid.email = "exlid1@nhb.not"
        lid.geboorte_datum = datetime.date(year=1988, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = None
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 100009
        lid.geslacht = "M"
        lid.voornaam = "Tweede"
        lid.achternaam = "Exlid"
        lid.email = "exlid1@nhb.not"
        lid.geboorte_datum = datetime.date(year=1988, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = None
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 100010
        lid.geslacht = "M"
        lid.voornaam = "Whatever"
        lid.achternaam = "Overstapper"
        lid.email = "overstapper@nhb.not"
        lid.geboorte_datum = datetime.date(year=1988, month=12, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=7, day=15)
        lid.bij_vereniging = None
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

    def setUp(self):
        """ initialisatie van de test case """

        self.url_aanmaken = '/bondscompetities/aanmaken/'
        self.url_klassegrenzen_vaststellen = '/bondscompetities/%s/klassegrenzen/vaststellen/'

        # maak een BB aan, nodig om de competitie defaults in te zien
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        self._maak_competitie_aan()

        self._maak_leden_aan()

        self.boog_bb = BoogType.objects.get(afkorting='BB')

        # een schutterboog inschrijven in verkeerde klasse zodat deze verwijderd gaat worden
        boog_r = BoogType.objects.get(afkorting='R')
        schutterboog = SchutterBoog(nhblid=self.lid_100002, boogtype=boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100002 = schutterboog

        deelcomp = DeelCompetitie.objects.filter(competitie__afstand='18', laag=LAAG_REGIO).all()[0]
        obj = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                          schutterboog=schutterboog,
                                          bij_vereniging=self.lid_100002.bij_vereniging,
                                          klasse=self.klasse)
        obj.save()
        self.deelcomp = deelcomp

        self.dir_top = './Competitie/management/testfiles/'
        self.dir_testfiles1 = './Competitie/management/testfiles/20200929_220000'
        self.dir_testfiles2 = './Competitie/management/testfiles/20200930_091011'

    def test_verwijder_oude_data(self):
        # eerst aanmaken, dan verwijderen
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(1861):
            management.call_command('oude_site_overnemen', self.dir_testfiles1, '100', stderr=f1, stdout=f2)

        # verwijder de uitslag van een wedstrijd
        ronde = DeelcompetitieRonde.objects.all()[3]
        wedstrijd = ronde.plan.wedstrijden.all()[0]
        uitslag = wedstrijd.uitslag
        wedstrijd.uitslag = None
        wedstrijd.save()
        uitslag.delete()

        # voeg een ronde toe die niet voor het oude programma is
        plan = WedstrijdenPlan()
        plan.save()
        ronde = DeelcompetitieRonde(deelcompetitie=self.deelcomp,
                                    beschrijving="Hello World",
                                    week_nr=42,
                                    plan=plan)
        ronde.save()

        # maak een AG die opgeruimd moet worden
        Score(schutterboog=self.schutterboog_100002,
              type=SCORE_TYPE_INDIV_AG,
              waarde=1000,
              afstand_meter=18).save()

        # maak er nog een met een ScoreHist, die moet dus niet opgeruimd worden
        score = Score(schutterboog=self.schutterboog_100002,
                      type=SCORE_TYPE_INDIV_AG,
                      waarde=1000,
                      afstand_meter=25)
        score.save()
        ScoreHist(score=score,
                  nieuwe_waarde=1000,
                  oude_waarde=999,
                  notitie="Gewoon een testje").save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(4270):
            management.call_command('verwijder_data_oude_site', stderr=f1, stdout=f2)
        self.assertTrue("AG's opgeruimd: 1" in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('verwijder_data_oude_site', stderr=f1, stdout=f2)
        self.assertTrue("AG's opgeruimd" not in f2.getvalue())

    def test_bepaal_1(self):
        self.assertEqual(Score.objects.count(), 0)
        self.assertEqual(ScoreHist.objects.count(), 0)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(1861):
            management.call_command('oude_site_overnemen', self.dir_testfiles1, '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Schutter 100001 heeft te laag AG (9.022) voor klasse Recurve klasse 2 (9.500)" in f2.getvalue())
        self.assertTrue("[WARNING] Kan lid 100042 niet vinden" in f2.getvalue())
        self.assertTrue("[WARNING] Kan lid 990000 niet vinden" in f2.getvalue())
        self.assertTrue("[INFO] Verschil in lid 100004 naam: bekend=Juf de Schutter, oude programma=Juf de Schytter" in f2.getvalue())
        self.assertTrue("[INFO] Sla dubbele invoer onder recurve (18m) over: 100002 (scores:" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder 1 dubbele inschrijvingen" in f2.getvalue())

        self.assertEqual(Score.objects.filter(type=SCORE_TYPE_INDIV_AG).count(), 0)
        self.assertEqual(Score.objects.filter(type=SCORE_TYPE_SCORE).count(), 4)
        self.assertEqual(ScoreHist.objects.count(), 4)

        hist = ScoreHist.objects.all()[0]
        self.assertEqual(str(hist.when), '2020-09-29 20:00:00+00:00')       # TODO: test gevoelig voor timezone?

        # nog een keer, want dan zijn de uitslagen er al (extra coverage)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(923):
            management.call_command('oude_site_overnemen', self.dir_testfiles1, '1', stderr=f1, stdout=f2)

        self.assertEqual(ScoreHist.objects.count(), 4)

    def test_bepaal_2(self):
        # maak een AG aan voor schutter 100002-BB zodat we een verschil kunnen detecteren

        schutterboog = SchutterBoog(nhblid=self.lid_100002,
                                    boogtype=self.boog_bb,
                                    voor_wedstrijd=True)
        schutterboog.save()
        score_indiv_ag_opslaan(schutterboog, 18, 4.444, None, 'test prep')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(1893):
            management.call_command('oude_site_overnemen', self.dir_testfiles2, '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        self.assertTrue("[ERROR] Kan wedstrijdklasse 'Barebow Cadetten klasse 1' niet vinden (competitie Indoor" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1099 is niet bekend; kan lid 100004 niet inschrijven" in f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Lid 100003 heeft 1 scores maar geen vereniging en wordt ingeschreven onder de oude vereniging" in f2.getvalue())
        self.assertTrue("[WARNING] Verschil in AG voor nhbnr 100002 (18m): bekend=4.444, in uitslag=4.567" in f2.getvalue())

        # nog een keer uitvoeren zodat eventuele teams al bestaan
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(950):
            management.call_command('oude_site_overnemen', self.dir_testfiles2, '100', stderr=f1, stdout=f2)

    def test_dryrun(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(1840):
            management.call_command('oude_site_overnemen', '--dryrun', self.dir_testfiles1, '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("(DRY RUN)" in f2.getvalue())

    def test_all(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(2850):
            management.call_command('oude_site_overnemen', '--all', self.dir_top, '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        # de 3 directories bevatten maar 2 oude_site.json
        self.assertTrue('Voortgang: 1 van de 2' in f2.getvalue())
        self.assertTrue('Voortgang: 2 van de 2' in f2.getvalue())

    def test_te_veel_fouten(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(SystemExit):
            management.call_command('oude_site_overnemen', self.dir_testfiles1, '-1', stderr=f1, stdout=f2)

    def test_verkeerde_fase(self):
        comp_18 = Competitie.objects.get(afstand='18')
        zet_competitie_fase(comp_18, 'A')
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(910):
            management.call_command('oude_site_overnemen', '--dryrun', self.dir_testfiles1, '100', stderr=f1, stdout=f2)
        self.assertTrue("(DRY RUN)" in f2.getvalue())

    def test_verwijderde_vereniging(self):
        # uitslag oude programma verwijst nog naar een vereniging waar de schutter weg
        # is en die bovendien opgeruimd is in het CRM
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(1895):
            management.call_command('oude_site_overnemen', self.dir_testfiles1, '100', stderr=f1, stdout=f2)

        # ruim vereniging 1000 op
        for deelnemer in RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self.ver_1000):
            deelnemer.delete()
        # for
        for lid in NhbLid.objects.filter(bij_vereniging=self.ver_1000):
            lid.bij_vereniging = None
            lid.save()
        # for
        self.ver_1000.delete()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(950):
            management.call_command('oude_site_overnemen', self.dir_testfiles1, '100', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[ERROR] Vereniging 1000 is niet bekend; kan lid 100002 niet inschrijven (bij de oude vereniging)' in f1.getvalue())

# end of file
