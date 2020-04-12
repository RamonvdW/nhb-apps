# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.contrib.auth import get_user_model
from Account.models import Account, account_rechten_otp_controle_gelukt
from Functie.models import maak_functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from .models import Competitie, DeelCompetitie, CompetitieWedstrijdKlasse, competitie_aanmaken
import datetime


class TestCompetitie(E2EHelpers, TestCase):
    """ unit tests voor de Competitie applicatie """

    test_after = ('BasisTypen', 'Functie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BB aan, nodig om de competitie defaults in te zien
        self.account_bb = self.e2e_create_account('bko', 'bko@test.com', 'BKO', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # deze test is afhankelijk van de standaard regio's
        regio = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = regio
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test lid aan
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

        # (strategisch gekozen) historische data om klassegrenzen uit te bepalen
        comp = HistCompetitie()
        comp.seizoen = '2018/2019'
        comp.comp_type = '18'
        comp.klasse = 'Testcurve1'       # TODO: kan de klasse een spatie bevatten?
        comp.is_team = False
        comp.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = comp
        rec.rank = 1
        rec.schutter_nr = 100001
        rec.schutter_naam = 'Ramon de Tester'
        rec.vereniging_nr = 1000
        rec.vereniging_naam = 'Grote Club'
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

    def test_anon(self):
        self.e2e_logout()

        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get('/competitie/aanmaken/')
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.post('/competitie/aanmaken/')
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get('/competitie/klassegrenzen/18/')
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get('/competitie/klassegrenzen/25/')
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get('/competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

    def test_instellingen(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_aanmaken(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get('/competitie/aanmaken/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/competities-aanmaken.dtl', 'plein/site_layout.dtl'))

        # gebruik een post om de competitie aan te laten maken
        # geen parameters nodig
        self.assertEqual(len(Competitie.objects.all()), 0)
        self.assertEqual(len(DeelCompetitie.objects.all()), 0)
        resp = self.client.post('/competitie/aanmaken/')
        self.assert_is_redirect(resp, '/competitie/')
        self.assertEqual(len(Competitie.objects.all()), 2)
        self.assertEqual(len(DeelCompetitie.objects.all()), 2*(1 + 4 + 16))

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

    def test_klassegrenzen_cornercases(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        resp = self.client.post('/competitie/aanmaken/')
        self.assert_is_redirect(resp, '/competitie/')

        # illegale competitie
        resp = self.client.get('/competitie/klassegrenzen/xx/')
        self.assert_is_redirect(resp, '/plein/')
        #self.assertEqual(resp.status_code, 302)     # 302 = Redirect naar plein

        # 18m competitie, zonder historie
        HistCompetitie.objects.all().delete()
        resp = self.client.get('/competitie/klassegrenzen/18/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "FOUT - GEEN DATA AANWEZIG")

    def test_klassegrenzen(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        resp = self.client.post('/competitie/aanmaken/')

        # 18m competitie
        resp = self.client.get('/competitie/klassegrenzen/18/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassegrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))
        # TODO: check de aangeboden data

        # nu kunnen we met een POST de klassegrenzen vaststellen
        self.assertEqual(len(CompetitieWedstrijdKlasse.objects.all()), 0)       # TODO: filter op Competitie
        resp = self.client.post('/competitie/klassegrenzen/18/')
        self.assertNotEqual(len(CompetitieWedstrijdKlasse.objects.all()), 0)    # TODO: filter op Competitie
        obj = CompetitieWedstrijdKlasse.objects.all()[0]
        self.assertTrue(len(str(obj)) != "")
        # TODO: check nog meer velden van de aangemaakte objecten

# TODO: gebruik assert_other_http_commands_not_supported

# end of file
