# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import maak_functie, Functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse, RegioCompetitieSchutterBoog,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3, LAAG_REGIO, LAAG_RK,
                               DeelcompetitieRonde)
from Competitie.operations import competities_aanmaken
from Competitie.test_fase import zet_competitie_fase
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Schutter.models import SchutterBoog, SchutterVoorkeuren
from Score.operations import score_indiv_ag_opslaan
from Wedstrijden.models import WedstrijdLocatie, CompetitieWedstrijd
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingHWL(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Schutter', 'Competitie')

    url_overzicht = '/vereniging/'
    url_ledenlijst = '/vereniging/leden-lijst/'
    url_voorkeuren = '/vereniging/leden-voorkeuren/'
    url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'  # <comp_pk>
    url_ingeschreven = '/vereniging/leden-ingeschreven/competitie/%s/'  # <deelcomp_pk>
    url_wijzig_ag = '/vereniging/leden-ingeschreven/wijzig-aanvangsgemiddelde/%s/'  # <deelnemer_pk>
    url_schutter_voorkeuren = '/sporter/voorkeuren/%s/'  # <nhblid_pk>
    url_planning_regio = '/bondscompetities/planning/regio/%s/'  # deelcomp_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/planning/regio/regio-wedstrijden/%s/'  # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/planning/regio/wedstrijd/wijzig/%s/'  # wedstrijd_pk

    testdata = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak het lid aan dat HWL wordt
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        self.account_hwl = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        lid.account = self.account_hwl
        lid.save()
        self.nhblid_100001 = lid

        jaar = timezone.now().year

        # maak een jeugdlid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Jeugdschutter"
        lid.email = "nietleeg@nhb.not"
        lid.geboorte_datum = datetime.date(year=jaar-10, month=3, day=4)
        lid.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)  # heeft last_login=None
        lid.save()
        self.nhblid_100002 = lid

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        lid = NhbLid()
        lid.nhb_nr = 100012
        lid.geslacht = "V"
        lid.voornaam = "Andrea"
        lid.achternaam = "de Jeugdschutter"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=jaar-10, month=3, day=4)
        lid.sinds_datum = datetime.date(year=jaar-3, month=10, day=10)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100012 = lid

        # maak een jeugd lid aan
        lid = NhbLid()
        lid.nhb_nr = 100004
        lid.geslacht = "M"
        lid.voornaam = "Cadet"
        lid.achternaam = "de Jeugd"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=jaar-13, month=3, day=4)    # 13=asp, maar 14 in 2e jaar competitie!
        lid.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100004 = lid

        # maak een senior lid aan, om inactief te maken
        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100003 = lid

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # maak een senior lid aan, om inactief te maken
        lid = NhbLid()
        lid.nhb_nr = 102000
        lid.geslacht = "M"
        lid.voornaam = "Andre"
        lid.achternaam = "Club"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        lid.bij_vereniging = ver2
        lid.save()
        self.nhblid_102000 = lid

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        # fake een deelnemerslijst voor de RK
        deelcomp_rk = DeelCompetitie.objects.get(competitie=self.comp_25,
                                                 laag=LAAG_RK,
                                                 nhb_rayon=self.regio_111.rayon)
        deelcomp_rk.heeft_deelnemerslijst = True
        deelcomp_rk.save()

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
        rec.schutter_nr = self.nhblid_100002.nhb_nr
        rec.schutter_naam = self.nhblid_100002.volledige_naam()
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

        self.assertEqual(CompetitieKlasse.objects.count(), 0)
        competities_aanmaken()
        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        self.deelcomp_regio = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                         nhb_regio=self.regio_111,
                                                         competitie__afstand=18)

    def _zet_schutter_voorkeuren(self, nhb_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_schutter_voorkeuren = '/sporter/voorkeuren/'

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SchutterBoog records aan
        with self.assert_max_queries(20):
            resp = self.client.get(url_schutter_voorkeuren + '%s/' % nhb_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        if nhb_nr == 100003:
            with self.assert_max_queries(20):
                resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                  'schiet_BB': 'on',
                                                                  'schiet_R': 'on',         # 2 bogen
                                                                  'info_R': 'on',
                                                                  'voorkeur_meedoen_competitie': 'on'})
        elif nhb_nr == 100012:
            # geen voorkeur voor meedoen met de competitie
            with self.assert_max_queries(20):
                resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                  'schiet_BB': 'on',
                                                                  'info_R': 'on'})

            # verwijder de SchutterVoorkeur records
            SchutterVoorkeuren.objects.filter(nhblid__nhb_nr=100012).delete()
        else:
            with self.assert_max_queries(20):
                resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                  'schiet_R': 'on',
                                                                  'info_C': 'on',
                                                                  'voorkeur_meedoen_competitie': 'on'})

        self.assert_is_redirect(resp, self.url_voorkeuren)

    def _zet_ag(self, nhb_nr, afstand, waarde=7.42):
        if nhb_nr == 100003:
            schutterboog = SchutterBoog.objects.get(nhblid__nhb_nr=nhb_nr, boogtype__afkorting='BB')
            score_indiv_ag_opslaan(schutterboog, afstand, waarde, self.account_hwl, 'Test AG %s' % afstand)

        schutterboog = SchutterBoog.objects.get(nhblid__nhb_nr=nhb_nr, boogtype__afkorting='R')
        score_indiv_ag_opslaan(schutterboog, afstand, waarde, self.account_hwl, 'Test AG %s' % afstand)

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

        ronde_pk = DeelcompetitieRonde.objects.filter(deelcompetitie=self.deelcomp_regio)[0].pk

        # haal de ronde planning op
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url_ronde)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # maak een wedstrijd aan
        self.assertEqual(CompetitieWedstrijd.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)

        wedstrijd_pk = CompetitieWedstrijd.objects.all()[0].pk

        # wijzig de instellingen van deze wedstrijd
        url_wed = self.url_wijzig_wedstrijd % wedstrijd_pk
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

        return [wedstrijd_pk]

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

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

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

        self.assertContains(resp, 'Jeugd')
        self.assertContains(resp, 'Senioren')
        self.assertNotContains(resp, 'Inactieve leden')

        # maak een lid inactief
        self.nhblid_100003.is_actief_lid = False
        self.nhblid_100003.save()

        # stel ook een paar bogen in
        self._zet_schutter_voorkeuren(100002)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.assertContains(resp, 'Jeugd')
        self.assertContains(resp, 'Senioren')
        self.assertContains(resp, 'Inactieve leden')

        self.e2e_assert_other_http_commands_not_supported(self.url_ledenlijst)

    def test_voorkeuren(self):
        # haal de lijst met leden voorkeuren op
        # view is gebaseerd op ledenlijst, dus niet veel te testen

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # eerste keer, zonder schutterboog records
        self.assertEqual(SchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # nog een keer, nu met schutterboog records aanwezig
        # zowel van de vereniging van de HWL als van andere verenigingen
        for nhblid in (self.nhblid_100001, self.nhblid_100002, self.nhblid_100003):
            # get operatie maakt de schutterboog records aan
            url = self.url_schutter_voorkeuren % nhblid.pk
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
        # for
        self.assertEqual(SchutterBoog.objects.count(), 15)

        # zet een aantal schutterboog records op gebruik voor wedstrijd
        # dit maakt een schutter-boog
        for obj in SchutterBoog.objects.all():
            if obj.pk & 1:  # odd?
                obj.voor_wedstrijd = True
                obj.save()
        # for

        # nu de schutterboog records gemaakt zijn (HWL had toestemming)
        # stoppen we 1 lid in een andere vereniging
        self.nhblid_100003.bij_vereniging = self.nhbver2
        self.nhblid_100003.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_inschrijven(self):
        url = self.url_inschrijven % self.comp_18.pk

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

        # maakt SchutterBoog aan van andere vereniging
        self._zet_schutter_voorkeuren(102000)

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
        self.assert404(resp)
        zet_competitie_fase(self.comp_18, 'B')

        # stel 1 schutter in die op randje aspirant/cadet zit
        self._zet_schutter_voorkeuren(100004)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, '<td>Cadet de Jeugd</td>')
        self.assertContains(resp, '<td>14</td>')            # leeftijd 2021
        self.assertContains(resp, '<td class="hide-on-small-only">Cadet</td>')  # leeftijdsklasse competitie

        # schrijf het jonge lid in en controleer de wedstrijdklasse
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on'})       # 1=R
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertEqual(inschrijving.schutterboog.nhblid.nhb_nr, 100004)
        self.assertTrue('Cadet' in inschrijving.klasse.indiv.beschrijving)
        inschrijving.delete()

        # zet het min_ag voor Recurve klassen
        klasse_5 = None
        for klasse in (CompetitieKlasse
                       .objects
                       .filter(competitie=self.comp_18,
                               indiv__volgorde__in=(100, 101, 102, 103, 104, 105))):
            if klasse.indiv.volgorde == 105:
                klasse.min_ag = 0.001
            elif klasse.indiv.volgorde == 104:
                klasse.min_ag = 7.420
                klasse_5 = klasse
            else:
                klasse.min_ag = 9.000

            klasse.save(update_fields=['min_ag'])
        # for

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)
        self._zet_schutter_voorkeuren(100003)
        self._zet_schutter_voorkeuren(100012)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 18)
        self._zet_ag(100003, 25)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100012_boogtype_1': 'on'})      # heeft geen voorkeuren
        self.assert404(resp, 'Sporter heeft geen voorkeur voor wedstrijden opgegeven')

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',       # 1=R
                                          'lid_100003_boogtype_1': 'on'})      # 3=BB
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog__nhblid__nhb_nr=100003)
        # print('deelnemer:', deelnemer, 'klasse:', deelnemer.klasse)
        self.assertEqual(deelnemer.klasse, klasse_5)

        # dubbele inschrijving
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on'})
        self.assert404(resp)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        # POST met garbage
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_10xxx2_boogtype_1': 'on'})
        self.assert404(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_999999_boogtype_1': 'on'})
        self.assert404(resp)

        # haal het aanmeld-scherm op zodat er al ingeschreven leden bij staan
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # haal de lijst met ingeschreven schutters op
        url = self.url_ingeschreven % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-ingeschreven.dtl', 'plein/site_layout.dtl'))

    def test_inschrijven_methode3_twee_dagdelen(self):
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_3
        self.deelcomp_regio.toegestane_dagdelen = 'AV,ZO'
        self.deelcomp_regio.save()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 25)

        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden met een verkeer dagdeel
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'ZA'})
        self.assert404(resp)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

        # nu de POST om een paar leden aan te melden met een verkeer dagdeel
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'xx'})
        self.assert404(resp)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'dagdeel': 'AV',
                                          'opmerking': 'methode 3'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        for obj in RegioCompetitieSchutterBoog.objects.all():
            self.assertEqual(obj.inschrijf_notitie, 'methode 3')
            self.assertTrue(obj.inschrijf_voorkeur_dagdeel, 'AV')
        # for

        # haal de lijst met ingeschreven schutters op
        url = self.url_ingeschreven % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-ingeschreven.dtl', 'plein/site_layout.dtl'))

    def test_inschrijven_methode3_alle_dagdelen(self):
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_3
        self.deelcomp_regio.toegestane_dagdelen = ''    # alles toegestaan
        self.deelcomp_regio.save()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 25)

        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # probeer aan te melden met een niet-wedstrijd boog
        schutterboog = SchutterBoog.objects.get(nhblid__nhb_nr=self.nhblid_100002.nhb_nr,
                                                boogtype__afkorting='R')
        schutterboog.voor_wedstrijd = False
        schutterboog.save()
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'AV'})
        self.assert404(resp)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog.voor_wedstrijd = True
        schutterboog.save()

        # probeer aan te melden met een lid dat niet van de vereniging van de HWL is
        self.nhblid_100002.bij_vereniging = self.nhbver2
        self.nhblid_100002.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'dagdeel': 'AV'})
        self.assert403(resp)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        self.nhblid_100002.bij_vereniging = self.nhbver1
        self.nhblid_100002.save()

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'dagdeel': 'AV',
                                          'opmerking': 'methode 3' * 60})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)

        for obj in RegioCompetitieSchutterBoog.objects.all():
            self.assertTrue(obj.inschrijf_notitie.startswith('methode 3'))
            self.assertTrue(obj.inschrijf_voorkeur_dagdeel, 'AV')
            self.assertTrue(480 < len(obj.inschrijf_notitie) <= 500)
        # for

    def test_inschrijven_methode1(self):
        self.deelcomp_regio.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp_regio.toegestane_dagdelen = ''    # alles toegestaan
        self.deelcomp_regio.save()

        wedstrijd_pks = self._maak_wedstrijden()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)
        self._zet_schutter_voorkeuren(100003)

        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        with self.assert_max_queries(21):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % wedstrijd_pks[0]: 'on',
                                          'lid_100003_boogtype_3': 'on'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)    # 1 schutter, 1 competitie

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog__nhblid__nhb_nr=100003)
        self.assertEqual(deelnemer.inschrijf_gekozen_wedstrijden.count(), 1)

    def test_inschrijven_team(self):
        url = self.url_inschrijven % self.comp_18.pk
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
        self._zet_schutter_voorkeuren(100004)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'wil_in_team': 'ja',
                                          'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        for obj in RegioCompetitieSchutterBoog.objects.all():
            self.assertEqual(obj.inschrijf_notitie, 'door de hwl')
            self.assertTrue(obj.inschrijf_voorkeur_team)
        # for

    def test_inschrijven_team_udvl(self):
        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        # zet de udvl tussen de dvl van de twee schutters in
        # nhblid_100003.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        # nhblid_100004.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        self.comp_18.uiterste_datum_lid = datetime.date(year=self.nhblid_100004.sinds_datum.year, month=1, day=1)
        self.comp_18.save()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100004)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'wil_in_team': 'ja',
                                          'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        for obj in RegioCompetitieSchutterBoog.objects.all():
            self.assertEqual(obj.inschrijf_notitie, 'door de hwl')
            if obj.schutterboog.nhblid.nhb_nr == 100003:
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
        self._zet_schutter_voorkeuren(100004)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        zet_competitie_fase(self.comp_18, 'B')

        url = self.url_inschrijven % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on',        # 3=BB
                                          'wil_in_team': 'ja',
                                          'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        # schrijf de schutters weer uit
        pk = RegioCompetitieSchutterBoog.objects.all()[0].pk
        url = self.url_ingeschreven % 0
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'pk_%s' % pk: 'on'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)    # 1 schutter

        # schrijf een schutter uit van een andere vereniging
        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        inschrijving.bij_vereniging = self.nhbver2
        inschrijving.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'pk_%s' % inschrijving.pk: 'on'})
        self.assert403(resp)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)    # 1 schutter

    def test_cornercases(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven % 9999999)
        self.assert404(resp)         # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven % 9999999)
        self.assert404(resp)         # 404 = Not allowed

        url = self.url_inschrijven % self.comp_18.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'garbage': 'oh',
                                          'lid_GEENGETAL_boogtype_3': 'on'})
        self.assert404(resp)     # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'garbage': 'oh',
                                          'lid_999999_boogtype_GEENGETAL': 'on'})
        self.assert404(resp)     # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_999999_boogtype_3': 'on'})       # 3=BB
        self.assert404(resp)     # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100003_boogtype_1': 'on'})       # 1=R = geen wedstrijdboog
        self.assert404(resp)     # 404 = Not allowed

        url = self.url_ingeschreven % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)     # redirect want POST kijkt niet naar deelcomp_pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'pk_hallo': 'on'})
        self.assert404(resp)     # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'ignore': 'jaja', 'pk_null': 'on'})
        self.assert404(resp)  # 404 = Not allowed

        # extreem: aanmelden zonder passende klasse
        self._zet_schutter_voorkeuren(100002)
        self._zet_ag(100002, 18)
        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')
        # zet het min_ag te hoog
        for klasse in CompetitieKlasse.objects.filter(competitie=self.comp_18, indiv__boogtype__afkorting='R', min_ag__lt=8.0):
            klasse.min_ag = 8.0     # > 7.42 van zet_ag
            klasse.save(update_fields=['min_ag'])
        # for
        # verwijder alle klassen 'onbekend'
        for klasse in CompetitieKlasse.objects.filter(indiv__is_onbekend=True):
            indiv = klasse.indiv
            indiv.is_onbekend = False
            indiv.save(update_fields=['is_onbekend'])
        # for
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on'})
        self.assert404(resp)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

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

    def test_wijzig_ag(self):
        # de HWL wil het AG van een sporter aanpassen
        zet_competitie_fase(self.comp_18, 'B')

        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_ag % 99999)
        self.assert403(resp)

        # log in als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # bad deelnemer_pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_ag % 99999)
        self.assert404(resp)  # 404 = Not allowed

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_ag % 99999)
        self.assert404(resp)  # 404 = Not allowed

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)
        self._zet_schutter_voorkeuren(100003)

        # beide sporters hebben geen AG

        # meld twee leden aan voor de competitie
        url = self.url_inschrijven % self.comp_18.pk
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                          'lid_100003_boogtype_3': 'on'})       # 3=BB
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        deelnemer = RegioCompetitieSchutterBoog.objects.get(schutterboog__nhblid__nhb_nr=100003)

        url = self.url_wijzig_ag % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-wijzig-ag.dtl', 'plein/site_layout.dtl'))

        # post zonder wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # post een wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '7.654'})
        self.assert_is_redirect_not_plein(resp)

        # post nog een wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '7.645'})
        self.assert_is_redirect_not_plein(resp)

        # post een te laag AG
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '0.999'})
        self.assert404(resp)  # 404 = Not allowed

        # post een te hoog AG
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '10.0'})
        self.assert404(resp)  # 404 = Not allowed

        # post een slechte wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': 'hallo!'})
        self.assert404(resp)  # 404 = Not allowed

        # opnieuw een get --> dit keer is er al een AG en er is geschiedenis
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_administratief(self):
        # log in als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maak dit een administratieve regio waarvan de leden geen wedstrijden mogen schieten
        regio = self.nhbver1.regio
        regio.is_administratief = True
        regio.save()

        url = self.url_inschrijven % self.comp_18.pk
        zet_competitie_fase(self.comp_18, 'B')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Geen wedstrijden in deze regio')


# end of file
