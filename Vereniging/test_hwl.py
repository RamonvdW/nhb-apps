# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse,
                               RegioCompetitieSchutterBoog,
                               INSCHRIJF_METHODE_3, LAAG_REGIO, LAAG_RK)
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Schutter.models import SchutterBoog
from Score.models import aanvangsgemiddelde_opslaan
from Wedstrijden.models import WedstrijdLocatie
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestVerenigingHWL(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Schutter', 'Competitie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BB aan, nodig om de competitie aan te maken
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        self.regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
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
        ver2.nhb_nr = "1222"
        ver2.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        # fake een deelnemerslijst voor de RK
        deelcomp_rk = DeelCompetitie.objects.get(competitie=self.comp_25,
                                                 laag=LAAG_RK,
                                                 nhb_rayon=self.regio_111.rayon)
        deelcomp_rk.heeft_deelnemerslijst = True
        deelcomp_rk.save()

        self.url_overzicht = '/vereniging/'
        self.url_ledenlijst = '/vereniging/leden-lijst/'
        self.url_voorkeuren = '/vereniging/leden-voorkeuren/'
        self.url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'      # <comp_pk>
        self.url_ingeschreven = '/vereniging/leden-ingeschreven/competitie/%s/'  # <deelcomp_pk>
        self.url_schutter_voorkeuren = '/sporter/voorkeuren/%s/'                # <nhblid_pk>

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
        rec.vereniging_nr = self.nhbver1.nhb_nr
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
        rec.vereniging_nr = self.nhbver1.nhb_nr
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
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        url_overzicht = '/competitie/'
        url_aanmaken = '/competitie/aanmaken/'
        url_klassegrenzen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        url_klassegrenzen_25 = '/competitie/klassegrenzen/vaststellen/25/'

        self.assertEqual(CompetitieKlasse.objects.count(), 0)

        # competitie aanmaken
        resp = self.client.post(url_aanmaken)
        self.assert_is_redirect(resp, url_overzicht)

        # klassegrenzen vaststellen
        resp = self.client.post(url_klassegrenzen_18)
        self.assert_is_redirect(resp, url_overzicht)
        resp = self.client.post(url_klassegrenzen_25)
        self.assert_is_redirect(resp, url_overzicht)

        self.comp_18 = Competitie.objects.get(afstand=18)
        self.comp_25 = Competitie.objects.get(afstand=25)

        self.deelcomp_regio = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                         nhb_regio=self.regio_111,
                                                         competitie__afstand=18)

    def _zet_schutter_voorkeuren(self, nhb_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_schutter_voorkeuren = '/sporter/voorkeuren/'

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SchutterBoog records aan
        resp = self.client.get(url_schutter_voorkeuren + '%s/' % nhb_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        if nhb_nr == 100003:
            resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                              'schiet_BB': 'on',
                                                              'info_R': 'on',
                                                              'voorkeur_meedoen_competitie': 'on'})
        else:
            resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                              'schiet_R': 'on',
                                                              'info_C': 'on',
                                                              'voorkeur_meedoen_competitie': 'on'})

        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

    def _zet_ag(self, nhb_nr, afstand):
        if nhb_nr == 100003:
            afkorting = 'BB'
        else:
            afkorting = 'R'
        schutterboog = SchutterBoog.objects.get(nhblid__nhb_nr=nhb_nr, boogtype__afkorting=afkorting)
        aanvangsgemiddelde_opslaan(schutterboog, afstand, 7.42, self.account_hwl, 'Test AG %s' % afstand)

    def test_overzicht(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect(resp, '/plein/')

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

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

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

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
        # haal de lijst met leden voorkeuren op
        # view is gebaseerd op ledenlijst, dus niet veel te testen

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # eerste keer, zonder schutterboog records
        self.assertEqual(SchutterBoog.objects.count(), 0)
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # nog een keer, nu met schutterboog records aanwezig
        # zowel van de vereniging van de HWL als van andere verenigingen
        for nhblid in (self.nhblid_100001, self.nhblid_100002, self.nhblid_100003):
            # get operatie maakt de schutterboog records aan
            url = self.url_schutter_voorkeuren % nhblid.pk
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

        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/leden-voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_inschrijven(self):
        url = self.url_inschrijven % self.comp_18.pk

        # anon
        self.e2e_logout()
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel 1 schutter in die op randje aspirant/cadet zit
        self._zet_schutter_voorkeuren(100004)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, '<td>Cadet de Jeugd</td>')
        self.assertContains(resp, '<td>14</td>')            # leeftijd 2021
        self.assertContains(resp, '<td class="hide-on-small-only">Cadet</td>')  # leeftijdsklasse competitie

        # schrijf het jong lid in en controleer de wedstrijdklasse
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(url, {'lid_100004_boogtype_1': 'on'})       # 1=R
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        self.assertEqual(inschrijving.schutterboog.nhblid.nhb_nr, 100004)
        self.assertTrue('Cadet' in inschrijving.klasse.indiv.beschrijving)
        inschrijving.delete()

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100002)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 25)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                      'lid_100003_boogtype_3': 'on'})       # 3=BB
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        # haal de lijst met ingeschreven schutters op
        url = self.url_ingeschreven % self.deelcomp_regio.pk
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

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden met een verkeer dagdeel
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                      'dagdeel': 'ZA'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

        # nu de POST om een paar leden aan te melden met een verkeer dagdeel
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                      'dagdeel': 'xx'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
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

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # probeer aan te melden met een niet-wedstrijd boog
        schutterboog = SchutterBoog.objects.get(nhblid__nhb_nr=self.nhblid_100002.nhb_nr,
                                                boogtype__afkorting='R')
        schutterboog.voor_wedstrijd = False
        schutterboog.save()
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                      'dagdeel': 'AV'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        schutterboog.voor_wedstrijd = True
        schutterboog.save()

        # probeer aan te melden met een lid dat niet van de vereniging van de HWL is
        self.nhblid_100002.bij_vereniging = self.nhbver2
        self.nhblid_100002.save()
        resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',        # 1=R
                                      'dagdeel': 'AV'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        self.nhblid_100002.bij_vereniging = self.nhbver1
        self.nhblid_100002.save()

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
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

    def test_inschrijven_team(self):
        url = self.url_inschrijven % self.comp_18.pk

        # anon
        self.e2e_logout()
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100004)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
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

        # zet de udvl tussen de dvl van de twee schutters in
        # nhblid_100003.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        # nhblid_100004.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        comp = Competitie.objects.get(afstand='18')
        comp.uiterste_datum_lid = datetime.date(year=self.nhblid_100004.sinds_datum.year, month=1, day=1)
        comp.save()

        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # stel een paar bogen in
        self._zet_schutter_voorkeuren(100004)
        self._zet_schutter_voorkeuren(100003)

        self._zet_ag(100004, 18)
        self._zet_ag(100003, 25)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
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

        url = self.url_inschrijven % self.comp_18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('vereniging/competitie-aanmelden.dtl', 'plein/site_layout.dtl'))

        # nu de POST om een paar leden aan te melden
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)
        resp = self.client.post(url, {'lid_100004_boogtype_1': 'on',        # 1=R
                                      'lid_100003_boogtype_3': 'on',        # 3=BB
                                      'wil_in_team': 'ja',
                                      'opmerking': 'door de hwl'})
        self.assert_is_redirect_not_plein(resp)     # check success
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 2)    # 2 schutters, 1 competitie

        # schrijf de schutters weer uit
        pk = RegioCompetitieSchutterBoog.objects.all()[0].pk
        url = self.url_ingeschreven % 0
        resp = self.client.post(url, {'pk_%s' % pk: 'on'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)    # 1 schutter

        # schrijf een schutter uit van een andere vereniging
        inschrijving = RegioCompetitieSchutterBoog.objects.all()[0]
        inschrijving.schutterboog.nhblid.bij_vereniging = self.nhbver2
        inschrijving.schutterboog.nhblid.save()
        resp = self.client.post(url, {'pk_%s' % inschrijving.pk: 'on'})
        self.assertEqual(resp.status_code, 404)         # 404 = Not allowed
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)    # 1 schutter

    def test_cornercases(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_inschrijven % 9999999)
        self.assertEqual(resp.status_code, 404)         # 404 = Not allowed

        resp = self.client.post(self.url_inschrijven % 9999999)
        self.assertEqual(resp.status_code, 404)         # 404 = Not allowed

        url = self.url_inschrijven % self.comp_18.pk
        resp = self.client.post(url, {'garbage': 'oh',
                                      'lid_GEENGETAL_boogtype_3': 'on'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(url, {'garbage': 'oh',
                                      'lid_999999_boogtype_GEENGETAL': 'on'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(url, {'lid_999999_boogtype_3': 'on'})       # 3=BB
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(url, {'lid_100003_boogtype_1': 'on'})       # 1=R = geen wedstrijdboog
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        url = self.url_ingeschreven % 999999
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)     # redirect want POST kijkt niet naar deelcomp_pk

        resp = self.client.post(url, {'pk_hallo': 'on'})
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        resp = self.client.post(url, {'ignore': 'jaja', 'pk_null': 'on'})
        self.assertEqual(resp.status_code, 404)  # 404 = Not allowed

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
        resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        urls2 = [url for url in urls if url.startswith('/vereniging/accommodatie-details/')]
        self.assertEqual(len(urls2), 1)

        # ophalen en aanpassen: zie test_accommodatie

# end of file
