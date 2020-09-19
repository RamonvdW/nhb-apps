# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Competitie.models import RegioCompetitieSchutterBoog, DeelCompetitie, LAAG_REGIO
from NhbStructuur.models import NhbRegio, NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist
from Overig.e2ehelpers import E2EHelpers
from .models import CompetitieKlasse
import datetime
import io


class TestRecordsCliOudeSiteOvernemen(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command oude_site_overnemen """

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

    def test_bepaal(self):
        self.assertEqual(Score.objects.count(), 0)
        self.assertEqual(ScoreHist.objects.count(), 0)

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('oude_site_overnemen', './Competitie/management/testfiles/', '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Kan einde tabel onverwacht niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Kan einde regel onverwacht niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Kan einde wedstrijdklasse niet vinden: " in f1.getvalue())

        self.assertTrue("[WARNING] Lid 100003 heeft geen vereniging en wordt dus niet ingeschreven" in f2.getvalue())
        self.assertTrue("[WARNING] Verschil in vereniging naam: bekend=[1000] Grote Club, oude programma=[1000] Grootste Club" in f2.getvalue())
        self.assertTrue("[WARNING] schutter 100001 heeft te laag AG (9.022) voor klasse Recurve klasse 2 (9.500)" in f2.getvalue())
        self.assertTrue("[WARNING] Verschil in AG voor nhbnr 100001: bekend=9.022, in uitslag=8.022" in f2.getvalue())
        self.assertTrue("[WARNING] Kan lid 100042 niet vinden" in f2.getvalue())
        self.assertTrue("[WARNING] Kan lid 990000 niet vinden" in f2.getvalue())
        self.assertTrue("[WARNING] Verschil in lid 100004 naam: bekend=Juf de Schutter, oude programma=Juf de Schytter" in f2.getvalue())
        self.assertTrue("[WARNING] Sla dubbele invoer onder recurve (18m) over: 100002 (scores:" in f2.getvalue())
        self.assertTrue("[WARNING] Verwijder 1 dubbele inschrijvingen" in f2.getvalue())

        self.assertEqual(Score.objects.filter(is_ag=True).count(), 1)
        self.assertEqual(Score.objects.filter(is_ag=False).count(), 4)
        self.assertEqual(ScoreHist.objects.count(), 5)

        # nog een keer, want dan zijn de uitslagen er al (extra coverage)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(SystemExit):
            management.call_command('oude_site_overnemen', './Competitie/management/testfiles/', '1', stderr=f1, stdout=f2)

    def test_dryrun(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('oude_site_overnemen', '--dryrun', './Competitie/management/testfiles/', '100', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("(DRY RUN)" in f2.getvalue())

# end of file
