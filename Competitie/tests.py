# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import Resolver404
from Account.models import Account, account_vhpg_is_geaccepteerd, account_zet_sessionvars_na_otp_controle
from Account.rol import rol_zet_sessionvars_na_otp_controle, rol_activeer_rol, rol_activeer_functie, rol_is_bestuurder
from Plein.test_helpers import assert_html_ok, assert_template_used, extract_all_href_urls
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from .models import Competitie, DeelCompetitie, CompetitieWedstrijdKlasse, get_competitie_fase, \
                    FavorieteBestuurders, add_favoriete_bestuurder, competitie_aanmaken
from .views import KoppelBestuurdersCompetitieView
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
        account.is_BKO = True
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
        self.assertTrue(rol_is_bestuurder(self.client))

        resp = self.client.get('/competitie/instellingen-volgende-competitie/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_competitie_aanmaken(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_bestuurder(self.client))

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
        self.assertTrue(rol_is_bestuurder(self.client))

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
        self.assertTrue(rol_is_bestuurder(self.client))

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
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_bestuurder(self.client))

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

        resp = self.client.get('/competitie/beheer-favorieten/wijzig/', follow=False)
        self.assertEqual(resp.status_code, 404)     # 404 indicates rejected

    def test_beheer_favorieten_normaal(self):
        # niet-bestuurder mag favorieten niet te wijzigen
        self.client.login(username='100001', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_lid, self.client).save()

        self.assertEqual(len(FavorieteBestuurders.objects.all()), 0)
        resp = self.client.post('/competitie/beheer-favorieten/wijzig/', {'add_favoriet': self.account_lid.pk})
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect
        self.assertEqual(resp.url, '/competitie/beheer-favorieten/')
        self.assertEqual(len(FavorieteBestuurders.objects.all()), 0)

    def test_beheer_favorieten(self):
        self.client.login(username='bko', password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()
        rol_activeer_rol(self.client, 'BB').save()
        self.assertTrue(rol_is_bestuurder(self.client))

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


class TestCompetitieKoppelBestuurders(TestCase):
    """ unit tests voor de Koppel Bestuurders functie in de Competitie application """

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

    def _set_fav(self, account, favs):
        for fav in favs:
            add_favoriete_bestuurder(account, fav.pk)
        # for

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.usermodel = get_user_model()
        self.factory = RequestFactory()

        self.rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.rayon_3 = NhbRayon.objects.get(rayon_nr=3)
        self.rayon_4 = NhbRayon.objects.get(rayon_nr=4)

        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver
        self._next_nhbnr = 100001

        # maak een BKO aan (geen NHB lid)
        self.usermodel.objects.create_user('bko', 'bko@test.com', 'wachtwoord')
        account = Account.objects.get(username='bko')
        account.is_BKO = True
        account.save()
        self.account_bko = account
        account_vhpg_is_geaccepteerd(account)

        # maak test leden aan die we kunnen koppelen aan bestuurdersrollen
        self.account_rko1 = self._prep_lid('RKO1')
        self.account_rko2 = self._prep_lid('RKO2')
        self.account_rko3 = self._prep_lid('RKO3')
        self.account_rko4 = self._prep_lid('RKO4')
        self.account_rcl11 = self._prep_lid('RCL11')
        self.account_rcl12 = self._prep_lid('RCL12')
        self.account_rcl21 = self._prep_lid('RCL21')
        self.account_rcl22 = self._prep_lid('RCL22')
        self.account_rcl31 = self._prep_lid('RCL31')

        # stel the favorieten van elk lid in
        self._set_fav(self.account_bko, (self.account_rko1, self.account_rko2, self.account_rko3, self.account_rko4))
        self._set_fav(self.account_rko1, (self.account_rcl11, self.account_rcl12))
        self._set_fav(self.account_rko2, (self.account_rcl21, self.account_rcl22))
        self._set_fav(self.account_rko3, (self.account_rcl31, self.account_rcl22))
        self._set_fav(self.account_rko4, (self.account_rcl31,))

        # creer een competitie met deelcompetities
        competitie_aanmaken()

    def test_koppelbestuurder_competitie_anon(self):
        self.client.logout()

        resp = self.client.get('/competitie/toon-bestuurders/9999/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get('/competitie/kies-bestuurders/9999/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('account/login.dtl', 'plein/site_layout.dtl'))

        # get wordt niet ondersteund
        resp = self.client.get('/competitie/wijzig-bestuurders/')
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_koppelbestuurder_competitie_bko(self):
        # login als BB
        self.client.login(username=self.account_bko.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_bko, self.client).save()

        # wissel naar BKO rol voor de juiste competitie
        competitie = Competitie.objects.all()[0]
        deelcomp = DeelCompetitie.objects.filter(competitie=competitie, laag='BK')[0]
        functie = deelcomp.functies.all()[0]
        rol_activeer_functie(self.client, functie.pk).save()
        self.assertTrue(rol_is_bestuurder(self.client))

        # niet bestaande competitie_pk
        resp = self.client.get('/competitie/toon-bestuurders/9999/')
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # haal de lijst met gekoppelde bestuurders op voor de competitie
        competitie = Competitie.objects.all()[0]
        resp = self.client.get('/competitie/toon-bestuurders/%s/' % competitie.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/koppel-bestuurders-overzicht.dtl', 'plein/site_layout.dtl'))

        # controlleer dat de juiste Wijzig knoppen aanwezig zijn voor de BKO rol
        urls = extract_all_href_urls(resp)
        for deelcomp in DeelCompetitie.objects.filter(competitie=competitie):
            url = '/competitie/kies-bestuurders/%s/' % deelcomp.pk
            if deelcomp.laag == "RK":
                self.assertTrue(url in urls)        # check link voor koppelen RKO
            else:
                self.assertFalse(url in urls)       # check geen link voor andere lagen
        # for

    def test_koppelbestuurder_competitie_rko(self):
        # RKO kan RCL's koppelen

        # koppel rko2 aan de functie van RKO voor rayon 2
        competitie = Competitie.objects.all()[0]
        functie = Group.objects.get(name="RKO rayon 2 voor de %s" % competitie.beschrijving)
        functie.user_set.add(self.account_rko2)

        # login als rko2
        self.client.login(username=self.account_rko2.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_rko2, self.client).save()
        rol_activeer_functie(self.client, functie.pk).save()
        self.assertTrue(rol_is_bestuurder(self.client))

        resp = self.client.get('/competitie/toon-bestuurders/%s/' % competitie.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/koppel-bestuurders-overzicht.dtl', 'plein/site_layout.dtl'))

        # controlleer dat de juiste Wijzig knoppen aanwezig zijn voor de RCL rol
        rko_rayon_nr = functie.deelcompetitie_set.all()[0].nhb_rayon.rayon_nr
        urls = extract_all_href_urls(resp)
        for deelcomp in DeelCompetitie.objects.filter(competitie=competitie):
            url = '/competitie/kies-bestuurders/%s/' % deelcomp.pk
            if deelcomp.laag == "Regio" and deelcomp.nhb_regio.rayon.rayon_nr == rko_rayon_nr:
                self.assertTrue(url in urls)        # check link voor koppelen RCL
            else:
                self.assertFalse(url in urls)       # check geen link voor andere lagen
        # for

    def test_koppelbestuurder_competitie_rcl(self):
        # RCL kan niemand koppelen

        # koppel RCL11 aan de functie van RCL voor regio 101
        competitie = Competitie.objects.all()[0]
        functie = Group.objects.get(name="RCL regio 101 voor de %s" % competitie.beschrijving)
        functie.user_set.add(self.account_rcl11)

        # login als rcl11
        self.client.login(username=self.account_rcl11.username, password='wachtwoord')
        account_zet_sessionvars_na_otp_controle(self.client).save()
        rol_zet_sessionvars_na_otp_controle(self.account_rcl11, self.client).save()
        rol_activeer_functie(self.client, functie.pk).save()
        self.assertTrue(rol_is_bestuurder(self.client))

        resp = self.client.get('/competitie/toon-bestuurders/%s/' % competitie.pk, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('competitie/koppel-bestuurders-overzicht.dtl', 'plein/site_layout.dtl'))

        # controlleer dat de juiste Wijzig knoppen aanwezig zijn voor de RCL rol
        urls = extract_all_href_urls(resp)
        for deelcomp in DeelCompetitie.objects.filter(competitie=competitie):
            url = '/competitie/kies-bestuurders/%s/' % deelcomp.pk
            self.assertFalse(url in urls)       # check geen link voor koppelen RCL
        # for


        # haal de lijst met gekoppelde bestuurders op voor de competitie
        # dit werkt niet meer met self.client
        #request = self.factory.get('/competitie/toon-bestuurders/%s/' % competitie.pk, follow=True)
        #request.session = self.client.session
        #request.user = self.account_rcl11
        #with self.assertRaises(Resolver404):
        #    resp = KoppelBestuurdersCompetitieView.as_view()(request)

# end of file
