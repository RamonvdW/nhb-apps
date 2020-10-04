# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import Competitie, CompetitieKlasse, RegioCompetitieSchutterBoog
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Schutter.models import SchutterBoog
from Score.models import aanvangsgemiddelde_opslaan
from Wedstrijden.models import WedstrijdLocatie
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestVerenigingHWL(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Schutter', 'Competitie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BB aan, nodig om de competitie aan te maken
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
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
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Secretaris"
        lid.email = "rdesecretaris@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        self.account_sec = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        lid.account = self.account_sec
        lid.save()
        self.nhblid_100001 = lid

        # maak een jeugdlid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Jeugdschutter"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=2010, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100002 = lid

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        lid = NhbLid()
        lid.nhb_nr = 100012
        lid.geslacht = "V"
        lid.voornaam = "Andrea"
        lid.achternaam = "de Jeugdschutter"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=2010, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=10, day=10)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100012 = lid

        # maak een senior lid aan, om inactief te maken
        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100003 = lid

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.nhb_nr = "1222"
        ver2.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        self.url_overzicht = '/vereniging/'
        self.url_ledenlijst = '/vereniging/leden-lijst/'
        self.url_voorkeuren = '/vereniging/leden-voorkeuren/'
        self.url_inschrijven = '/vereniging/leden-inschrijven/competitie/%s/'    # <comp_pk>
        self.url_ingeschreven = '/vereniging/leden-ingeschreven/competitie/%s/'  # <deelcomp_pk>
        self.url_schutter_voorkeuren = '/schutter/voorkeuren/%s/'                # <nhblid_pk>

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
        rec.schutter_nr = self.nhblid_100001.nhb_nr
        rec.schutter_naam = self.nhblid_100001.volledige_naam()
        rec.vereniging_nr = self.nhbver1.nhb_nr
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
        rec.schutter_nr = self.nhblid_100002.nhb_nr
        rec.schutter_naam = self.nhblid_100002.volledige_naam()
        rec.vereniging_nr = self.nhbver1.nhb_nr
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
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        url_overzicht = '/competitie/'
        url_aanmaken = '/competitie/aanmaken/'
        url_klassegrenzen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        url_klassegrenzen_25 = '/competitie/klassegrenzen/vaststellen/25/'

        self.assertEqual(CompetitieKlasse.objects.count(), 0)

        resp = self.client.get(url_aanmaken)

        # competitie aanmaken
        resp = self.client.post(url_aanmaken)
        self.assert_is_redirect(resp, url_overzicht)

        # klassegrenzen vaststellen
        resp = self.client.post(url_klassegrenzen_18)
        self.assert_is_redirect(resp, url_overzicht)
        resp = self.client.post(url_klassegrenzen_25)
        self.assert_is_redirect(resp, url_overzicht)

        self.comp_18 = Competitie.objects.get(afstand=18)
        self.comp_25 = Competitie.objects.get(afstand=25)

    def test_overzicht(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

    def test_ledenlijst(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

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
        self.assertEqual(SchutterBoog.objects.count(), 0)
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))

        # probeer de schutterboog instellingen van schutters te veranderen
        # maar dat mag de SEC niet, dus gebeurt er niets
        for nhblid in (self.nhblid_100001, self.nhblid_100002, self.nhblid_100003):
            url = self.url_schutter_voorkeuren % nhblid.pk
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)     # 302 = Redirect == mag niet
        # for
        self.assertEqual(SchutterBoog.objects.count(), 0)

    def test_inschrijven(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        url = self.url_inschrijven % self.comp_18.pk
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')          # SEC mag dit niet

        # wissel door naar HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

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
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')          # SEC mag dit niet

        # wissel door naar HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # pagina is wel op te halen, maar bevat geen leden die zich in kunnen schrijven
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # probeer iemand in te schrijven
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                      'lid_100003_boogtype_3': 'on'})       # 3=BB
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_ingeschreven(self):
        url = self.url_ingeschreven % 1

        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # SEC mag de lijst met ingeschreven schutters niet ophalen
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')          # SEC mag dit niet

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
        resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        urls2 = [url for url in urls if url.startswith('/vereniging/accommodatie-details/')]
        self.assertEqual(len(urls2), 1)

        # ophalen en aanpassen: zie test_accommodatie

# end of file
