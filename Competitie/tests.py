# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.contrib.auth import get_user_model
from Account.models import Account, account_zet_sessionvars_na_otp_controle
from Account.rol import rol_zet_sessionvars_na_login
from Plein.tests import assert_html_ok, assert_template_used
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from .models import Competitie, DeelCompetitie, CompetitieWedstrijdKlasse, get_competitie_fase, \
                    FavorieteBestuurders
import datetime


class TestCompetitie(TestCase):
    """ unit tests voor de BasisTypen application """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BKO aan, nodig om de competitie defaults in te zien
        usermodel = get_user_model()
        usermodel.objects.create_user('bko', 'bko@test.com', 'wachtwoord')
        account = Account.objects.get(username='bko')
        account.is_BKO = True
        account.save()
        self.account_bko = account

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
        lid.postcode = "1234PC"
        lid.huisnummer = "42bis"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        usermodel.objects.create_user('100001', 'nhb100001@test.com', 'wachtwoord')
        account = Account.objects.get(username='100001')
        account.nhblid = lid
        account.save()
        self.account_lid = account

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

    def test_competitie_must_be_bko(self):
        self.client.logout()
        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

        resp = self.client.get('/competitie/aanmaken/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

        resp = self.client.post('/competitie/aanmaken/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

        resp = self.client.get('/competitie/klassegrenzen/18/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

        resp = self.client.get('/competitie/klassegrenzen/25/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

    def test_competitie_instellingen(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_bko, self.client).save()
        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_competitie_aanmaken(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_bko, self.client).save()
        resp = self.client.get('/competitie/aanmaken/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/competities-aanmaken.dtl', 'plein/site_layout.dtl'))

        # gebruik een post om de competitie aan te laten maken
        # geen parameters nodig
        self.assertEqual(len(Competitie.objects.all()), 0)
        self.assertEqual(len(DeelCompetitie.objects.all()), 0)
        resp = self.client.post('/competitie/aanmaken/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect naar plein
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

    def test_competitie_klassegrenzen_cornercases(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_bko, self.client).save()
        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        resp = self.client.post('/competitie/aanmaken/')
        # illegale competitie
        resp = self.client.get('/competitie/klassegrenzen/xx/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect naar plein
        # 18m competitie, zonder historie
        HistCompetitie.objects.all().delete()
        resp = self.client.get('/competitie/klassegrenzen/18/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/klassegrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "FOUT - GEEN DATA AANWEZIG")

    def test_competitie_klassegrenzen(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_bko, self.client).save()

        fase, comp = get_competitie_fase(18)        # TODO: werkt niet bij twee actieve competities
        self.assertEqual(fase, 'A')

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        resp = self.client.post('/competitie/aanmaken/')
        fase, comp = get_competitie_fase(18)
        self.assertEqual(fase, 'A1')

        # 18m competitie
        resp = self.client.get('/competitie/klassegrenzen/18/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/klassegrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))
        # TODO: check de aangeboden data

        # nu kunnen we met een POST de klassegrenzen vaststellen
        self.assertEqual(len(CompetitieWedstrijdKlasse.objects.all()), 0)
        resp = self.client.post('/competitie/klassegrenzen/18/')
        self.assertNotEqual(len(CompetitieWedstrijdKlasse.objects.all()), 0)
        obj = CompetitieWedstrijdKlasse.objects.all()[0]
        self.assertTrue(len(str(obj)) != "")

        fase, comp = get_competitie_fase(18)
        self.assertEqual(fase, 'A2')
        # TODO: check nog meer velden van de aangemaakte objecten

    def test_competitie_overzicht_anon(self):
        self.client.logout()
        resp = self.client.get('/competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

    def test_competitie_overzicht_bestuurder(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_bko, self.client).save()

        resp = self.client.get('/competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/overzicht-bestuurder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, '/competitie/beheer-favorieten/')

    def test_beheer_favorieten_anon(self):
        self.client.logout()
        resp = self.client.get('/competitie/beheer-favorieten/', follow=True)
        # controleer dat dit een redirect is naar de login pagina
        self.assertEqual(resp.status_code, 200)
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))

    def test_beheer_favorieten(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_login(self.account_bko, self.client).save()

        resp = self.client.get('/competitie/beheer-favorieten/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, "de Tester")
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 0)

        # zoeken en toevoegen
        resp = self.client.get('/competitie/beheer-favorieten/', {'zoekterm': "de Test"})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, "Niets gevonden")
        self.assertContains(resp, "100001")
        self.assertContains(resp, "Ramon de Tester")

        # voeg niet bestaand lid toe
        resp = self.client.post('/competitie/beheer-favorieten/wijzig/', {'add_favoriet': '999999'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 0)

        # voeg toe
        resp = self.client.post('/competitie/beheer-favorieten/wijzig/', {'add_favoriet': self.account_lid.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        #print("resp: %s" % repr(resp.content))
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 1)
        self.assertContains(resp, "100001")
        self.assertContains(resp, "Ramon de Tester")
        obj = FavorieteBestuurders.objects.all()[0]
        self.assertTrue(str(obj) != "")

        # dubbel toevoegen
        resp = self.client.post('/competitie/beheer-favorieten/wijzig/', {'add_favoriet': self.account_lid.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 1)

        # verwijder
        resp = self.client.post('/competitie/beheer-favorieten/wijzig/', {'drop_favoriet': self.account_lid.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 0)
        self.assertNotContains(resp, "100001")
        self.assertNotContains(resp, "Ramon de Tester")

        # verwijder niet aanwezig
        resp = self.client.post('/competitie/beheer-favorieten/wijzig/', {'drop_nhb_nr': '100001'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 0)

        # verwijder niet bestaand
        resp = self.client.post('/competitie/beheer-favorieten/wijzig/', {'drop_nhb_nr': '999999'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/beheer-favorieten.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 0)

# end of file
