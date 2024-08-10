# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Competitie.definities import INSCHRIJF_METHODE_1
from Competitie.models import CompetitieMatch, CompetitieIndivKlasse, Regiocompetitie, RegiocompetitieSporterBoog
from Competitie.operations import maak_regiocompetitie_ronde
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Sporter.models import Sporter, SporterBoog
from Score.models import Score, Uitslag
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompLaagRegioWieSchietWaar(E2EHelpers, TestCase):

    """ tests voor de CompLaagRegio applicatie, functies voor Wie schiet waar """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_aanmelden = '/bondscompetities/deelnemen/leden-aanmelden/%s/'                      # comp.pk
    url_wieschietwaar = '/bondscompetities/regio/wie-schiet-waar/%s/'                      # deelcomp_pk
    url_sporter_zeven_wedstrijden = '/bondscompetities/regio/keuze-zeven-wedstrijden/%s/'  # deelnemer_pk

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
        self.functie_hwl = maak_functie("HWL test 1000", "HWL")
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

        boog_tr = BoogType.objects.get(afkorting='TR')

        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=boog_tr,
                                  voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100001 = sporterboog

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
        self.sporter_100004 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = Vereniging(
                    naam="Andere Club",
                    ver_nr=1222,
                    regio=self.regio_111)
        ver2.save()
        self.ver2 = ver2

        # maak de HWL functie
        self.functie_hwl2 = maak_functie("HWL test 1222", "HWL")
        self.functie_hwl2.vereniging = ver2
        self.functie_hwl2.save()

        # maak een lid aan bij deze tweede vereniging
        sporter = Sporter(
                    lid_nr=120001,
                    geslacht="M",
                    voornaam="Bij Twee",
                    achternaam="de Ver",
                    email="bijtweedever@gmail.not",
                    geboorte_datum=datetime.date(year=1971, month=5, day=28),
                    sinds_datum=datetime.date(year=2000, month=1, day=31),
                    bij_vereniging=ver2)
        sporter.save()
        self.sporter_120001 = sporter

        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=boog_tr,
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
        self.assertEqual(CompetitieIndivKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_c()

        self.deelcomp_regio = Regiocompetitie.objects.get(regio=self.regio_111,
                                                          competitie__afstand=18)

        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio.save()

    def _maak_wedstrijden(self):
        # maak een ronde + plan
        ronde = maak_regiocompetitie_ronde(self.deelcomp_regio, mag_database_wijzigen=True)
        self.ronde = ronde

        de_tijd = datetime.time(hour=20)

        # maak binnen het plan drie wedstrijden voor deze vereniging
        for volg_nr in range(3):
            match = CompetitieMatch(
                        competitie=self.deelcomp_regio.competitie,
                        vereniging=self.ver1,
                        datum_wanneer=datetime.date(year=2020, month=1, day=5+volg_nr*3),
                        tijd_begin_wedstrijd=de_tijd)

            if volg_nr <= 1:
                uitslag = Uitslag(max_score=300, afstand=12)
                uitslag.save()
                match.uitslag = uitslag
                match.beschrijving = "Dit is een testje %s" % volg_nr

                if volg_nr == 1:
                    score = Score(sporterboog=self.sporterboog_100001,
                                  waarde=123,
                                  afstand_meter=12)
                    score.save()
                    uitslag.scores.add(score)

            match.save()
            self.ronde_wedstrijd = match
            ronde.matches.add(match)
        # for

        # maak voor de vereniging een wedstrijd die niets met de competitie te doen heeft
        match = CompetitieMatch(
                    competitie=self.deelcomp_regio.competitie,
                    vereniging=self.ver1,
                    datum_wanneer=datetime.date(year=2020, month=2, day=1),
                    tijd_begin_wedstrijd=de_tijd)
        match.save()
        self.wedstrijd = match

    def _maak_deelnemers(self):
        url = self.url_aanmelden % self.comp_18.pk
        self.assertEqual(0, RegiocompetitieSporterBoog.objects.count())

        self.e2e_wisselnaarrol_bb()
        self.e2e_wissel_naar_functie(self.functie_hwl2)

        resp = self.client.post(url, {'lid_%s_boogtype_%s' % (self.sporterboog_120001.sporter.pk,
                                                              self.sporterboog_120001.boogtype.pk): 'on',
                                      'wedstrijd_%s' % self.ronde_wedstrijd.pk: 'on'})
        self.assertEqual(resp.status_code, 302)     # 302 = success
        self.assertEqual(1, RegiocompetitieSporterBoog.objects.count())

        self.e2e_wisselnaarrol_bb()
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.post(url, {'lid_%s_boogtype_%s' % (self.sporterboog_100001.sporter.pk,
                                                              self.sporterboog_100001.boogtype.pk): 'on',
                                      'wedstrijd_%s' % self.ronde_wedstrijd.pk: 'on'})
        self.assertEqual(resp.status_code, 302)     # 302 = success
        self.assertEqual(2, RegiocompetitieSporterBoog.objects.count())

        self.deelnemer_100001 = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_100001)
        self.deelnemer_120001 = RegiocompetitieSporterBoog.objects.get(sporterboog=self.sporterboog_120001)

    def test_anon(self):
        url = self.url_wieschietwaar % self.deelcomp_regio.pk
        resp = self.client.get(url)
        self.assert403(resp)      # redirect = access denied

    def test_hwl(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_wieschietwaar % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wieschietwaar-methode1.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

        urls = self.extract_all_urls(resp, skip_menu=True)
        url = self.url_sporter_zeven_wedstrijden % self.deelnemer_100001.pk
        self.assertEqual(urls, [url])

        # gebruiker de sporter pagina om de schietmomenten aan te passen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/keuze-zeven-wedstrijden-methode1.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # probeer schietmomenten van lid andere verenigingen aan te passen
        url = self.url_sporter_zeven_wedstrijden % self.deelnemer_120001.pk
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

        url = self.url_wieschietwaar % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/wieschietwaar-methode1.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_bad(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_wieschietwaar % 999999)
        self.assert404(resp, 'Geen valide competitie')

        # maak een hoop extra schutters aan
        basis = self.deelnemer_100001
        for lp in range(20):
            basis.pk = None
            basis.save()
        # for

        url = self.url_wieschietwaar % self.deelcomp_regio.pk

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

# end of file
