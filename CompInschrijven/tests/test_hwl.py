# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BOOGTYPE_AFKORTING_RECURVE
from Functie.operations import maak_functie, Functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import (Competitie, Regiocompetitie, CompetitieIndivKlasse, RegiocompetitieSporterBoog,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3,
                               Kampioenschap, DEEL_RK,
                               RegiocompetitieRonde, CompetitieMatch)
from Competitie.operations import competities_aanmaken
from Competitie.tests.test_helpers import zet_competitie_fase
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Score.operations import score_indiv_ag_opslaan, score_teams_ag_opslaan
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from time import sleep
import datetime


class TestCompInschrijvenHWL(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

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
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        sporter.bij_vereniging = ver2
        sporter.save()
        self.sporter_102000 = sporter

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        # fake een deelnemerslijst voor de RK
        deelkamp_rk = Kampioenschap.objects.get(competitie=self.comp_25,
                                                deel=DEEL_RK,
                                                nhb_rayon=self.regio_111.rayon)
        deelkamp_rk.heeft_deelnemerslijst = True
        deelkamp_rk.save()

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

        self.deelcomp_regio = Regiocompetitie.objects.get(nhb_regio=self.regio_111,
                                                          competitie__afstand=18)

    def _zet_sporter_voorkeuren(self, lid_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_sporter_voorkeuren = '/sporter/voorkeuren/'

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SporterBoog records aan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_sporter_voorkeuren % lid_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        if lid_nr == 100003:
            with self.assert_max_queries(24):
                resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_BB': 'on',
                                                                 'schiet_R': 'on',         # 2 bogen
                                                                 'info_R': 'on',
                                                                 'voorkeur_meedoen_competitie': 'on'})
        elif lid_nr == 100012:
            # geen voorkeur voor meedoen met de competitie
            with self.assert_max_queries(24):
                resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_BB': 'on',
                                                                 'info_R': 'on'})

            # verwijder de SchutterVoorkeur records
            SporterVoorkeuren.objects.filter(sporter__lid_nr=100012).delete()
        else:
            with self.assert_max_queries(23):
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
        functie_rcl = Functie.objects.get(rol='RCL', comp_type='18', nhb_regio=self.deelcomp_regio.nhb_regio)
        self.e2e_wissel_naar_functie(functie_rcl)

        url = self.url_planning_regio % self.deelcomp_regio.pk

        # haal de (lege) planning op. Dit maakt ook meteen de enige ronde aan
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        ronde_pk = RegiocompetitieRonde.objects.filter(regiocompetitie=self.deelcomp_regio)[0].pk

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

        match_pk = CompetitieMatch.objects.all()[0].pk

        # wijzig de instellingen van deze wedstrijd
        url_wed = self.url_wijzig_wedstrijd % match_pk
        with self.assert_max_queries(20):
            resp = self.client.post(url_wed, {'nhbver_pk': self.nhbver1.pk,
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
        self.functie_hwl.nhb_ver = self.nhbver2
        self.functie_hwl.save()
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maakt sporterboog aan van andere vereniging
        self._zet_sporter_voorkeuren(102000)

        # herstel de HWL functie
        self.functie_hwl.nhb_ver = self.nhbver1
        self.functie_hwl.save()

        # wordt HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # verkeerde competitie fase
        zet_competitie_fase(self.comp_18, 'A')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')
        zet_competitie_fase(self.comp_18, 'B')

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

        inschrijving = RegiocompetitieSporterBoog.objects.all()[0]
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

        with self.assert_max_queries(26):
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
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on'})
        self.assert404(resp, 'Sporter is al ingeschreven')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        # POST met garbage
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_10xxx2_boogtype_1': 'on'})
        self.assert404(resp, 'Verkeerde parameters')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_999999_boogtype_1': 'on'})
        self.assert404(resp, 'Sporter niet gevonden')

        # haal het aanmeld-scherm op zodat er al ingeschreven leden bij staan
        with self.assert_max_queries(26):
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
        zet_competitie_fase(self.comp_18, 'B')

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
        zet_competitie_fase(self.comp_18, 'B')

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
        self.sporter_100002.bij_vereniging = self.nhbver2
        self.sporter_100002.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'AV'})
        self.assert403(resp)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        self.sporter_100002.bij_vereniging = self.nhbver1
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
        zet_competitie_fase(self.comp_18, 'B')

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
        zet_competitie_fase(self.comp_18, 'B')

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

    def test_inschrijven_team_udvl(self):
        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        # zet de udvl tussen de dvl van de twee schutters in
        # sporter_100003.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        # sporter_100004.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        self.comp_18.uiterste_datum_lid = datetime.date(year=self.sporter_100004.sinds_datum.year, month=1, day=1)
        self.comp_18.save()

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
            if obj.sporterboog.sporter.lid_nr == 100003:
                self.assertTrue(obj.inschrijf_voorkeur_team)
            else:
                # 100004 heeft dvl > udvl, dus mag niet mee doen
                self.assertFalse(obj.inschrijf_voorkeur_team)
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

        zet_competitie_fase(self.comp_18, 'B')

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

        # schrijf de schutters weer uit
        pk = RegiocompetitieSporterBoog.objects.all()[0].pk
        url = self.url_ingeschreven % 0
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'pk_%s' % pk: 'on'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)    # 1 schutter

        # schrijf een schutter uit van een andere vereniging
        inschrijving = RegiocompetitieSporterBoog.objects.all()[0]
        inschrijving.bij_vereniging = self.nhbver2
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

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmelden % 9999999)
        self.assert404(resp, 'Competitie niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % 9999999)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_aanmelden % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'garbage': 'oh',
                                          'lid_GEENGETAL_boogtype_3': 'on'})
        self.assert404(resp, 'Verkeerde competitie fase')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'garbage': 'oh',
                                          'lid_999999_boogtype_GEENGETAL': 'on'})
        self.assert404(resp, 'Verkeerde competitie fase')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_999999_boogtype_3': 'on'})       # 3=BB
        self.assert404(resp, 'Verkeerde competitie fase')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100003_boogtype_1': 'on'})       # 1=R = geen wedstrijdboog
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_ingeschreven % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde parameters')

        with self.assert_max_queries(20):
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
        zet_competitie_fase(self.comp_18, 'B')
        # zet het min_ag te hoog
        for klasse in CompetitieIndivKlasse.objects.filter(competitie=self.comp_18, boogtype__afkorting='R', min_ag__lt=8.0):
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
        regio = self.nhbver1.regio
        regio.is_administratief = True
        regio.save()

        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Geen wedstrijden in deze regio')

    def test_met_ag_teams(self):
        url = self.url_aanmelden % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

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
                self.assertEqual(str(obj.ag_voor_team), '8.180')
        # for

# end of file
