# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamWedstrijdklasse
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Schutter.models import SchutterBoog
from Functie.models import maak_functie
from .models import (Competitie, DeelCompetitie, CompetitieKlasse)
import datetime


class TestCompetitie(E2EHelpers, TestCase):
    """ unit tests voor de Competitie applicatie """

    test_after = ('BasisTypen', 'Functie', 'Competitie.test_fase')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BB aan, nodig om de competitie defaults in te zien
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = regio = NhbRegio.objects.get(regio_nr=101)

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

        boog_bb = BoogType.objects.get(afkorting='BB')
        boog_ib = BoogType.objects.get(afkorting='IB')

        # maak een schutterboog aan voor het jeugdlid (nodig om aan te melden)
        schutterboog = SchutterBoog(nhblid=self.lid_100002, boogtype=boog_bb, voor_wedstrijd=False)
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

        # maak een schutterboog aan voor het lid (nodig om aan te melden)
        schutterboog = SchutterBoog(nhblid=self.lid_100003, boogtype=boog_bb, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100003 = schutterboog

        # maak een schutterboog aan voor het lid (nodig om aan te melden)
        schutterboog = SchutterBoog(nhblid=self.lid_100001, boogtype=boog_ib, voor_wedstrijd=True)
        schutterboog.save()

        # (strategisch gekozen) historische data om klassegrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.klasse = 'Testcurve1'       # TODO: kan de klasse een spatie bevatten?
        histcomp.is_team = False
        histcomp.save()
        self.histcomp = histcomp

        # een ouder seizoen dat niet gebruikt moet worden
        histcomp2 = HistCompetitie()
        histcomp2.seizoen = '2017/2018'
        histcomp2.comp_type = '18'
        histcomp2.klasse = 'Testcurve2'
        histcomp2.is_team = False
        histcomp2.save()

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

        # nog een record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp2
        rec.rank = 1
        rec.schutter_nr = self.lid_100001.nhb_nr
        rec.schutter_naam = self.lid_100001.volledige_naam()
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'R'
        rec.score1 = 11
        rec.score2 = 21
        rec.score3 = 31
        rec.score4 = 41
        rec.score5 = 51
        rec.score6 = 61
        rec.score7 = 71
        rec.totaal = 81
        rec.gemiddelde = 6.12
        rec.save()

        # nog een record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 100
        rec.schutter_nr = self.lid_100001.nhb_nr
        rec.schutter_naam = self.lid_100001.volledige_naam()
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'IB'
        rec.score1 = 11
        rec.score2 = 21
        rec.score3 = 31
        rec.score4 = 41
        rec.score5 = 51
        rec.score6 = 61
        rec.score7 = 71
        rec.totaal = 81
        rec.gemiddelde = 6.12
        rec.save()

        # maak een record aan zonder eindgemiddelde
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.schutter_nr = self.lid_100002.nhb_nr
        rec.schutter_naam = self.lid_100002.volledige_naam()
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'C'
        rec.score1 = 0
        rec.score2 = 0
        rec.score3 = 0
        rec.score4 = 0
        rec.score5 = 0
        rec.score6 = 0
        rec.score7 = 0
        rec.totaal = 0
        rec.gemiddelde = 0.0
        rec.save()

        # record voor het jeugdlid
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

        # maak een record aan voor iemand die geen nhblid meer is
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.schutter_nr = 991111
        rec.schutter_naam = "Die is weg"
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

        self.url_kies = '/bondscompetities/'
        self.url_overzicht = '/bondscompetities/%s/'
        self.url_instellingen = '/bondscompetities/instellingen-volgende-competitie/'
        self.url_aanmaken = '/bondscompetities/aanmaken/'
        self.url_ag_vaststellen = '/bondscompetities/ag-vaststellen/'
        self.url_klassegrenzen_vaststellen = '/bondscompetities/%s/klassegrenzen/vaststellen/'  # comp_pk
        self.url_klassegrenzen_tonen = '/bondscompetities/%s/klassegrenzen/tonen/'              # comp_pk

    def _maak_many_histcomp(self):
        # maak veel histcomp records aan
        # zodat de AG-vaststellen bulk-create limiet van 500 gehaald wordt

        nhb_nr = 190000
        records = list()
        leden = list()

        geboorte_datum = datetime.date(year=1970, month=3, day=4)
        sinds_datum = datetime.date(year=2001, month=11, day=12)

        for lp in range(550):
            lid = NhbLid(nhb_nr=nhb_nr + lp,
                         geslacht='V',
                         geboorte_datum=geboorte_datum,
                         sinds_datum=sinds_datum)
            leden.append(lid)

            rec = HistCompetitieIndividueel(histcompetitie=self.histcomp,
                                            boogtype='R',
                                            rank=lp,
                                            schutter_nr=lid.nhb_nr,
                                            vereniging_nr=1000,
                                            score1=1,
                                            score2=2,
                                            score3=3,
                                            score4=4,
                                            score5=5,
                                            score6=6,
                                            score7=250,
                                            totaal=270,
                                            gemiddelde= 5.5)
            records.append(rec)
        # for

        NhbLid.objects.bulk_create(leden)
        HistCompetitieIndividueel.objects.bulk_create(records)

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_instellingen)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, '/plein/')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassegrenzen_vaststellen % 999999)
        self.assert_is_redirect(resp, '/plein/')

    def test_instellingen(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_instellingen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_aanmaken(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-competities-aanmaken.dtl', 'plein/site_layout.dtl'))

        # gebruik een post om de competitie aan te laten maken
        # geen parameters nodig
        self.assertEqual(Competitie.objects.count(), 0)
        self.assertEqual(DeelCompetitie.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)
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
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        # probeer de competities nog een keer aan te maken
        # verifieer geen effect
        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(DeelCompetitie.objects.count(), 2*(1 + 4 + 16))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-competities-aanmaken.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wat doe je hier?")

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(DeelCompetitie.objects.count(), 2*(1 + 4 + 16))

    def test_ag_vaststellen(self):
        self.e2e_login_and_pass_otp(self.account_bb)

        # trigger de permissie check (want: verkeerde rol)
        self.e2e_wisselnaarrol_gebruiker()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, '/plein/')

        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # trigger de permissie check (want: geen competitie aangemaakt)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, '/plein/')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om AG's vast te stellen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        # controleer dat het "ag vaststellen" kaartje er is
        # om te beginnen zonder "voor het laatst gedaan"
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_ag_vaststellen in urls)
        self.assertNotContains(resp, "voor het laatst gedaan")

        # verander de fase van de 25m competitie zodat we een A1 en een A2 hebben
        comp = Competitie.objects.get(afstand=25, is_afgesloten=False)
        CompetitieKlasse(competitie=comp, min_ag=25.0).save()

        # maak nog een hele bak AG's aan
        self._maak_many_histcomp()

        # haal het AG scherm op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # gebruik een POST om de AG's vast te stellen
        with self.assert_max_queries(600):      # TODO: optimize
            resp = self.client.post(self.url_ag_vaststellen)

        # controleer dat er geen dubbele SchutterBoog records aangemaakt zijn
        self.assertEqual(1, SchutterBoog.objects.filter(nhblid=self.lid_100001, boogtype__afkorting='R').count())
        self.assertEqual(1, SchutterBoog.objects.filter(nhblid=self.lid_100002, boogtype__afkorting='BB').count())
        self.assertEqual(554, SchutterBoog.objects.count())

        # controleer dat het "ag vaststellen" kaartje er nog steeds is
        # dit keer met de "voor het laatst gedaan" notitie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_ag_vaststellen in urls)
        self.assertContains(resp, "voor het laatst gedaan")

    def test_ag_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om AG's vast te stellen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        # geen HistCompIndividueel
        HistCompetitieIndividueel.objects.all().delete()

        # haal het AG scherm op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # probeer de POST
        with self.assert_max_queries(15):
            resp = self.client.post(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, self.url_kies)

        # geen HistComp
        HistCompetitie.objects.all().delete()

        # haal het AG scherm op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # probeer de POST
        with self.assert_max_queries(5):
            resp = self.client.post(self.url_ag_vaststellen)
        self.assert_is_redirect(resp, self.url_kies)

    def test_klassegrenzen_vaststellen(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        comp_pk = Competitie.objects.all()[0].pk

        # 18m competitie
        url = self.url_klassegrenzen_vaststellen % comp_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-klassegrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))
        # TODO: check de aangeboden data

        # nu kunnen we met een POST de klassegrenzen vaststellen
        self.assertEqual(CompetitieKlasse.objects.count(), 0)       # TODO: filter op Competitie
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_kies)
        self.assertNotEqual(CompetitieKlasse.objects.count(), 0)    # TODO: filter op Competitie
        # TODO: check nog meer velden van de aangemaakte objecten

        # coverage: nog een keer vaststellen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_kies)

        # coverage
        obj = CompetitieKlasse.objects.all()[0]
        self.assertTrue(str(obj) != "")
        obj.indiv = None
        obj.team = TeamWedstrijdklasse.objects.all()[0]
        self.assertTrue(str(obj) != "")

    def test_klassegrenzen_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        # illegale competitie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassegrenzen_vaststellen % 'xx')
        self.assertEqual(resp.status_code, 404)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_klassegrenzen_vaststellen % 'xx')
        self.assertEqual(resp.status_code, 404)

    def test_klassegrenzen_tonen(self):
        # competitie opstarten
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        comp_18 = Competitie.objects.filter(afstand=18).all()[0]
        comp_25 = Competitie.objects.filter(afstand=25).all()[0]

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassegrenzen_tonen % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, ' zijn nog niet vastgesteld')
        self.assertContains(resp, 'De klassegrenzen voor de ')

        # klassegrenzen vaststellen (18m en 25m)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_klassegrenzen_vaststellen % comp_18.pk)
        self.assert_is_redirect(resp, self.url_kies)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_klassegrenzen_vaststellen % comp_25.pk)
        self.assert_is_redirect(resp, self.url_kies)
        self.e2e_logout()

        # nog een keer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassegrenzen_tonen % comp_25.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, ' zijn nog niet vastgesteld')
        self.assertNotContains(resp, 'De klassegrenzen voor de ')

    def test_team(self):
        # slechts een test van een CompetitieKlasse() gekoppeld aan een TeamWedstrijdKlasse
        datum = datetime.date(year=2015, month=11, day=12)
        comp = Competitie(afstand='18', beschrijving='Test Competitie', begin_jaar=2015,
                          uiterste_datum_lid=datum,
                          begin_aanmeldingen=datum,
                          einde_aanmeldingen=datum,
                          einde_teamvorming=datum,
                          eerste_wedstrijd=datum,
                          laatst_mogelijke_wedstrijd=datum,
                          rk_eerste_wedstrijd=datum,
                          rk_laatste_wedstrijd=datum,
                          bk_eerste_wedstrijd=datum,
                          bk_laatste_wedstrijd=datum)
        comp.save()

        wkl = TeamWedstrijdklasse.objects.all()[0]

        obj = CompetitieKlasse(competitie=comp, team=wkl, min_ag=0.42)
        obj.save()
        self.assertTrue(wkl.beschrijving in str(obj))


# TODO: gebruik assert_other_http_commands_not_supported

# end of file
