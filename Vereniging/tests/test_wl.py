# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import Competitie, CompetitieIndivKlasse, LAAG_REGIO, DeelCompetitie
from Competitie.operations import competities_aanmaken
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingWL(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, functies voor de WL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_overzicht = '/vereniging/'
    url_ledenlijst = '/vereniging/leden-lijst/'
    url_voorkeuren = '/vereniging/leden-voorkeuren/'
    url_schutter_voorkeuren = '/sporter/voorkeuren/%s/'  # <sporter_pk>

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak het lid aan dat WL wordt
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_wl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_wl.accounts.add(self.account_wl)

        sporter.account = self.account_wl
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
        ver2.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

    def _create_histcomp(self):
        # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
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

        self.assertEqual(CompetitieIndivKlasse.objects.count(), 0)
        competities_aanmaken()
        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        self.deelcomp_regio = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                         nhb_regio=self.regio_111,
                                                         competitie__afstand=18)

    def test_overzicht(self):
        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

    def test_ledenlijst(self):
        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ledenlijst)
        self.assert403(resp)

        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/ledenlijst.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, 'Jeugdleden')
        self.assertContains(resp, 'Volwassenen')
        self.assertNotContains(resp, 'Inactieve leden')

    def test_voorkeuren(self):
        # haal de lijst met leden voorkeuren op
        # view is gebaseerd op ledenlijst, dus niet veel te testen

        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # het overzicht mag de WL ophalen
        self.assertEqual(SporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))

        # probeer de schutterboog instellingen van schutters te veranderen
        # maar dat mag de WL niet, dus gebeurt er niets
        for nhblid in (self.sporter_100001, self.sporter_100002, self.sporter_100003):
            url = self.url_schutter_voorkeuren % nhblid.pk
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assert403(resp)   # naar Plein, want mag niet
        # for
        self.assertEqual(SporterBoog.objects.count(), 0)

    def test_wedstrijdlocatie(self):
        # maak een locatie en koppel aan de vereniging
        loc = WedstrijdLocatie()
        # loc.adres = "Dubbelbaan 16\n1234AB Schietbuurt"
        loc.save()
        loc.verenigingen.add(self.nhbver1)

        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # check dat het kaartje er is om de accommodatie details op te vragen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        urls2 = [url for url in urls if url.startswith('/vereniging/accommodatie-details/')]
        self.assertEqual(len(urls2), 1)

        # ophalen en aanpassen: zie test_accommodatie

# end of file