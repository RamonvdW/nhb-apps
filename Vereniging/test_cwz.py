# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import RegioCompetitieSchutterBoog, CompetitieKlasse
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Schutter.models import SchutterBoog
from Score.models import aanvangsgemiddelde_opslaan
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestVerenigingCWZ(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de CWZ """

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
        self.nhbver = ver

        # maak de CWZ functie
        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        # maak het lid aan dat CWZ wordt
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

        self.account_cwz = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_cwz.accounts.add(self.account_cwz)

        lid.account = self.account_cwz
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

        self.url_overzicht = '/vereniging/'
        self.url_ledenlijst = '/vereniging/leden-lijst/'
        self.url_voorkeuren = '/vereniging/leden-voorkeuren/'
        self.url_aanmelden = '/vereniging/leden-aanmelden/'

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

    def _create_histcomp(self):
        # (strategisch gekozen) historische data om klassegrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.klasse = 'Testcurve1'       # TODO: kan de klasse een spatie bevatten?
        histcomp.is_team = False
        histcomp.save()

        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.schutter_nr = self.nhblid_100001.nhb_nr
        rec.schutter_naam = self.nhblid_100001.volledige_naam()
        rec.vereniging_nr = self.nhbver.nhb_nr
        rec.vereniging_naam = self.nhbver.naam
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
        rec.vereniging_nr = self.nhbver.nhb_nr
        rec.vereniging_naam = self.nhbver.naam
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

    def _zet_schutter_voorkeuren(self, nhb_nr):
        # deze functie kan alleen gebruikt worden als CWZ
        url_schutter_voorkeuren = '/schutter/voorkeuren/'

        # haal als CWZ de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SchutterBoog records aan
        resp = self.client.get(url_schutter_voorkeuren + '%s/' % nhb_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        if nhb_nr == 100003:
            resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr, 'schiet_BB': 'on', 'info_R': 'on'})
        else:
            resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr, 'schiet_R': 'on', 'info_C': 'on'})

        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

    def _zet_ag(self, nhb_nr, afstand):
        if nhb_nr == 100003:
            afkorting = 'BB'
        else:
            afkorting = 'R'
        schutterboog = SchutterBoog.objects.get(nhblid__nhb_nr=nhb_nr, boogtype__afkorting=afkorting)
        datum = datetime.date(year=2020, month=4, day=1)
        aanvangsgemiddelde_opslaan(schutterboog, afstand, 7.42, datum, self.account_cwz, 'Test AG %s' % afstand)

    def test_overzicht(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect(resp, '/plein/')

        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_ledenlijst(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_ledenlijst)
        self.assert_is_redirect(resp, '/plein/')

        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

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

        resp = self.client.get(self.url_ledenlijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.assertContains(resp, 'Jeugd')
        self.assertContains(resp, 'Senioren')
        self.assertContains(resp, 'Inactieve leden')

        self.e2e_assert_other_http_commands_not_supported(self.url_ledenlijst)

    def test_voorkeuren(self):
        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        # inhoudelijk is de pagina gelijk aan ledenlijst

    def test_aanmelden(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_aanmelden)
        self.assert_is_redirect(resp, '/plein/')

        # login als CWZ
        self.e2e_login_and_pass_otp(self.account_cwz)
        self.e2e_wissel_naar_functie(self.functie_cwz)
        self.e2e_check_rol('CWZ')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 25)

        resp = self.client.get(self.url_aanmelden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(self.url_aanmelden, {'lid_100002_boogtype_1': 'on',        # 1=R
                                                     'lid_100003_boogtype_3': 'on'})       # 3=BB
        self.assert_is_redirect(resp, self.url_aanmelden)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 4)        # 2 schutters, 2 competities

        resp = self.client.post(self.url_aanmelden, {'garbage': 'oh',
                                                     'lid_GEENGETAL_boogtype_3': 'on'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_aanmelden, {'garbage': 'oh',
                                                     'lid_999999_boogtype_GEENGETAL': 'on'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_aanmelden, {'lid_999999_boogtype_3': 'on'})       # 3=BB
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(self.url_aanmelden, {'lid_100003_boogtype_1': 'on'})       # 1=R = geen wedstrijdboog
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 4)        # 2 schutters, 2 competities



# end of file
