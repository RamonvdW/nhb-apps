# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import (Competitie, DeelCompetitie, CompetitieIndivKlasse, CompetitieMatch, DeelcompetitieRonde,
                               DeelKampioenschap, DEEL_RK, LAAG_REGIO, INSCHRIJF_METHODE_1)
from Competitie.operations import competities_aanmaken
from Competitie.tests.test_fase import zet_competitie_fase
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingHWL(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_overzicht = '/vereniging/'
    url_ledenlijst = '/vereniging/leden-lijst/'
    url_voorkeuren = '/vereniging/leden-voorkeuren/'
    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'                                              # sporter_pk
    url_planning_regio = '/bondscompetities/regio/planning/%s/'                                     # deelcomp_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/regio/planning/regio-wedstrijden/%s/'    # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/wijzig/%s/'                  # match_pk
    url_wieschietwaar = '/bondscompetities/regio/wie-schiet-waar/%s/'                               # deelcomp_pk

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
        ver.save()
        self.nhbver1 = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        # maak het lid aan dat HWL wordt
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

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100001 = sporter

        jaar = timezone.now().year

        # maak een jeugdlid aan
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Jeugdschutter"
        sporter.email = "nietleeg@nhb.not"
        sporter.geboorte_datum = datetime.date(year=jaar-10, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)  # heeft last_login=None
        sporter.save()
        self.sporter_100002 = sporter

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        sporter = Sporter()
        sporter.lid_nr = 100012
        sporter.geslacht = "V"
        sporter.voornaam = "Andrea"
        sporter.achternaam = "de Jeugdschutter"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=jaar-10, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-3, month=10, day=10)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100012 = sporter

        # maak een jeugd lid aan
        sporter = Sporter()
        sporter.lid_nr = 100004
        sporter.geslacht = "M"
        sporter.voornaam = "Cadet"
        sporter.achternaam = "de Jeugd"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=jaar-13, month=3, day=4)    # 13=asp, maar 14 in 2e jaar competitie!
        sporter.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100004 = sporter

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100003 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        ver2.save()
        self.nhbver2 = ver2

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter()
        sporter.lid_nr = 102000
        sporter.geslacht = "M"
        sporter.voornaam = "Andre"
        sporter.achternaam = "Club"
        sporter.email = "andre@nhn.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        sporter.bij_vereniging = ver2
        sporter.save()
        self.sporter_102000 = sporter

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        # fake een deelnemerslijst voor de RK
        deelkamp = DeelKampioenschap.objects.get(competitie=self.comp_25,
                                                 deel=DEEL_RK,
                                                 nhb_rayon=self.regio_111.rayon)
        deelkamp.heeft_deelnemerslijst = True
        deelkamp.save()
        self.deelcomp_rk = deelkamp

        ronde = DeelcompetitieRonde(
                    deelcompetitie=self.deelcomp_regio,
                    week_nr=99,
                    beschrijving='ronde')
        ronde.save()

        match = CompetitieMatch(
                        competitie=self.comp_25,
                        beschrijving='test',
                        vereniging=self.nhbver1,
                        datum_wanneer='2000-01-01',
                        tijd_begin_wedstrijd='00:00')
        match.save()
        ronde.matches.add(match)

    def _create_histcomp(self):
        # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.boog_str = 'Testcurve1'
        histcomp.is_team = False
        histcomp.save()

        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.sporter_lid_nr = self.sporter_100001.lid_nr
        rec.sporter_naam = self.sporter_100001.volledige_naam()
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
        rec.sporter_lid_nr = self.sporter_100002.lid_nr
        rec.sporter_naam = self.sporter_100002.volledige_naam()
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
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio.save()

        zet_competitie_fase(self.comp_18, 'B')

        # maak nog een competitie aan waarvoor geen kaartjes getoond worden
        competities_aanmaken(jaar=2100)
        comp = Competitie.objects.get(afstand='25', begin_jaar=2100)
        zet_competitie_fase(comp, 'S')
        comp = Competitie.objects.get(afstand='18', begin_jaar=2100)
        zet_competitie_fase(comp, 'S')

    def _zet_sporter_voorkeuren(self, lid_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_sporter_voorkeuren = '/sporter/voorkeuren/'

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SporterBoog records aan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_sporter_voorkeuren % lid_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        with self.assert_max_queries(23):
            resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_R': 'on',
                                                             'info_C': 'on',
                                                             'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, self.url_voorkeuren)

    def test_overzicht(self):
        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        # zet de competities door naar andere fases
        zet_competitie_fase(self.comp_18, 'E')
        self.deelcomp_regio.huidige_team_ronde = 1
        self.deelcomp_regio.save()

        zet_competitie_fase(self.comp_25, 'E')
        deelcomp = DeelCompetitie.objects.get(competitie=self.comp_25,
                                              laag=LAAG_REGIO,
                                              nhb_regio=self.regio_111)
        deelcomp.regio_organiseert_teamcompetitie = False
        deelcomp.save(update_fields=['regio_organiseert_teamcompetitie'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        zet_competitie_fase(self.comp_25, 'J')
        self.comp_25.eerste_wedstrijd -= datetime.timedelta(days=100)       # forceer 'beschikbaar vanaf' label
        self.comp_25.save(update_fields=['eerste_wedstrijd'])
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase, 'J')

        DeelcompetitieRonde.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_kaartjes(self):
        # kaartje "Wie schiet waar?" moet getoond worden aan de HWL en WL
        # zolang de competitie in fase B..F is
        # en alleen voor een regio met inschrijfmethode 1

        url = self.url_wieschietwaar % self.deelcomp_regio.pk
        urls_expected = [url]

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_overzicht)
        urls = [url for url in self.extract_all_urls(resp, skip_menu=True) if '/wie-schiet-waar/' in url]
        # print('urls als HWL: %s' % urls)
        self.assertEqual(urls_expected, urls)

        # wissel naar WL rol
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        resp = self.client.get(self.url_overzicht)
        urls = [url for url in self.extract_all_urls(resp, skip_menu=True) if '/wie-schiet-waar/' in url]
        # print('urls als WL: %s' % urls)
        self.assertEqual(urls_expected, urls)

        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        resp = self.client.get(self.url_overzicht)
        urls = [url for url in self.extract_all_urls(resp, skip_menu=True) if '/wie-schiet-waar/' in url]
        # print('urls als SEC: %s' % urls)
        self.assertEqual([], urls)

    def test_ledenlijst(self):
        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ledenlijst)
        self.assert403(resp)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/ledenlijst.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, 'Jeugdleden')
        self.assertContains(resp, 'Volwassenen')
        self.assertNotContains(resp, 'Inactieve leden')

        # maak een lid inactief
        self.sporter_100003.is_actief_lid = False
        self.sporter_100003.save()

        # stel ook een paar bogen in
        self._zet_sporter_voorkeuren(100002)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.assertContains(resp, 'Jeugdleden')
        self.assertContains(resp, 'Volwassenen')
        self.assertContains(resp, 'Inactieve leden')

        self.e2e_assert_other_http_commands_not_supported(self.url_ledenlijst)

    def test_voorkeuren(self):
        # haal de lijst met leden voorkeuren op
        # view is gebaseerd op ledenlijst, dus niet veel te testen

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # eerste keer, zonder sporterboog records
        self.assertEqual(SporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # nog een keer, nu met sporterboog records aanwezig
        # zowel van de vereniging van de HWL als van andere verenigingen
        for sporter in (self.sporter_100001, self.sporter_100002, self.sporter_100003):
            # get operatie maakt de sporterboog records aan
            url = self.url_sporter_voorkeuren % sporter.pk
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
        # for
        self.assertEqual(SporterBoog.objects.count(), 51)

        # zet een aantal sporterboog records op gebruik voor wedstrijd
        # dit maakt een sporterboog-boog
        for obj in SporterBoog.objects.all():
            if obj.pk & 1:  # odd?
                obj.voor_wedstrijd = True
                obj.save()
        # for

        # nu de sporterboog records gemaakt zijn (HWL had toestemming)
        # stoppen we 1 lid in een andere vereniging
        self.sporter_100003.bij_vereniging = self.nhbver2
        self.sporter_100003.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_wedstrijdlocatie(self):
        # maak een locatie en koppel aan de vereniging
        loc = WedstrijdLocatie()
        # loc.adres = "Dubbelbaan 16\n1234AB Schietbuurt"
        loc.save()
        loc.verenigingen.add(self.nhbver1)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # check voor het kaartje om de doel details aan te passen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        urls2 = [url for url in urls if url.startswith('/vereniging/accommodatie-details/')]
        self.assertEqual(len(urls2), 1)

        # ophalen en aanpassen: zie test_accommodatie


# end of file
