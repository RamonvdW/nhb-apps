# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers
from NhbStructuur.models import NhbVereniging, NhbRegio, NhbLid
from .models import HistCompetitie, HistCompetitieIndividueel
from .views import RESULTS_PER_PAGE
import datetime


class TestHistCompInterland(E2EHelpers, TestCase):
    """ unittests voor de HistComp applicatie, module Interland """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = 1000
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

        obj = HistCompetitie()
        obj.seizoen = '2018/2019'
        obj.comp_type = '25'
        obj.klasse = 'Compound'
        obj.is_team = False
        obj.save()
        self.klasse_pk_leeg = obj.pk

        obj.pk = None
        obj.klasse = 'Recurve'
        obj.save()
        self.klasse_pk = obj.pk

        # maak een jeugdlid aan (komt in BB jeugd zonder klasse onbekend)
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "het Testertje"
        lid.email = "rdetestertje@gmail.not"
        lid.geboorte_datum = datetime.date(year=2019-15, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = lid.nhb_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = "wordt niet gebruikt"
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.laagste_score_nr = 1
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()
        self.indiv_rec_pk = rec.pk

        # maak nog een lid aan, met te weinig scores
        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "het Tester"
        lid.email = "mevrdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1969, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = lid.nhb_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = "wordt niet gebruikt"
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 0
        rec.score6 = 0
        rec.score7 = 0
        rec.laagste_score_nr = 1
        rec.totaal = 80
        rec.gemiddelde = 6.123
        rec.save()

        # maak nog een inactief lid aan
        lid = NhbLid()
        lid.nhb_nr = 100004
        lid.geslacht = "V"
        lid.voornaam = "Weg"
        lid.achternaam = "Is Weg"
        lid.email = "mevrwegisweg@gmail.not"
        lid.geboorte_datum = datetime.date(year=1969, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = None
        lid.account = None
        lid.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = lid.nhb_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = "wordt niet gebruikt"
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 0
        rec.laagste_score_nr = 1
        rec.totaal = 80
        rec.gemiddelde = 7.123
        rec.save()

        # maak nog een record aan voor een lid dat weg is
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = 999999
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = "wordt niet gebruikt"
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.laagste_score_nr = 1
        rec.totaal = 80
        rec.gemiddelde = 6.123
        rec.save()

        # maak een aspirant aan (mag niet meedoen)
        lid = NhbLid()
        lid.nhb_nr = 100005
        lid.geslacht = "M"
        lid.voornaam = "Appie"
        lid.achternaam = "Rant"
        lid.email = "aspriant@gmail.not"
        lid.geboorte_datum = datetime.date(year=2019-12, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2015, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = lid.nhb_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.nhb_nr
        rec.vereniging_naam = "wordt niet gebruikt"
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.laagste_score_nr = 1
        rec.totaal = 80
        rec.gemiddelde = 9.998
        rec.save()

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        self.url_interland = '/hist/interland/'
        self.url_interland_download = '/hist/interland/als-bestand/%s/'     # klasse_pk

    def test_interland(self):
        # anon
        resp = self.client.get(self.url_interland)
        self.assert_is_redirect(resp, '/plein/')

        # log in als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_interland)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('hist/interland.dtl', 'plein/site_layout.dtl'))

    def test_download(self):
        url = self.url_interland_download % self.klasse_pk

        # anon
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

        # log in als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_is_bestand(resp)

        # download een lege lijst
        url = self.url_interland_download % self.klasse_pk_leeg
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_is_bestand(resp)

    def test_bad(self):
        # log in als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        # illegale klasse_pk
        resp = self.client.get(self.url_interland_download % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # bestaande klasse_pk, maar verkeerd seizoen
        obj = HistCompetitie()
        obj.seizoen = '2017/2018'
        obj.comp_type = '25'
        obj.klasse = 'Compound'
        obj.is_team = False
        obj.save()
        resp = self.client.get(self.url_interland_download % obj.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # verwijder de hele histcomp
        HistCompetitie.objects.all().delete()

        # haal het lege overzicht op
        resp = self.client.get(self.url_interland)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

# end of file
