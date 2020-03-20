# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.contrib.auth import get_user_model
from Account.models import Account, account_vhpg_is_geaccepteerd, account_zet_sessionvars_na_otp_controle
from Functie.rol import rol_zet_sessionvars_na_otp_controle, rol_activeer_rol, rol_activeer_functie, \
                        rol_is_beheerder, rol_is_BB
from Functie.models import maak_functie
from Plein.test_helpers import assert_html_ok, assert_template_used, extract_all_href_urls
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from .models import Competitie, DeelCompetitie, CompetitieWedstrijdKlasse, \
                    competitie_aanmaken
import datetime


class TestCompetitie(TestCase):
    """ unit tests voor de Competitie applicatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BKO aan, nodig om de competitie defaults in te zien
        usermodel = get_user_model()
        usermodel.objects.create_user('bko', 'bko@test.com', 'wachtwoord')
        account = Account.objects.get(username='bko')
        account.is_BB = True
        account.save()
        self.account_bko = account
        account_vhpg_is_geaccepteerd(account)

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
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_beheerder(self.client))

        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_competitie_aanmaken(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_beheerder(self.client))

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
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_beheerder(self.client))

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
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_beheerder(self.client))

        # gebruik een POST om de competitie aan te maken
        # daarna is het mogelijk om klassegrenzen in te stellen
        resp = self.client.post('/competitie/aanmaken/')

        # 18m competitie
        resp = self.client.get('/competitie/klassegrenzen/18/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/klassegrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))
        # TODO: check de aangeboden data

        # nu kunnen we met een POST de klassegrenzen vaststellen
        self.assertEqual(len(CompetitieWedstrijdKlasse.objects.all()), 0)       # TODO: filter op Competitie
        resp = self.client.post('/competitie/klassegrenzen/18/')
        self.assertNotEqual(len(CompetitieWedstrijdKlasse.objects.all()), 0)    # TODO: filter op Competitie
        obj = CompetitieWedstrijdKlasse.objects.all()[0]
        self.assertTrue(len(str(obj)) != "")
        # TODO: check nog meer velden van de aangemaakte objecten

    def test_competitie_overzicht_anon(self):
        self.client.logout()
        resp = self.client.get('/competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, '/competitie/beheer-favorieten/')

    def test_competitie_overzicht_beheerder(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_beheerder(self.client))

        resp = self.client.get('/competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, '/functie/overzicht/')


class TestCompetitieBeheerders(TestCase):

    """ unit tests voor de Koppel Beheerders functie in de Competitie application """

    def _prep_lid(self, voornaam):
        nhb_nr = self._next_nhbnr
        self._next_nhbnr += 1

        lid = NhbLid()
        lid.nhb_nr = nhb_nr
        lid.geslacht = "M"
        lid.voornaam = voornaam
        lid.achternaam = "Tester"
        lid.email = "whatever@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = self._ver
        lid.save()

        self.usermodel.objects.create_user(nhb_nr, lid.email, 'wachtwoord')
        account = Account.objects.get(username=nhb_nr)
        account.nhblid = lid
        account.save()
        account_vhpg_is_geaccepteerd(account)
        return account

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.usermodel = get_user_model()
        #self.factory = RequestFactory()

        usermodel = get_user_model()
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')

        self._next_nhbnr = 100001

        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver

        # maak CWZ functie aan voor deze vereniging
        self.functie_cwz = maak_functie("CWZ Vereniging %s" % ver.nhb_nr, "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        # maak een BKO aan (geen NHB lid)
        self.usermodel.objects.create_user('bko', 'bko@test.com', 'wachtwoord')
        account = Account.objects.get(username='bko')
        account.is_BB = True
        account.save()
        self.account_bb = account

        # maak test leden aan die we kunnen koppelen aan beheerdersrollen
        self.account_bko = self._prep_lid('BKO')
        self.account_rko = self._prep_lid('RKO')
        self.account_rcl = self._prep_lid('RCL')
        self.account_schutter = self._prep_lid('Schutter')

        account_vhpg_is_geaccepteerd(self.account_bb)
        account_vhpg_is_geaccepteerd(self.account_bko)
        account_vhpg_is_geaccepteerd(self.account_rko)
        account_vhpg_is_geaccepteerd(self.account_rcl)
        account_vhpg_is_geaccepteerd(self.account_admin)

        # creer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        self.functie_bko = DeelCompetitie.objects.filter(laag='BK')[0].functie
        self.functie_rko = DeelCompetitie.objects.filter(laag='RK', nhb_rayon=self.rayon_2)[0].functie
        self.functie_rcl = DeelCompetitie.objects.filter(laag='Regio', nhb_regio=self.regio_101)[0].functie

        self.account_bko.functies.add(self.functie_bko)
        self.account_rko.functies.add(self.functie_rko)
        self.account_rcl.functies.add(self.functie_rcl)

        # maak nog een test vereniging, zonder CWZ functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

    def _login_as(self, account, functie):
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        if functie:
            rol_activeer_functie(self.client, functie.pk).save()
        else:
            rol_activeer_rol(self.client, "BB").save()
        self.assertTrue(rol_is_beheerder(self.client))

    def test_lijst_verenigingen_anon(self):
        self.client.logout()
        resp = self.client.get('/competitie/lijst-verenigingen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_lijst_verenigingen_admin(self):
        account = self.account_admin
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(account, self.client).save()
        rol_activeer_rol(self.client, "beheerder").save()
        resp = self.client.get('/competitie/lijst-verenigingen/', follow=True)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_lijst_verenigingen_bb(self):
        self._login_as(self.account_bb, None)
        resp = self.client.get('/competitie/lijst-verenigingen/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_lijst_verenigingen_bko(self):
        self._login_as(self.account_bko, self.functie_bko)
        resp = self.client.get('/competitie/lijst-verenigingen/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_lijst_verenigingen_rko(self):
        self._login_as(self.account_rko, self.functie_rko)
        resp = self.client.get('/competitie/lijst-verenigingen/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_lijst_verenigingen_rcl(self):
        self._login_as(self.account_rcl, self.functie_rcl)
        resp = self.client.get('/competitie/lijst-verenigingen/', follow=False)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

# end of file
