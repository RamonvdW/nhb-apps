# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import (CompetitieKlasse, DeelCompetitie, RegioCompetitieSchutterBoog,
                               LAAG_REGIO, INSCHRIJF_METHODE_1)
from Competitie.operations import maak_deelcompetitie_ronde
from Competitie.test_competitie import maak_competities_en_zet_fase_b
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdUitslag
from Score.models import Score
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingSchietmomenten(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor Schietmomenten """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_overzicht = '/vereniging/'
    url_schietmomenten = '/vereniging/leden-ingeschreven/competitie/%s/schietmomenten/'  # deelcomp_pk
    url_aanmelden = '/vereniging/leden-aanmelden/competitie/%s/'  # comp.pk
    url_sporter_schietmomenten = '/sporter/regiocompetitie/%s/schietmomenten/'  # regiocompetitieschutterboog.pk

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

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test 1000", "HWL")
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

        boog_ib = BoogType.objects.get(afkorting='IB')

        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=boog_ib,
                                  voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001 = sporterboog

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
        self.nhblid_100002 = sporter

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
        self.nhblid_100012 = sporter

        # maak het lid aan dat HWL wordt
        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = "ramonatesterin@nhb.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.nhblid_100003 = sporter

        # maak het lid aan dat SEC wordt
        sporter = Sporter()
        sporter.lid_nr = 100004
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Secretaris"
        sporter.email = "rdesecretaris@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1971, month=5, day=28)
        sporter.sinds_datum = datetime.date(year=2000, month=1, day=31)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        sporter.account = self.account_sec
        sporter.save()
        self.nhblid_100004 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # maak de HWL functie
        self.functie_hwl2 = maak_functie("HWL test 1222", "HWL")
        self.functie_hwl2.nhb_ver = ver2
        self.functie_hwl2.save()

        # maak een lid aan bij deze tweede vereniging
        sporter = Sporter()
        sporter.lid_nr = 120001
        sporter.geslacht = "M"
        sporter.voornaam = "Bij Twee"
        sporter.achternaam = "de Ver"
        sporter.email = "bijtweedever@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1971, month=5, day=28)
        sporter.sinds_datum = datetime.date(year=2000, month=1, day=31)
        sporter.bij_vereniging = ver2
        sporter.save()
        self.lid_120001 = sporter

        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=boog_ib,
                                  voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_120001 = sporterboog

        # BB worden
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competitie aan die nodig is voor deze tests
        self._create_competitie()
        self._maak_wedstrijden()
        self._maak_deelnemers()

        self.client.logout()

    def _create_competitie(self):
        url_kies = '/bondscompetities/'

        self.assertEqual(CompetitieKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_b()

        self.deelcomp_regio = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                         nhb_regio=self.regio_111,
                                                         competitie__afstand=18)

        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio.save()

    def _maak_wedstrijden(self):
        # maak een ronde + plan
        ronde = maak_deelcompetitie_ronde(self.deelcomp_regio)
        self.ronde = ronde

        de_tijd = datetime.time(hour=20)

        # maak binnen het plan drie wedstrijden voor deze vereniging
        for volgnr in range(3):
            wedstrijd = CompetitieWedstrijd(
                            vereniging=self.nhbver1,
                            datum_wanneer=datetime.date(year=2020, month=1, day=5+volgnr*3),
                            tijd_begin_aanmelden=de_tijd,
                            tijd_begin_wedstrijd=de_tijd,
                            tijd_einde_wedstrijd=de_tijd)

            if volgnr <= 1:
                uitslag = CompetitieWedstrijdUitslag(max_score=300, afstand_meter=12)
                uitslag.save()
                wedstrijd.uitslag = uitslag
                wedstrijd.beschrijving = "Dit is een testje %s" % volgnr

            if volgnr == 1:
                score = Score(sporterboog=self.sporterboog_100001,
                              waarde=123,
                              afstand_meter=12)
                score.save()
                uitslag.scores.add(score)

            wedstrijd.save()
            self.ronde_wedstrijd = wedstrijd
            ronde.plan.wedstrijden.add(wedstrijd)
        # for

        # maak voor de vereniging een wedstrijd die niets met de competitie te doen heeft
        wedstrijd = CompetitieWedstrijd(
                        vereniging=self.nhbver1,
                        datum_wanneer=datetime.date(year=2020, month=2, day=1),
                        tijd_begin_aanmelden=de_tijd,
                        tijd_begin_wedstrijd=de_tijd,
                        tijd_einde_wedstrijd=de_tijd)
        wedstrijd.save()
        self.wedstrijd = wedstrijd

    def _maak_deelnemers(self):
        url = self.url_aanmelden % self.comp_18.pk
        self.assertEqual(0, RegioCompetitieSchutterBoog.objects.count())

        self.e2e_wisselnaarrol_bb()
        self.e2e_wissel_naar_functie(self.functie_hwl2)

        resp = self.client.post(url, {'lid_%s_boogtype_%s' % (self.sporterboog_120001.sporter.pk,
                                                              self.sporterboog_120001.boogtype.pk): 'on',
                                      'wedstrijd_%s' % self.ronde_wedstrijd.pk: 'on'})
        self.assertEqual(resp.status_code, 302)     # 302 = success
        self.assertEqual(1, RegioCompetitieSchutterBoog.objects.count())

        self.e2e_wisselnaarrol_bb()
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.post(url, {'lid_%s_boogtype_%s' % (self.sporterboog_100001.sporter.pk,
                                                              self.sporterboog_100001.boogtype.pk): 'on',
                                      'wedstrijd_%s' % self.ronde_wedstrijd.pk: 'on'})
        self.assertEqual(resp.status_code, 302)     # 302 = success
        self.assertEqual(2, RegioCompetitieSchutterBoog.objects.count())

        self.deelnemer_100001 = RegioCompetitieSchutterBoog.objects.get(sporterboog=self.sporterboog_100001)
        self.deelnemer_120001 = RegioCompetitieSchutterBoog.objects.get(sporterboog=self.sporterboog_120001)

    def test_anon(self):
        url = self.url_schietmomenten % self.deelcomp_regio.pk
        resp = self.client.get(url)
        self.assert403(resp)      # redirect = access denied

    def test_kaartjes(self):
        # kaartje "Wie schiet waar?" moet getoond worden aan de HWL en WL
        # zolang de competitie in fase B..F is
        # en alleen voor een regio met inschrijfmethode 1

        url = self.url_schietmomenten % self.deelcomp_regio.pk
        urls_expected = [url]

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_overzicht)
        urls = [url for url in self.extract_all_urls(resp, skip_menu=True) if '/schietmomenten/' in url]
        # print('urls als HWL: %s' % urls)
        self.assertEqual(urls, urls_expected)

        # wissel naar WL rol
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        resp = self.client.get(self.url_overzicht)
        urls = [url for url in self.extract_all_urls(resp, skip_menu=True) if '/schietmomenten/' in url]
        # print('urls als WL: %s' % urls)
        self.assertEqual(urls, urls_expected)

        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        resp = self.client.get(self.url_overzicht)
        urls = [url for url in self.extract_all_urls(resp, skip_menu=True) if '/schietmomenten/' in url]
        # print('urls als SEC: %s' % urls)
        self.assertEqual(urls, [])

    def test_hwl(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_schietmomenten % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-schietmomenten-methode1.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

        urls = self.extract_all_urls(resp, skip_menu=True)
        url = self.url_sporter_schietmomenten % self.deelnemer_100001.pk
        self.assertEqual(urls, [url])

        # gebruiker de sporter pagina om de schietmomenten aan te passen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/schietmomenten.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # probeer schietmomenten van lid andere verenigingen aan te passen
        url = self.url_sporter_schietmomenten % self.deelnemer_120001.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_wl(self):
        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        url = self.url_schietmomenten % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-schietmomenten-methode1.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_bad(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_schietmomenten % 999999)
        self.assert404(resp)     # 404 = Not found

        # maak een hoop extra schutters aan
        basis = self.deelnemer_100001
        for lp in range(20):
            basis.pk = None
            basis.save()
        # for

        url = self.url_schietmomenten % self.deelcomp_regio.pk

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # verbouw de deelcompetitieronde zodat deze niet meer meegenomen wordt
        self.ronde.beschrijving = 'Ronde 0 oude programma'
        self.ronde.save()
        resp = self.client.get(self.url_schietmomenten % self.deelcomp_regio.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

# end of file
