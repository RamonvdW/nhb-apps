# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType, TeamWedstrijdklasse, IndivWedstrijdklasse
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Schutter.models import SchutterBoog
from Functie.models import maak_functie
from .models import (Competitie, DeelCompetitie, CompetitieKlasse, maak_competitieklasse_indiv,
                     RegioCompetitieSchutterBoog, regiocompetitie_schutterboog_aanmelden)
from .views import zet_fase
import datetime


class TestCompetitie(E2EHelpers, TestCase):
    """ unit tests voor de Competitie applicatie """

    test_after = ('BasisTypen', 'Functie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BB aan, nodig om de competitie defaults in te zien
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # deze test is afhankelijk van de standaard regio's
        regio = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = 1000
        ver.regio = regio
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een volwassen test lid aan (komt in groep met klasse onbekend)
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        self.account_lid = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.account = self.account_lid
        lid.save()
        self.lid_100001 = lid

        self.functie_hwl = maak_functie('HWL test', 'HWL')
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_lid)

        # maak een jeugdlid aan (komt in BB jeugd zonder klasse onbekend)
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "het Testertje"
        lid.email = "rdetestertje@gmail.not"
        lid.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        lid.bij_vereniging = ver
        self.account_jeugdlid = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.account = self.account_jeugdlid
        lid.save()
        self.lid_100002 = lid

        # maak een schutterboog aan voor het jeugdlid (nodig om aan te melden)
        boog_bb = BoogType.objects.get(afkorting='BB')
        schutterboog = SchutterBoog(nhblid=self.lid_100002, boogtype=boog_bb, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100002 = schutterboog

        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Zus"
        lid.achternaam = "de Testerin"
        lid.email = "zus@gmail.not"
        lid.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.lid_100003 = lid

        # maak een schutterboog aan voor het jeugdlid (nodig om aan te melden)
        schutterboog = SchutterBoog(nhblid=self.lid_100003, boogtype=boog_bb, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100003 = schutterboog

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
        rec.schutter_nr = self.lid_100001.nhb_nr
        rec.schutter_naam = self.lid_100001.volledige_naam()
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = ver.naam
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
        rec.schutter_nr = self.lid_100002.nhb_nr
        rec.schutter_naam = self.lid_100002.volledige_naam()
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = ver.naam
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

        self.url_overzicht = '/competitie/'
        self.url_instellingen = '/competitie/instellingen-volgende-competitie/'
        self.url_aanmaken = '/competitie/aanmaken/'
        self.url_ag_vaststellen = '/competitie/ag-vaststellen/'
        self.url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        self.url_klassegrenzen_vaststellen_25 = '/competitie/klassegrenzen/vaststellen/25/'
        self.url_klassegrenzen_tonen = '/competitie/klassegrenzen/tonen/'
        self.url_aangemeld = '/competitie/lijst-regio/%s/'  # % comp_pk

    def test_anon(self):
        self.e2e_logout()

        resp = self.client.get(self.url_instellingen)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_aanmaken)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_klassegrenzen_vaststellen_25)
        self.assert_is_redirect(resp, '/plein/')

    def test_instellingen(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_instellingen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_aanmaken(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/competities-aanmaken.dtl', 'plein/site_layout.dtl'))

        # gebruik een post om de competitie aan te laten maken
        # geen parameters nodig
        self.assertEqual(Competitie.objects.count(), 0)
        self.assertEqual(DeelCompetitie.objects.count(), 0)
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(DeelCompetitie.objects.count(), 2*(1 + 4 + 16))

        obj = Competitie.objects.all()[0]
        self.assertTrue(len(str(obj)) != "")
        for obj in DeelCompetitie.objects.all():
            msg = str(obj)
            if obj.nhb_regio:
                self.assertTrue("Regio " in msg)
            elif obj.nhb_rayon:
                self.assertTrue("Rayon " in msg)
            else:
                self.assertTrue("BK" in msg)
        # for

    def test_dubbel_aanmaken(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een post om de competitie aan te laten maken
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        # probeer de competities nog een keer aan te maken
        # verifieer geen effect
        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(DeelCompetitie.objects.count(), 2*(1 + 4 + 16))

        resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/competities-aanmaken.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wat doe je hier?")

        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(DeelCompetitie.objects.count(), 2*(1 + 4 + 16))

    def test_ag_vaststellen(self):
        self.e2e_login_and_pass_otp(self.account_bb)

        # trigger de permissie check (want: verkeerde rol)
        self.e2e_wisselnaarrol_gebruiker()
        resp = self.client.get(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, '/plein/')

        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # trigger de permissie check (want: geen competitie aangemaakt)
        resp = self.client.get(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, '/plein/')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om AG's vast te stellen
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        # controleer dat het "ag vaststellen" kaartje er is
        # om te beginnen zonder "voor het laatst gedaan"
        resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_ag_vaststellen in urls)
        self.assertNotContains(resp, "voor het laatst gedaan")

        # verander de fase van de 25m competitie zodat we een A1 en een A2 hebben
        comp = Competitie.objects.get(afstand=25, is_afgesloten=False)
        CompetitieKlasse(competitie=comp, min_ag=25.0).save()

        # haal het AG scherm op
        resp = self.client.get(self.url_ag_vaststellen)

        # gebruik een POST om de AG's vast te stellen
        resp = self.client.post(self.url_ag_vaststellen)

        # controleer dat het "ag vaststellen" kaartje er nog steeds is
        # dit keer met de "voor het laatst gedaan" notitie
        resp = self.client.get(self.url_overzicht)
        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_ag_vaststellen in urls)
        self.assertContains(resp, "voor het laatst gedaan")

    def test_ag_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om AG's vast te stellen
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        # geen HistComp
        HistCompetitie.objects.all().delete()

        # haal het AG scherm op
        resp = self.client.get(self.url_ag_vaststellen)

        # probeer de POST
        resp = self.client.post(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, self.url_overzicht)

    def test_klassegrenzen_vaststellen(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        # 18m competitie
        resp = self.client.get(self.url_klassegrenzen_vaststellen_18)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))
        # TODO: check de aangeboden data

        # nu kunnen we met een POST de klassegrenzen vaststellen
        self.assertEqual(CompetitieKlasse.objects.count(), 0)       # TODO: filter op Competitie
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertNotEqual(CompetitieKlasse.objects.count(), 0)    # TODO: filter op Competitie
        # TODO: check nog meer velden van de aangemaakte objecten

        # coverage
        obj = CompetitieKlasse.objects.all()[0]
        self.assertTrue(str(obj) != "")

    def test_klassegrenzen_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        # illegale competitie
        resp = self.client.get(self.url_klassegrenzen_vaststellen_18.replace('18', 'xx'))
        self.assertEqual(resp.status_code, 404)

    def test_klassegrenzen_tonen(self):
        resp = self.client.get(self.url_klassegrenzen_tonen)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De klassegrenzen zijn nog niet vastgesteld')

        # competitie opstarten
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        resp = self.client.get(self.url_klassegrenzen_tonen)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De klassegrenzen zijn nog niet vastgesteld')

        # daarna is het mogelijk om AG's vast te stellen?

        # klassegrenzen vaststellen (18m en 25m)
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect(resp, self.url_overzicht)
        resp = self.client.post(self.url_klassegrenzen_vaststellen_25)
        self.assert_is_redirect(resp, self.url_overzicht)
        self.e2e_logout()

        # nog een keer
        resp = self.client.get(self.url_klassegrenzen_tonen)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'De klassegrenzen zijn nog niet vastgesteld')

    def test_schutterboog_aanmelden(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken en de klassegrenzen vast te stellen
        resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_overzicht)

        competitie_18 = Competitie.objects.get(afstand=18)

        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect(resp, self.url_overzicht)
        resp = self.client.post(self.url_klassegrenzen_vaststellen_25)
        self.assert_is_redirect(resp, self.url_overzicht)

        # wissel naar HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # meld de schutterboog aan
        self.assertEqual(SchutterBoog.objects.count(), 2)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 0)

        # maak een cadet
        self.lid_100002.geboorte_datum = datetime.date(competitie_18.begin_jaar-15, month=3, day=4)
        self.lid_100002.save()

        regiocompetitie_schutterboog_aanmelden(competitie_18, self.schutterboog_100002, 8.18)
        self.assertEqual(RegioCompetitieSchutterBoog.objects.count(), 1)

        for obj in RegioCompetitieSchutterBoog.objects.all():
            self.assertEqual(obj.schutterboog, self.schutterboog_100002)
            self.assertEqual(obj.bij_vereniging.nhb_nr, self.lid_100002.bij_vereniging.nhb_nr)
            self.assertEqual(obj.klasse.indiv.boogtype, self.schutterboog_100002.boogtype)
            afk = [lkl.afkorting for lkl in obj.klasse.indiv.leeftijdsklassen.all()]
            self.assertTrue('CH' in afk)

            self.assertTrue(str(obj) != "")      # just to cover the code
        # for

        # lijst aangemeld regiocompetitie ophalen
        resp = self.client.get(self.url_aangemeld % competitie_18.pk)
        self.assertEqual(resp.status_code, 200)

        # maak nog een cadet aan
        self.lid_100003.geboorte_datum = datetime.date(competitie_18.begin_jaar-15, month=3, day=5)
        self.lid_100003.save()

        regiocompetitie_schutterboog_aanmelden(competitie_18, self.schutterboog_100003, 9.18)

        for obj in RegioCompetitieSchutterBoog.objects.filter(schutterboog=self.schutterboog_100003):
            self.assertEqual(obj.bij_vereniging.nhb_nr, self.lid_100003.bij_vereniging.nhb_nr)
            self.assertEqual(obj.klasse.indiv.boogtype, self.schutterboog_100003.boogtype)
            afk = [lkl.afkorting for lkl in obj.klasse.indiv.leeftijdsklassen.all()]
            self.assertTrue('CV' in afk)
        # for

        # lijst aangemeld regiocompetitie ophalen
        resp = self.client.get(self.url_aangemeld % competitie_18.pk)
        self.assertEqual(resp.status_code, 200)

        # corner case
        resp = self.client.get(self.url_aangemeld % 999999)
        self.assertEqual(resp.status_code, 404)

        # probeer dubbel aan te melden
        regiocompetitie_schutterboog_aanmelden(competitie_18, self.schutterboog_100003, None)

    def test_team(self):
        # slechts een test van een CompetitieKlasse() gekoppeld aan een TeamWedstrijdKlasse
        datum = datetime.date(year=2015, month=11, day=12)
        comp = Competitie(afstand='18', beschrijving='Test Competitie', begin_jaar=2015,
                          uiterste_datum_lid=datum,
                          begin_aanmeldingen=datum,
                          einde_aanmeldingen=datum,
                          einde_teamvorming=datum,
                          eerste_wedstrijd=datum)
        comp.save()

        wkl = TeamWedstrijdklasse.objects.all()[0]

        obj = CompetitieKlasse(competitie=comp, team=wkl, min_ag=0.42)
        obj.save()
        self.assertTrue(wkl.beschrijving in str(obj))

    def test_zet_fase(self):

        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        einde_jaar = datetime.date(year=now.year, month=12, day=31)
        gisteren = now - datetime.timedelta(days=1)

        # maak een competitie aan en controleer de fase
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = comp.eerste_wedstrijd = einde_jaar
        comp.save()
        zet_fase(comp)
        self.assertEqual(comp.fase, 'A1')

        # maak de klassen aan en controleer de fase weer
        indiv = IndivWedstrijdklasse.objects.all()[0]
        maak_competitieklasse_indiv(comp, indiv, 0.0)
        zet_fase(comp)
        self.assertEqual(comp.fase, 'A2')

        # tussen begin en einde aanmeldingen = B
        comp.begin_aanmeldingen = gisteren
        zet_fase(comp)
        self.assertEqual(comp.fase, 'B')

        # na einde aanmeldingen tot einde_teamvorming = C
        comp.einde_aanmeldingen = gisteren
        zet_fase(comp)
        self.assertEqual(comp.fase, 'C')

        # na einde teamvorming tot eerste wedstrijd = D
        comp.einde_teamvorming = gisteren
        zet_fase(comp)
        self.assertEqual(comp.fase, 'D')

        # na eerste wedstrijd = E
        comp.eerste_wedstrijd = gisteren
        zet_fase(comp)
        self.assertEqual(comp.fase, 'E')


# TODO: gebruik assert_other_http_commands_not_supported

# end of file
