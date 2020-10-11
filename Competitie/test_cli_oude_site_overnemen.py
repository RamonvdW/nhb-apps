# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Competitie.models import (RegioCompetitieSchutterBoog, DeelCompetitie, LAAG_REGIO,
                               DeelcompetitieRonde)
from NhbStructuur.models import NhbRegio, NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, aanvangsgemiddelde_opslaan
from Wedstrijden.models import WedstrijdenPlan
from Overig.e2ehelpers import E2EHelpers
from .models import CompetitieKlasse
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

        # klassegrenzen vaststellen
        self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.client.post(self.url_klassegrenzen_vaststellen_25)

        # competitieklassen vaststellen

        # verander de minimale aanvangsgemiddelde voor Recurve Klasse 2 naar 9.5
        klasse = CompetitieKlasse.objects.get(competitie__afstand='18',
                                              indiv__beschrijving='Recurve klasse 2')
        klasse.min_ag = 9.5
        klasse.save()
        self.klasse = klasse

    def _maak_leden_aan(self):
        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = regio = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Oude Club"
        ver.plaats = "Boogdrop"
        ver.nhb_nr = 1002
        ver.regio = regio
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.plaats = "Boogstad"
        ver.nhb_nr = 1000
        ver.regio = regio
        # secretaris kan nog niet ingevuld worden
        ver.save()

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

    def setUp(self):
        """ initialisatie van de test case """

        self.url_aanmaken = '/competitie/aanmaken/'
        self.url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        self.url_klassegrenzen_vaststellen_25 = '/competitie/klassegrenzen/vaststellen/25/'

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

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('verwijder_data_oude_site', stderr=f1, stdout=f2)

    def test_bepaal_1(self):
        self.assertEqual(Score.objects.count(), 0)
        self.assertEqual(ScoreHist.objects.count(), 0)

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('oude_site_overnemen', self.dir_testfiles1, '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] schutter 100001 heeft te laag AG (9.022) voor klasse Recurve klasse 2 (9.500)" in f2.getvalue())
        self.assertTrue("[WARNING] Kan lid 100042 niet vinden" in f2.getvalue())
        self.assertTrue("[WARNING] Kan lid 990000 niet vinden" in f2.getvalue())
        self.assertTrue("[WARNING] Verschil in lid 100004 naam: bekend=Juf de Schutter, oude programma=Juf de Schytter" in f2.getvalue())
        self.assertTrue("[WARNING] Sla dubbele invoer onder recurve (18m) over: 100002 (scores:" in f2.getvalue())
        self.assertTrue("[WARNING] Verwijder 1 dubbele inschrijvingen" in f2.getvalue())

        self.assertEqual(Score.objects.filter(is_ag=True).count(), 0)
        self.assertEqual(Score.objects.filter(is_ag=False).count(), 4)
        self.assertEqual(ScoreHist.objects.count(), 4)

        hist = ScoreHist.objects.all()[0]
        self.assertEqual(str(hist.when), '2020-09-29 22:00:00+00:00')

        # nog een keer, want dan zijn de uitslagen er al (extra coverage)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('oude_site_overnemen', self.dir_testfiles1, '1', stderr=f1, stdout=f2)

        self.assertEqual(ScoreHist.objects.count(), 4)

    def test_bepaal_2(self):
        # maak een AG aan voor schutter 100002-BB zodat we een verschil kunnen detecteren

        schutterboog = SchutterBoog(nhblid=self.lid_100002,
                                    boogtype=self.boog_bb,
                                    voor_wedstrijd=True)
        schutterboog.save()
        aanvangsgemiddelde_opslaan(schutterboog, 18, 4.444, None, 'test prep')

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('oude_site_overnemen', self.dir_testfiles2, '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        self.assertTrue("[ERROR] Kan wedstrijdklasse 'Barebow Cadetten klasse 1' niet vinden (competitie Indoor" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1099 is niet bekend; kan lid 100004 niet inschrijven" in f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Lid 100003 heeft 1 scores maar geen vereniging en wordt dus niet ingeschreven" in f2.getvalue())
        self.assertTrue("[WARNING] Verschil in AG voor nhbnr 100002 (18m): bekend=4.444, in uitslag=4.567" in f2.getvalue())

    def test_dryrun(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('oude_site_overnemen', '--dryrun', self.dir_testfiles1, '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("(DRY RUN)" in f2.getvalue())

    def test_all(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
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

# end of file
