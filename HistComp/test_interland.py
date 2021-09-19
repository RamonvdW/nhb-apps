# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbVereniging, NhbRegio
from Sporter.models import Sporter
from .models import HistCompetitie, HistCompetitieIndividueel
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestHistCompInterland(E2EHelpers, TestCase):
    """ unittests voor de HistComp applicatie, module Interland """

    url_interland = '/bondscompetities/hist/interland/'
    url_interland_download = '/bondscompetities/hist/interland/als-bestand/%s/'  # klasse_pk

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = 1000
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
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "het Testertje"
        sporter.email = "rdetestertje@gmail.not"
        sporter.geboorte_datum = datetime.date(year=2019-15, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2015, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = sporter.lid_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.ver_nr
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
        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "het Tester"
        sporter.email = "mevrdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1969, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = sporter.lid_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.ver_nr
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
        sporter = Sporter()
        sporter.lid_nr = 100004
        sporter.geslacht = "V"
        sporter.voornaam = "Weg"
        sporter.achternaam = "Is Weg"
        sporter.email = "mevrwegisweg@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1969, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = None
        sporter.account = None
        sporter.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = sporter.lid_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.ver_nr
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
        rec.vereniging_nr = ver.ver_nr
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
        sporter = Sporter()
        sporter.lid_nr = 100005
        sporter.geslacht = "M"
        sporter.voornaam = "Appie"
        sporter.achternaam = "Rant"
        sporter.email = "aspriant@gmail.not"
        sporter.geboorte_datum = datetime.date(year=2019-12, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2015, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()

        rec = HistCompetitieIndividueel()
        rec.histcompetitie = obj
        rec.rank = 1
        rec.schutter_nr = sporter.lid_nr
        rec.schutter_naam = "wordt niet gebruikt"
        rec.vereniging_nr = ver.ver_nr
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

    def test_interland(self):
        # anon
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland)
        self.assert403(resp)

        # log in als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('hist/interland.dtl', 'plein/site_layout.dtl'))

    def test_download(self):
        url = self.url_interland_download % self.klasse_pk

        # anon
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # log in als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_is_bestand(resp)

        # download een lege lijst
        url = self.url_interland_download % self.klasse_pk_leeg
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_is_bestand(resp)

    def test_bad(self):
        # log in als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # illegale klasse_pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland_download % 999999)
        self.assert404(resp)     # 404 = Not found

        # bestaande klasse_pk, maar verkeerd seizoen
        obj = HistCompetitie()
        obj.seizoen = '2017/2018'
        obj.comp_type = '25'
        obj.klasse = 'Compound'
        obj.is_team = False
        obj.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland_download % obj.pk)
        self.assert404(resp)     # 404 = Not found

        # verwijder de hele histcomp
        HistCompetitie.objects.all().delete()

        # haal het lege overzicht op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

# end of file
