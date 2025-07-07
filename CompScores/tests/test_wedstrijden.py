# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import (CompetitieMatch, CompetitieIndivKlasse,
                               Regiocompetitie, RegiocompetitieSporterBoog,
                               Kampioenschap)
from Competitie.operations import maak_regiocompetitie_ronde
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from Score.models import Score, Uitslag
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompScoresWedstrijden(E2EHelpers, TestCase):

    """ tests voor de CompScores applicatie, functies voor Wedstrijden """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_scores = '/bondscompetities/scores/bij-de-vereniging/'
    url_wedstrijden = '/bondscompetities/scores/wedstrijden-bij-de-vereniging/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.regio_111 = Regio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_111)
        ver.save()
        self.ver1 = ver

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save()

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        # maak het lid aan dat WL wordt
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
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
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Jeugdschutter",
                    email="",
                    geboorte_datum=datetime.date(year=2010, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100002 = sporter

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        sporter = Sporter(
                    lid_nr=100012,
                    geslacht="V",
                    voornaam="Andrea",
                    achternaam="de Jeugdschutter",
                    email="",
                    geboorte_datum=datetime.date(year=2010, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=10, day=10),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100012 = sporter

        # maak het lid aan dat HWL wordt
        sporter = Sporter(
                    lid_nr=100003,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Testerin",
                    email="ramonatesterin@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100003 = sporter

        # maak het lid aan dat SEC wordt
        sporter = Sporter(
                    lid_nr=100004,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Secretaris",
                    email="rdesecretaris@gmail.not",
                    geboorte_datum=datetime.date(year=1971, month=5, day=28),
                    sinds_datum=datetime.date(year=2000, month=1, day=31),
                    bij_vereniging=ver)
        sporter.save()

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        sporter.account = self.account_sec
        sporter.save()
        self.lid_100004 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = Vereniging(
                    naam="Andere Club",
                    ver_nr=1222,
                    regio=self.regio_111)
        ver2.save()
        self.ver2 = ver2

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
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_c()

        self.deelcomp_regio_18 = Regiocompetitie.objects.get(regio=self.regio_111,
                                                             competitie__afstand='18')

        self.deelcomp_regio_25 = Regiocompetitie.objects.get(regio=self.regio_111,
                                                             competitie__afstand='25')

        self.deelkamp18_rk1 = Kampioenschap.objects.filter(deel=DEEL_RK, competitie__afstand='18').order_by('rayon__rayon_nr')[0]
        self.deelkamp18_bk = Kampioenschap.objects.get(deel=DEEL_BK, competitie__afstand='18')

    def _maak_wedstrijden(self):
        self.wedstrijden = list()

        # maak een ronde + plan
        ronde = maak_regiocompetitie_ronde(self.deelcomp_regio_18, mag_database_wijzigen=True)
        self.ronde = ronde

        de_tijd = datetime.time(hour=20)

        # maak binnen het plan drie wedstrijden voor deze vereniging
        for volgnr in range(3):
            match = CompetitieMatch(
                        competitie=self.comp_18,
                        vereniging=self.ver1,
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

        # maak een RK wedstrijd
        match = CompetitieMatch(
                    competitie=self.comp_18,
                    vereniging=self.ver1,
                    datum_wanneer=datetime.date(year=2020, month=2, day=1),
                    tijd_begin_wedstrijd=de_tijd)
        match.save()
        self.deelkamp18_rk1.rk_bk_matches.add(match)

        # maak een BK wedstrijd
        match = CompetitieMatch(
                    competitie=self.comp_18,
                    vereniging=self.ver1,
                    datum_wanneer=datetime.date(year=2020, month=5, day=1),
                    tijd_begin_wedstrijd=de_tijd)
        match.save()
        self.deelkamp18_bk.rk_bk_matches.add(match)

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

        RegiocompetitieSporterBoog(
                regiocompetitie=self.deelcomp_regio_18,
                sporterboog=sporterboog,
                bij_vereniging=sporterboog.sporter.bij_vereniging,
                indiv_klasse=indiv_klasse).save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_25,
                                boogtype=boog_r,
                                is_onbekend=True))[0]

        RegiocompetitieSporterBoog(
                regiocompetitie=self.deelcomp_regio_25,
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

        aanmelding = RegiocompetitieSporterBoog(regiocompetitie=self.deelcomp_regio_18,
                                                sporterboog=sporterboog,
                                                bij_vereniging=sporterboog.sporter.bij_vereniging,
                                                indiv_klasse=indiv_klasse)
        aanmelding.save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_25,
                                boogtype=boog_c,
                                is_onbekend=False))[0]

        aanmelding = RegiocompetitieSporterBoog(regiocompetitie=self.deelcomp_regio_25,
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

        aanmelding = RegiocompetitieSporterBoog(regiocompetitie=self.deelcomp_regio_18,
                                                sporterboog=sporterboog,
                                                bij_vereniging=sporterboog.sporter.bij_vereniging,
                                                indiv_klasse=indiv_klasse)
        aanmelding.save()

        indiv_klasse = (CompetitieIndivKlasse
                        .objects
                        .filter(competitie=self.comp_25,
                                boogtype=boog_tr,
                                beschrijving__contains="Onder 12 Jongens"))[0]

        RegiocompetitieSporterBoog(
                regiocompetitie=self.deelcomp_regio_25,
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

        RegiocompetitieSporterBoog(
                regiocompetitie=self.deelcomp_regio_18,
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

        match = CompetitieMatch.objects.first()
        match.beschrijving = 'Hallo'
        match.save(update_fields=['beschrijving'])

        # haal de lijst van wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compscores/wedstrijden.dtl', 'plein/site_layout.dtl'))

        # trigger het "er zijn geen kampioenschappen" in de view code
        self.deelkamp18_rk1.rk_bk_matches.clear()
        self.deelkamp18_bk.rk_bk_matches.clear()

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)

    def test_wedstrijden_sec(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # geen toegang tot de pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assert403(resp)

# end of file
