# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import BOOGTYPE_AFKORTING_RECURVE
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Competitie.definities import DEEL_RK, INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieMatch,
                               Regiocompetitie, RegiocompetitieSporterBoog, RegiocompetitieRonde,
                               Kampioenschap)
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fases, zet_competitie_fase_regio_inschrijven
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Score.operations import score_indiv_ag_opslaan, score_teams_ag_opslaan
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from time import sleep
import datetime


class TestCompInschrijvenHWL(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_aanmelden = '/bondscompetities/deelnemen/leden-aanmelden/%s/'               # comp_pk
    url_ingeschreven = '/bondscompetities/deelnemen/leden-ingeschreven/%s/'         # deelcomp_pk
    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'                              # sporter_pk
    url_overzicht = '/vereniging/'
    url_voorkeuren = '/vereniging/leden-voorkeuren/'
    url_planning_regio = '/bondscompetities/regio/planning/%s/'                     # deelcomp_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/regio/planning/regio-wedstrijden/%s/'  # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/wijzig/%s/'  # match_pk

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

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

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
        sporter.save(update_fields=['account'])
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
        sporter.save()
        sporter.account = self.e2e_create_account(sporter.lid_nr,                       # heeft last_login=None
                                                  sporter.email, sporter.voornaam)
        sporter.save(update_fields=['account'])
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
                    geboorte_datum=datetime.date(year=jaar-13, month=3, day=4),  # 13=asp, maar 14 in 2e jaar comp
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
                    ver_nr="1222",
                    regio=self.regio_111)
        ver2.save()
        self.ver2 = ver2

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter(
                    lid_nr=102000,
                    geslacht="M",
                    voornaam="Andre",
                    achternaam="Club",
                    email="",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=jaar-4, month=11, day=12),
                    bij_vereniging=ver2)
        sporter.save()
        self.sporter_102000 = sporter

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        # fake een deelnemerslijst voor de RK
        deelkamp_rk = Kampioenschap.objects.get(competitie=self.comp_25,
                                                deel=DEEL_RK,
                                                rayon=self.regio_111.rayon)
        deelkamp_rk.heeft_deelnemerslijst = True
        deelkamp_rk.save()

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

    def _zet_sporter_voorkeuren(self, lid_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_sporter_voorkeuren = '/sporter/voorkeuren/'

        # maak de SporterBoog aan
        if lid_nr == 100003:
            resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_BB': 'on',
                                                             'schiet_R': 'on',         # 2 bogen
                                                             'info_R': 'on',
                                                             'voorkeur_meedoen_competitie': 'on'})
        elif lid_nr == 100012:
            # geen voorkeur voor meedoen met de competitie
            resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_BB': 'on',
                                                             'info_R': 'on'})

            # verwijder de voorkeur records
            SporterVoorkeuren.objects.filter(sporter__lid_nr=100012).delete()
        else:
            resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_R': 'on',
                                                             'info_C': 'on',
                                                             'voorkeur_meedoen_competitie': 'on'})

        self.assert_is_redirect(resp, self.url_voorkeuren)

    def _zet_ag(self, lid_nr, afstand, waarde=7.42):
        if lid_nr == 100003:
            sporterboog = SporterBoog.objects.get(sporter__lid_nr=lid_nr, boogtype__afkorting='BB')
            score_indiv_ag_opslaan(sporterboog, afstand, waarde, self.account_hwl, 'Test AG %s' % afstand)

        sporterboog = SporterBoog.objects.get(sporter__lid_nr=lid_nr, boogtype__afkorting='R')
        score_indiv_ag_opslaan(sporterboog, afstand, waarde, self.account_hwl, 'Test AG %s' % afstand)

    def _maak_wedstrijden(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # maak een aantal wedstrijden aan, als RCL van Regio 101
        functie_rcl = Functie.objects.get(rol='RCL', comp_type='18', regio=self.deelcomp_regio.regio)
        self.e2e_wissel_naar_functie(functie_rcl)

        # doe een POST om de eerste ronde aan te maken
        url = self.url_planning_regio % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

        ronde_pk = RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio).first().pk

        # haal de ronde planning op
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url_ronde)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)

        match_pk = CompetitieMatch.objects.first().pk

        # wijzig de instellingen van deze wedstrijd
        url_wed = self.url_wijzig_wedstrijd % match_pk
        with self.assert_max_queries(20):
            resp = self.client.post(url_wed, {'ver_pk': self.ver1.pk,
                                              'wanneer': '2020-12-11', 'aanvang': '12:34'})
        self.assert_is_redirect(resp, url_ronde)

        # maak nog een paar wedstrijden aan (voor later gebruik)
        for lp in range(7):
            with self.assert_max_queries(20):
                resp = self.client.post(url_ronde)
            self.assert_is_redirect_not_plein(resp)
        # for

        return [match_pk]

    def test_inschrijven(self):
        url = self.url_aanmelden % self.comp_18.pk

        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)

        # pas de HWL aan naar de andere club
        self.functie_hwl.vereniging = self.ver2
        self.functie_hwl.save()
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maakt sporterboog aan van andere vereniging
        self._zet_sporter_voorkeuren(102000)

        # herstel de HWL functie
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.save()

        # wordt HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # verkeerde competitie fase
        zet_competitie_fases(self.comp_18, 'A', 'A')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        # stel 1 schutter in die op randje aspirant/cadet zit
        self._zet_sporter_voorkeuren(100004)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, '>[100004] Cadet de Jeugd</')
        self.assertContains(resp, '>14</')                  # leeftijd 2021
        self.assertContains(resp, '>Onder 18</')            # leeftijdsklasse competitie

        # schrijf het jonge lid in en controleer de wedstrijdklasse
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on'})       # 1=R
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        inschrijving = RegiocompetitieSporterBoog.objects.first()
        self.assertEqual(inschrijving.sporterboog.sporter.lid_nr, 100004)
        self.assertTrue('Onder 18' in inschrijving.indiv_klasse.beschrijving)
        inschrijving.delete()

        # zet het min_ag voor Recurve klassen
        klasse_5 = None
        for klasse in (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=self.comp_18,
                               volgorde__in=(1100, 1101, 1102, 1103, 1104, 1105))):
            if klasse.volgorde == 1105:
                klasse.min_ag = 0.001
            elif klasse.volgorde == 1104:
                klasse.min_ag = 7.420
                klasse_5 = klasse
            else:
                klasse.min_ag = 9.000

            klasse.save(update_fields=['min_ag'])
        # for

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100002)
        self._zet_sporter_voorkeuren(100003)
        self._zet_sporter_voorkeuren(100012)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 18)
        self._zet_ag(100003, 25)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100012_boogtype_1': 'on'})      # heeft geen voorkeuren
        self.assert404(resp, 'Sporter heeft geen voorkeur voor wedstrijden opgegeven')

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',       # 1=R
                                          'lid_100003_boogtype_1': 'on'})      # 3=BB
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog__sporter__lid_nr=100003)
        # print('deelnemer:', deelnemer, 'klasse:', deelnemer.klasse)
        self.assertEqual(deelnemer.indiv_klasse, klasse_5)

        # dubbele inschrijving
        resp = self.client.post(url, {'lid_100002_boogtype_1': 'on'})
        self.assert404(resp, 'Sporter is al ingeschreven')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        # POST met garbage
        resp = self.client.post(url, {'lid_10xxx2_boogtype_1': 'on'})
        self.assert404(resp, 'Verkeerde parameters')

        resp = self.client.post(url, {'lid_999999_boogtype_1': 'on'})
        self.assert404(resp, 'Sporter niet gevonden')

        # haal het aanmeld-scherm op zodat er al ingeschreven leden bij staan
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # haal de lijst met ingeschreven schutters op
        url = self.url_ingeschreven % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-ingeschreven.dtl', 'plein/site_layout.dtl'))

    def test_inschrijven_methode3_twee_dagdelen(self):
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_3
        self.deelcomp_regio.toegestane_dagdelen = 'AV,ZO'
        self.deelcomp_regio.save()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100002)
        self._zet_sporter_voorkeuren(100003)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 25)

        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden met een verkeer dagdeel
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'ZA'})
        self.assert404(resp, 'Incompleet verzoek')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)

        # nu de POST om een paar leden aan te melden met een verkeer dagdeel
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'xx'})
        self.assert404(resp, 'Incompleet verzoek')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'dagdeel': 'AV',
                                          'opmerking': 'methode 3'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        for obj in RegiocompetitieSporterBoog.objects.all():
            self.assertEqual(obj.inschrijf_notitie, 'methode 3')
            self.assertTrue(obj.inschrijf_voorkeur_dagdeel, 'AV')
        # for

        # haal de lijst met ingeschreven schutters op
        url = self.url_ingeschreven % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-ingeschreven.dtl', 'plein/site_layout.dtl'))

    def test_inschrijven_methode3_alle_dagdelen(self):
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_3
        self.deelcomp_regio.toegestane_dagdelen = ''    # alles toegestaan
        self.deelcomp_regio.save()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100002)
        self._zet_sporter_voorkeuren(100003)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 25)

        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # probeer aan te melden met een niet-wedstrijd boog
        sporterboog = SporterBoog.objects.get(sporter__lid_nr=self.sporter_100002.lid_nr,
                                              boogtype__afkorting='R')
        sporterboog.voor_wedstrijd = False
        sporterboog.save()
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'AV'})
        self.assert404(resp, 'Sporter heeft geen voorkeur voor wedstrijden opgegeven')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        sporterboog.voor_wedstrijd = True
        sporterboog.save()

        # probeer aan te melden met een lid dat niet van de vereniging van de HWL is
        self.sporter_100002.bij_vereniging = self.ver2
        self.sporter_100002.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'AV'})
        self.assert403(resp)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        self.sporter_100002.bij_vereniging = self.ver1
        self.sporter_100002.save()

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'dagdeel': 'AV',
                                          'opmerking': 'methode 3' * 60})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)

        for obj in RegiocompetitieSporterBoog.objects.all():
            self.assertTrue(obj.inschrijf_notitie.startswith('methode 3'))
            self.assertTrue(obj.inschrijf_voorkeur_dagdeel, 'AV')
            self.assertTrue(480 < len(obj.inschrijf_notitie) <= 500)
        # for

    def test_inschrijven_methode1(self):
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio.toegestane_dagdelen = ''    # alles toegestaan
        self.deelcomp_regio.save()

        match_pks = self._maak_wedstrijden()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100002)
        self._zet_sporter_voorkeuren(100003)

        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        with self.assert_max_queries(25):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % match_pks[0]: 'on',
                                          'lid_100003_boogtype_3': 'on'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)    # 1 schutter, 1 competitie

        deelnemer = RegiocompetitieSporterBoog.objects.get(sporterboog__sporter__lid_nr=100003)
        self.assertEqual(deelnemer.inschrijf_gekozen_matches.count(), 1)

    def test_aanmelden_team(self):
        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100004)
        self._zet_sporter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'wil_in_team': 'ja',
                                          'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        for obj in RegiocompetitieSporterBoog.objects.all():
            self.assertEqual(obj.inschrijf_notitie, 'door de hwl')
            self.assertTrue(obj.inschrijf_voorkeur_team)
        # for

    def test_afmelden(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100004)
        self._zet_sporter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        zet_competitie_fase_regio_inschrijven(self.comp_18)

        url = self.url_aanmelden % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'wil_in_team': 'ja',
                                          'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        # schrijf een sporter uit
        pk = RegiocompetitieSporterBoog.objects.first().pk
        url = self.url_ingeschreven % 0
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'pk_%s' % pk: 'on'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)    # 1 schutter

        # schrijf een sporter uit van een andere vereniging
        inschrijving = RegiocompetitieSporterBoog.objects.first()
        inschrijving.bij_vereniging = self.ver2
        inschrijving.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'pk_%s' % inschrijving.pk: 'on'})
        self.assert403(resp)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)    # 1 schutter

    def test_cornercases(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_aanmelden % 9999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_aanmelden % 9999999)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_aanmelden % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'garbage': 'oh',
                                          'lid_GEENGETAL_boogtype_3': 'on'})
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(url, {'garbage': 'oh',
                                      'lid_999999_boogtype_GEENGETAL': 'on'})
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(url, {'lid_999999_boogtype_3': 'on'})       # 3=BB
        self.assert404(resp, 'Verkeerde competitie fase')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100003_boogtype_1': 'on'})       # 1=R = geen wedstrijdboog
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_ingeschreven % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde parameters')

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)     # redirect want POST kijkt niet naar deelcomp_pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'pk_hallo': 'on'})
        self.assert404(resp, 'Geen valide inschrijving')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'ignore': 'jaja', 'pk_null': 'on'})
        self.assert404(resp, 'Geen valide inschrijving')

        # extreem: aanmelden zonder passende klasse
        self._zet_sporter_voorkeuren(100002)
        self._zet_ag(100002, 18)
        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)
        # zet het min_ag te hoog
        for klasse in CompetitieIndivKlasse.objects.filter(competitie=self.comp_18,
                                                           boogtype__afkorting='R',
                                                           min_ag__lt=8.0):
            klasse.min_ag = 8.0     # > 7.42 van zet_ag
            klasse.save(update_fields=['min_ag'])
        # for
        # verwijder alle klassen 'onbekend'
        for klasse in CompetitieIndivKlasse.objects.filter(is_onbekend=True):
            klasse.is_onbekend = False
            klasse.save(update_fields=['is_onbekend'])
        # for
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on'})
        self.assert404(resp, 'Geen passende wedstrijdklasse')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)

    def test_administratief(self):
        # log in als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maak dit een administratieve regio waarvan de leden geen wedstrijden mogen schieten
        regio = self.ver1.regio
        regio.is_administratief = True
        regio.save()

        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Geen wedstrijden in deze regio')

    def test_met_ag_teams(self):
        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100004)
        self._zet_sporter_voorkeuren(100003)

        # self._zet_ag(100004, 18)       # geen AG, dan mag handmatig AG gebruikt worden
        self._zet_ag(100003, 25)

        sporterboog = SporterBoog.objects.get(sporter__lid_nr=100004,
                                              boogtype__afkorting=BOOGTYPE_AFKORTING_RECURVE)

        res = score_teams_ag_opslaan(sporterboog, 18, 8.25, self.account_hwl, 'Test')
        self.assertTrue(res)
        sleep(0.050)        # zorg iets van spreiding in de 'when'
        res = score_teams_ag_opslaan(sporterboog, 18, 8.18, self.account_hwl, 'Test')
        self.assertTrue(res)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(23):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'wil_in_team': 'ja',
                                          'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        for obj in RegiocompetitieSporterBoog.objects.all():
            self.assertEqual(obj.inschrijf_notitie, 'door de hwl')
            self.assertTrue(obj.inschrijf_voorkeur_team)
            if obj.sporterboog.sporter.lid_nr == 100004:
                self.assertTrue(obj.ag_voor_team_mag_aangepast_worden)
                self.assertEqual(str(obj.ag_voor_team), '8.180')
        # for

    def test_met_ag_prio(self):
        # controleer dat individueel AG prio heeft over handmatig ingevoerd AG
        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase_regio_inschrijven(self.comp_18)

        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_sporter_voorkeuren(100004)
        self._zet_sporter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        sporterboog = SporterBoog.objects.get(sporter__lid_nr=100004,
                                              boogtype__afkorting=BOOGTYPE_AFKORTING_RECURVE)

        res = score_teams_ag_opslaan(sporterboog, 18, 8.25, self.account_hwl, 'Test')
        self.assertTrue(res)
        sleep(0.050)  # zorg iets van spreiding in de 'when'
        res = score_teams_ag_opslaan(sporterboog, 18, 8.18, self.account_hwl, 'Test')
        self.assertTrue(res)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(23):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',  # 1=R
                                          'lid_100003_boogtype_3': 'on',  # 3=BB
                                          'wil_in_team': 'ja',
                                          'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)  # check success
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)  # 2 schutters, 1 competitie

        for obj in RegiocompetitieSporterBoog.objects.all():
            self.assertEqual(obj.inschrijf_notitie, 'door de hwl')
            self.assertTrue(obj.inschrijf_voorkeur_team)
            if obj.sporterboog.sporter.lid_nr == 100004:
                self.assertEqual(obj.ag_voor_team, obj.ag_voor_indiv)
                self.assertFalse(obj.ag_voor_team_mag_aangepast_worden)
        # for

# end of file
