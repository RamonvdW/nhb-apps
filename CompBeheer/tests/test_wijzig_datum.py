# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Competitie.models import Competitie
from Competitie.operations import competities_aanmaken
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompBeheerTestWijzigDatum(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module Wijzig datums """

    test_after = ('BasisTypen', 'Functie', 'Competitie.tests.test_overzicht')

    url_kies = '/bondscompetities/'
    url_overzicht = '/bondscompetities/%s/'
    url_overzicht_beheer = '/bondscompetities/beheer/%s/'
    url_aanmaken = '/bondscompetities/beheer/aanmaken/'
    url_instellingen = '/bondscompetities/beheer/instellingen-volgende-competitie/'
    url_wijzigdatums = '/bondscompetities/beheer/%s/wijzig-datums/'                             # comp_pk
    url_ag_vaststellen_afstand = '/bondscompetities/beheer/ag-vaststellen/%s/'                  # afstand
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp_pk
    url_klassengrenzen_tonen = '/bondscompetities/%s/klassengrenzen-tonen/'                     # comp_pk
    url_seizoen_afsluiten = '/bondscompetities/beheer/seizoen-afsluiten/'
    url_statistiek = '/bondscompetities/beheer/statistiek/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        # cls.testdata.maak_clubs_en_sporters()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = regio = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio)
        ver.save()

        # maak een volwassen test lid aan (komt in groep met klasse onbekend)
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        self.account_lid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_lid
        sporter.save()
        self.sporter_100001 = sporter

        self.functie_hwl = maak_functie('HWL test', 'HWL')
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_lid)

        # maak een jeugdlid aan (komt in BB jeugd zonder klasse onbekend)
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="het Testertje",
                    email="rdetestertje@gmail.not",
                    geboorte_datum=datetime.date(year=2008, month=3, day=4),
                    sinds_datum=datetime.date(year=2015, month=11, day=12),
                    bij_vereniging=ver)
        self.account_jeugdlid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_jeugdlid
        sporter.save()
        self.sporter_100002 = sporter

        boog_bb = BoogType.objects.get(afkorting='BB')
        boog_tr = BoogType.objects.get(afkorting='TR')

        # maak een sporterboog aan voor het jeugdlid (nodig om aan te melden)
        sporterboog = SporterBoog(sporter=self.sporter_100002, boogtype=boog_bb, voor_wedstrijd=False)
        sporterboog.save()
        self.sporterboog_100002 = sporterboog

        sporter = Sporter(
                    lid_nr=100003,
                    geslacht="V",
                    voornaam="Zus",
                    achternaam="de Testerin",
                    email="zus@gmail.not",
                    geboorte_datum=datetime.date(year=2008, month=3, day=4),
                    sinds_datum=datetime.date(year=2015, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100003 = sporter

        # maak een sporterboog aan voor het lid (nodig om aan te melden)
        sporterboog = SporterBoog(sporter=self.sporter_100003, boogtype=boog_bb, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100003 = sporterboog

        # maak een sporterboog aan voor het lid (nodig om aan te melden)
        sporterboog = SporterBoog(sporter=self.sporter_100001, boogtype=boog_tr, voor_wedstrijd=True)
        sporterboog.save()

    def test_anon(self):
        self.e2e_logout()

        resp = self.client.get(self.url_wijzigdatums % 999999)
        self.assert403(resp)

    def test_wijzig_datums(self):
        expected_month, expected_day = 12, 31
        expected_year = 2019

        # creëer een competitie met regiocompetities
        competities_aanmaken(jaar=expected_year)
        # nu in fase A

        comp = Competitie.objects.first()

        # avoid testcase from failing one day per year --> blijkt toch niet nodig
        # now = timezone.now()
        # if now.month == expected_month and now.day == expected_day:
        #     expected_month, expected_day = 1, 1
        #     expected_year += 1

        self.assertEqual(datetime.date(year=expected_year, month=expected_month, day=expected_day), comp.begin_fase_C)
        self.assertEqual(datetime.date(year=expected_year, month=expected_month, day=expected_day), comp.begin_fase_F)

        # niet BB
        url = self.url_wijzigdatums % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # wordt BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # get
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-wijzig-datums.dtl', 'plein/site_layout.dtl'))

        # post
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': '2019-08-09',       # begin_fase_C
                                          'datum2': '2019-09-10',       # begin_fase_F
                                          'datum3': '2019-10-11',       # einde_fase_F
                                          'datum4': '2019-11-12',
                                          'datum5': '2019-11-12',       # begin_fase_L_indiv
                                          'datum6': '2020-02-01',       # einde_fase_L_indiv
                                          'datum7': '2019-02-12',       # begin_fase_L_teams
                                          'datum8': '2020-05-01',       # einde_fase_L_teams
                                          'datum9': '2020-05-12',       # begin_fase_P_indiv
                                          'datum10': '2020-06-12',      # einde_fase_P_indiv
                                          'datum11': '2020-07-12',      # begin_fase_P_teams
                                          'datum12': '2020-08-12',      # einde_fase_P_teams
                                          })
        self.assert_is_redirect(resp, self.url_overzicht_beheer % comp.pk)

        # controleer dat de nieuwe datums opgeslagen zijn
        comp = Competitie.objects.get(pk=comp.pk)
        self.assertEqual(datetime.date(year=2019, month=8, day=9),   comp.begin_fase_C)
        self.assertEqual(datetime.date(year=2019, month=9, day=10),  comp.begin_fase_F)
        self.assertEqual(datetime.date(year=2019, month=10, day=11), comp.einde_fase_F)
        self.assertEqual(datetime.date(year=2020, month=2, day=1),   comp.einde_fase_L_indiv)
        self.assertEqual(datetime.date(year=2020, month=6, day=12),  comp.einde_fase_P_indiv)
        self.assertEqual(datetime.date(year=2020, month=8, day=12),  comp.einde_fase_P_teams)

        # check corner cases

        # alle datums verplicht
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': '2019-08-09'})
        self.assert404(resp, 'Verplichte parameter ontbreekt')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': 'null',
                                          'datum2': 'hallo',
                                          'datum3': '0',
                                          'datum4': '2019-13-42'})
        self.assert404(resp, 'Geen valide datum')

        # foute comp_pk bij get
        url = self.url_wijzigdatums % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # foute comp_pk bij post
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

        self.e2e_assert_other_http_commands_not_supported(url, post=False)


# end of file
