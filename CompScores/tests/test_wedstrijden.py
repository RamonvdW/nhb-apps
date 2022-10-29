# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import (CompetitieIndivKlasse, DeelCompetitie, CompetitieMatch, LAAG_REGIO,
                               RegioCompetitieSchutterBoog)
from Competitie.operations import maak_deelcompetitie_ronde
from Competitie.tests.test_competitie import maak_competities_en_zet_fase_b
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from Score.models import Score, Uitslag
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompScoresWedstrijden(E2EHelpers, TestCase):

    """ tests voor de CompScores applicatie, functies voor Wedstrijden """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_scores = '/bondscompetities/scores/bij-de-vereniging/'
    url_wedstrijden = '/bondscompetities/scores/wedstrijden-bij-de-vereniging/'

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

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

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

        boog_r = BoogType.objects.get(afkorting='R')
        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=boog_r,
                                  voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001 = sporterboog

        voorkeuren = SporterVoorkeuren(sporter=self.sporter_100001,
                                       opmerking_para_sporter="test para opmerking")
        voorkeuren.save()

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
        self.sporter_100003 = sporter

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
        self.lid_100004 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        ver2.save()
        self.nhbver2 = ver2

        # BB worden
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competitie aan die nodig is voor deze tests
        self._maak_competitie()
        self._maak_wedstrijden()
        self._maak_inschrijvingen()

    def _maak_competitie(self):
        self.assertEqual(CompetitieIndivKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_b()

        self.deelcomp_regio_18 = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                            nhb_regio=self.regio_111,
                                                            competitie__afstand='18')

        self.deelcomp_regio_25 = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                            nhb_regio=self.regio_111,
                                                            competitie__afstand='25')

    def _maak_wedstrijden(self):
        self.wedstrijden = list()

        # maak een ronde + plan
        ronde = maak_deelcompetitie_ronde(self.deelcomp_regio_18)
        self.ronde = ronde

        de_tijd = datetime.time(hour=20)

        # maak binnen het plan drie wedstrijden voor deze vereniging
        for volgnr in range(3):
            match = CompetitieMatch(
                        competitie=self.comp_18,
                        vereniging=self.nhbver1,
                        datum_wanneer=datetime.date(year=2020, month=1, day=5+volgnr*3),
                        tijd_begin_wedstrijd=de_tijd)

            if volgnr <= 1:
                uitslag = Uitslag(max_score=300, afstand=12)
                uitslag.save()
                match.uitslag = uitslag
                match.beschrijving = "Test - Dit is een testje %s" % volgnr

                if volgnr == 1:
                    score = Score(sporterboog=self.sporterboog_100001,
                                  waarde=123,
                                  afstand_meter=12)
                    score.save()
                    uitslag.scores.add(score)

            match.save()
            ronde.matches.add(match)

            match.indiv_klassen.set(CompetitieIndivKlasse.objects.filter(competitie=self.comp_18))

            self.wedstrijden.append(match)
        # for

        # maak voor de vereniging een wedstrijd die niets met de competitie te doen heeft       TODO: no such thing
        match = CompetitieMatch(
                    competitie=self.comp_25,
                    vereniging=self.nhbver1,
                    datum_wanneer=datetime.date(year=2020, month=2, day=1),
                    tijd_begin_wedstrijd=de_tijd)
        match.save()

    def _maak_inschrijvingen(self):
        # schrijf iemand in
        boog_tr = BoogType.objects.get(afkorting='TR')
        boog_r = BoogType.objects.get(afkorting='R')
        boog_c = BoogType.objects.get(afkorting='C')

        # sporter 1 aanmelden

        sporterboog = self.sporterboog_100001

        SporterVoorkeuren(sporter=sporterboog.sporter, voorkeur_eigen_blazoen=True).save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_18,
                                boogtype=boog_r,
                                is_onbekend=True))[0]

        RegioCompetitieSchutterBoog(
                deelcompetitie=self.deelcomp_regio_18,
                sporterboog=sporterboog,
                bij_vereniging=sporterboog.sporter.bij_vereniging,
                indiv_klasse=indiv_klasse).save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_25,
                                boogtype=boog_r,
                                is_onbekend=True))[0]

        RegioCompetitieSchutterBoog(
                deelcompetitie=self.deelcomp_regio_25,
                sporterboog=sporterboog,
                bij_vereniging=sporterboog.sporter.bij_vereniging,
                indiv_klasse=indiv_klasse).save()

        # Schutter 2 aanmelden

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_18,
                                boogtype=boog_c,
                                is_onbekend=False))[0]

        sporterboog = SporterBoog(sporter=self.sporter_100002,
                                  boogtype=boog_c,
                                  voor_wedstrijd=True)
        sporterboog.save()

        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=self.deelcomp_regio_18,
                                                 sporterboog=sporterboog,
                                                 bij_vereniging=sporterboog.sporter.bij_vereniging,
                                                 indiv_klasse=indiv_klasse)
        aanmelding.save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_25,
                                boogtype=boog_c,
                                is_onbekend=False))[0]

        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=self.deelcomp_regio_25,
                                                 sporterboog=sporterboog,
                                                 bij_vereniging=sporterboog.sporter.bij_vereniging,
                                                 indiv_klasse=indiv_klasse)
        aanmelding.save()

        # aspirant schutter aanmelden
        self.sporter_100012.geboorte_datum = datetime.date(year=self.comp_18.begin_jaar - 10, month=1, day=1)
        self.sporter_100012.geslacht = 'M'
        self.sporter_100012.save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_18,
                                boogtype=boog_tr,
                                beschrijving__contains="Onder 12 Jongens"))[0]

        sporterboog = SporterBoog(sporter=self.sporter_100012,
                                  boogtype=boog_tr,
                                  voor_wedstrijd=True)
        sporterboog.save()

        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=self.deelcomp_regio_18,
                                                 sporterboog=sporterboog,
                                                 bij_vereniging=sporterboog.sporter.bij_vereniging,
                                                 indiv_klasse=indiv_klasse)
        aanmelding.save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_25,
                                boogtype=boog_tr,
                                beschrijving__contains="Onder 12 Jongens"))[0]

        RegioCompetitieSchutterBoog(
                deelcompetitie=self.deelcomp_regio_25,
                sporterboog=sporterboog,
                bij_vereniging=sporterboog.sporter.bij_vereniging,
                indiv_klasse=indiv_klasse).save()

        # Schutter 3 aanmelden
        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_18,
                                boogtype=boog_r))[0]

        sporterboog = SporterBoog(sporter=self.sporter_100003,
                                  boogtype=boog_r,
                                  voor_wedstrijd=True)
        sporterboog.save()

        RegioCompetitieSchutterBoog(
                deelcompetitie=self.deelcomp_regio_18,
                sporterboog=sporterboog,
                bij_vereniging=sporterboog.sporter.bij_vereniging,
                indiv_klasse=indiv_klasse).save()

    def test_wedstrijden_hwl(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal de lijst van wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compscores/wedstrijden.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)

        # haal de lijst van wedstrijden waarvan de uitslag ingevoerd mag worden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_scores)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compscores/wedstrijden.dtl', 'plein/site_layout.dtl'))

        urls2 = self.extract_all_urls(resp, skip_menu=True)
        url = None
        for url in urls2:
            self.assertTrue("/waarschijnlijke-deelnemers/" in url or url.startswith('/bondscompetities/scores/uitslag-invoeren/'))
        # for

        if url:     # pragma: no branch
            self.e2e_assert_other_http_commands_not_supported(url)

    def test_wedstrijden_wl(self):
        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        match = CompetitieMatch.objects.all()[0]
        match.beschrijving = 'Hallo'
        match.save(update_fields=['beschrijving'])

        # haal de lijst van wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compscores/wedstrijden.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)

    def test_wedstrijden_sec(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # haal de lijst van wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compscores/wedstrijden.dtl', 'plein/site_layout.dtl'))

        # geen toegang tot de pagina
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assert403(resp)

# end of file
