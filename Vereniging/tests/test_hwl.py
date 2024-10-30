# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Competitie.definities import DEEL_RK, INSCHRIJF_METHODE_1
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieMatch,
                               Regiocompetitie, RegiocompetitieRonde,
                               Kampioenschap)
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import (zet_competitie_fase_regio_wedstrijden, zet_competitie_fase_rk_prep,
                                            zet_competitie_fase_regio_inschrijven, zet_competitie_fase_afsluiten)
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestVerenigingHWL(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_overzicht = '/vereniging/'
    url_ledenlijst = '/vereniging/leden-lijst/'
    url_leden_voorkeuren = '/vereniging/leden-voorkeuren/'
    url_sporter_voorkeuren = '/sporter/voorkeuren/'
    url_planning_regio = '/bondscompetities/regio/planning/%s/'                                     # deelcomp_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/regio/planning/regio-wedstrijden/%s/'    # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/wijzig/%s/'                  # match_pk
    url_wieschietwaar = '/bondscompetities/regio/wie-schiet-waar/%s/'                               # deelcomp_pk

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

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save()

        # maak het lid aan dat HWL wordt
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

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100001 = sporter

        jaar = timezone.now().year

        # maak een jeugdlid aan
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Jeugdschutter",
                    email="nietleeg@test.not",
                    geboorte_datum=datetime.date(year=jaar-10, month=3, day=4),
                    sinds_datum=datetime.date(year=jaar-3, month=11, day=12),
                    bij_vereniging=ver)
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)  # heeft last_login=None
        sporter.save()
        self.sporter_100002 = sporter

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        sporter = Sporter(
                    lid_nr=100012,
                    geslacht="V",
                    voornaam="Andrea",
                    achternaam="de Jeugdschutter",
                    email="",
                    geboorte_datum=datetime.date(year=jaar-10, month=3, day=4),
                    sinds_datum=datetime.date(year=jaar-3, month=10, day=10),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100012 = sporter

        # maak een jeugd lid aan
        sporter = Sporter(
                    lid_nr=100004,
                    geslacht="M",
                    voornaam="Cadet",
                    achternaam="de Jeugd",
                    email="",
                    geboorte_datum=datetime.date(year=jaar-13, month=3, day=4),    # 13=asp -> 14 in 2e jaar competitie
                    sinds_datum=datetime.date(year=jaar-3, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100004 = sporter

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter(
                    lid_nr=100003,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Testerin",
                    email="",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=jaar-4, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100003 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = Vereniging(
                    naam="Andere Club",
                    ver_nr=1222,
                    regio=self.regio_111)
        ver2.save()
        self.ver2 = ver2

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter(
                    lid_nr=102000,
                    geslacht="M",
                    voornaam="Andre",
                    achternaam="Club",
                    email="andre@nhn.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=jaar-4, month=11, day=12),
                    bij_vereniging=ver2)
        sporter.save()
        self.sporter_102000 = sporter

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        # fake een deelnemerslijst voor de RK
        deelkamp = Kampioenschap.objects.get(competitie=self.comp_25,
                                             deel=DEEL_RK,
                                             rayon=self.regio_111.rayon)
        deelkamp.heeft_deelnemerslijst = True
        deelkamp.save()
        self.deelcomp_rk = deelkamp

        ronde = RegiocompetitieRonde(
                    regiocompetitie=self.deelcomp_regio,
                    week_nr=99,
                    beschrijving='ronde')
        ronde.save()

        match = CompetitieMatch(
                        competitie=self.comp_25,
                        beschrijving='test',
                        vereniging=self.ver1,
                        datum_wanneer='2000-01-01',
                        tijd_begin_wedstrijd='00:00')
        match.save()
        ronde.matches.add(match)

    def _create_histcomp(self):
        # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
        hist_seizoen = HistCompSeizoen(seizoen='2018/2019', comp_type=HISTCOMP_TYPE_18,
                                       indiv_bogen=",".join(HIST_BOGEN_DEFAULT))
        hist_seizoen.save()

        # record voor het volwassen lid
        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=self.sporter_100001.lid_nr,
                    sporter_naam=self.sporter_100001.volledige_naam(),
                    vereniging_nr=self.ver1.ver_nr,
                    vereniging_naam=self.ver1.naam,
                    boogtype='R',
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    totaal=80,
                    gemiddelde=5.321)
        rec.save()

        # record voor het jeugdlid
        # record voor het volwassen lid
        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=self.sporter_100002.lid_nr,
                    sporter_naam=self.sporter_100002.volledige_naam(),
                    vereniging_nr=self.ver1.ver_nr,
                    vereniging_naam=self.ver1.naam,
                    boogtype='BB',
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    totaal=80,
                    gemiddelde=5.321)
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

        self.deelcomp_regio = Regiocompetitie.objects.get(regio=self.regio_111,
                                                          competitie__afstand=18)
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio.save()

        zet_competitie_fase_regio_inschrijven(self.comp_18)

        # maak nog een competitie aan waarvoor geen kaartjes getoond worden
        competities_aanmaken(jaar=2100)
        comp = Competitie.objects.get(afstand='25', begin_jaar=2100)
        zet_competitie_fase_afsluiten(comp)
        comp = Competitie.objects.get(afstand='18', begin_jaar=2100)
        zet_competitie_fase_afsluiten(comp)

    def _zet_sporter_voorkeuren(self, lid_nr):
        # deze functie kan alleen gebruikt worden als HWL

        # maak de SporterBoog aan
        resp = self.client.post(self.url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                              'schiet_R': 'on',
                                                              'info_C': 'on',
                                                              'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, self.url_leden_voorkeuren)

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
        zet_competitie_fase_regio_wedstrijden(self.comp_18)
        self.deelcomp_regio.huidige_team_ronde = 1
        self.deelcomp_regio.save()

        zet_competitie_fase_regio_wedstrijden(self.comp_25)
        deelcomp = Regiocompetitie.objects.get(competitie=self.comp_25,
                                               regio=self.regio_111)
        deelcomp.regio_organiseert_teamcompetitie = False
        deelcomp.save(update_fields=['regio_organiseert_teamcompetitie'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        zet_competitie_fase_rk_prep(self.comp_25)
        self.comp_25.begin_fase_F -= datetime.timedelta(days=100)       # forceer 'beschikbaar vanaf' label
        self.comp_25.save(update_fields=['begin_fase_F'])
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_indiv, 'J')

        RegiocompetitieRonde.objects.all().delete()

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

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp, skip_menu=True) if '/wie-schiet-waar/' in url]
        # print('urls als WL: %s' % urls)
        self.assertEqual(urls_expected, urls)

        # maak dit een administratieve vereniging
        self.ver1.regio = Regio.objects.filter(is_administratief=True).first()
        self.ver1.save(update_fields=['regio'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

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
            resp = self.client.get(self.url_leden_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # nog een keer, nu met sporterboog records aanwezig
        # zowel van de vereniging van de HWL als van andere verenigingen
        for sporter in (self.sporter_100001, self.sporter_100002, self.sporter_100003):
            # maak de sporterboog records aan
            resp = self.client.post(self.url_sporter_voorkeuren, {'sporter_pk': sporter.pk})
            self.assert_is_redirect(resp, self.url_leden_voorkeuren)
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
        self.sporter_100003.bij_vereniging = self.ver2
        self.sporter_100003.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_leden_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_locatie(self):
        # maak een locatie en koppel aan de vereniging
        loc = WedstrijdLocatie()
        # loc.adres = "Dubbelbaan 16\n1234AB Schietbuurt"
        loc.save()
        loc.verenigingen.add(self.ver1)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # check voor het kaartje om de doel details aan te passen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        urls2 = [url for url in urls if url.startswith('/vereniging/locatie/')]
        self.assertEqual(len(urls2), 2)

        # ophalen en aanpassen: zie test_accommodatie


# end of file
