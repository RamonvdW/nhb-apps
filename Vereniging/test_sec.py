# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import Competitie, CompetitieKlasse, RegioCompetitieSchutterBoog
from Competitie.test_fase import zet_competitie_fase
from Competitie.operations import competities_aanmaken
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingHWL(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, functies voor de SEC """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_overzicht = '/vereniging/'
    url_ledenlijst = '/vereniging/leden-lijst/'
    url_voorkeuren = '/vereniging/leden-voorkeuren/'
    url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'  # <comp_pk>
    url_ingeschreven = '/vereniging/leden-ingeschreven/competitie/%s/'  # <deelcomp_pk>
    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'  # <sporter_pk>

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        # maak de HWL functie
        # de functie is nodig zodat er BB er naartoe kan wisselen om schutterboog instellingen te doen
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        # maak het lid aan dat SEC wordt
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Secretaris"
        sporter.email = "rdesecretaris@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        sporter.account = self.account_sec
        sporter.save()
        self.sporter_100001 = sporter

        # maak een jeugdlid aan
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Jeugdschutter"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=2010, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100002 = sporter

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        sporter = Sporter()
        sporter.lid_nr = 100012
        sporter.geslacht = "V"
        sporter.voornaam = "Andrea"
        sporter.achternaam = "de Jeugdschutter"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=2010, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=10, day=10)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100012 = sporter

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100003 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

    def _create_histcomp(self):
        # (strategisch gekozen) historische data om klassegrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.klasse = 'Testcurve1'
        histcomp.is_team = False
        histcomp.save()

        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.schutter_nr = self.sporter_100001.lid_nr
        rec.schutter_naam = self.sporter_100001.volledige_naam()
        rec.vereniging_nr = self.nhbver1.ver_nr
        rec.vereniging_naam = self.nhbver1.naam
        rec.boogtype = 'R'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

        # record voor het jeugdlid
        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.schutter_nr = self.sporter_100002.lid_nr
        rec.schutter_naam = self.sporter_100002.volledige_naam()
        rec.vereniging_nr = self.nhbver1.ver_nr
        rec.vereniging_naam = self.nhbver1.naam
        rec.boogtype = 'BB'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

    def _create_competitie(self):
        # BB worden
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.assertEqual(CompetitieKlasse.objects.count(), 0)
        competities_aanmaken()
        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

    def test_overzicht(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

    def test_ledenlijst(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/ledenlijst.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, 'Jeugd')
        self.assertContains(resp, 'Senioren')
        self.assertNotContains(resp, 'Inactieve leden')

    def test_voorkeuren(self):
        # haal de lijst met leden voorkeuren op
        # view is gebaseerd op ledenlijst, dus niet veel te testen

        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # het overzicht mag de SEC ophalen
        self.assertEqual(SporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))

        # probeer de sporterboog instellingen van sporters te veranderen
        # maar dat mag de SEC niet, dus gebeurt er niets
        for sporter in (self.sporter_100001, self.sporter_100002, self.sporter_100003):
            url = self.url_sporter_voorkeuren % sporter.pk
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assert403(resp)
        # for
        self.assertEqual(SporterBoog.objects.count(), 0)

    def test_inschrijven(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)          # SEC mag dit niet

        # wissel door naar HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

    def test_administratieve_regio(self):
        # corner case: SEC van vereniging in administratieve regio

        # regio 100 is administratief
        regio100 = NhbRegio.objects.get(regio_nr=100)
        self.assertTrue(regio100.is_administratief)

        # account_sec is SEC bij self.nhbver1
        self.nhbver1.regio = regio100
        self.nhbver1.save()

        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)          # SEC mag dit niet

        # wissel door naar HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # pagina is wel op te halen, maar bevat geen leden die zich in kunnen schrijven
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # probeer iemand in te schrijven
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on'})       # 3=BB
        self.assert404(resp)     # 404 = Not found

    def test_ingeschreven(self):
        url = self.url_ingeschreven % 1

        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # SEC mag de lijst met ingeschreven sporters niet ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)          # SEC mag dit niet

    def test_wedstrijdlocatie(self):
        # maak een locatie en koppel aan de vereniging
        loc = WedstrijdLocatie()
        # loc.adres = "Dubbelbaan 16\n1234AB Schietbuurt"
        loc.save()
        loc.verenigingen.add(self.nhbver1)

        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # check voor het kaartje om de doel details aan te passen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        urls2 = [url for url in urls if url.startswith('/vereniging/accommodatie-details/')]
        self.assertEqual(len(urls2), 1)

        # ophalen en aanpassen: zie test_accommodatie

# end of file
