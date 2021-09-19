# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType, TeamType
from Competitie.models import (Competitie, CompetitieKlasse, DeelCompetitie,
                               RegioCompetitieSchutterBoog, RegiocompetitieTeam,
                               LAAG_BK, LAAG_RK, LAAG_REGIO)
from Competitie.test_competitie import maak_competities_en_zet_fase_b
from Functie.models import maak_functie, Functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompetitieUitslagen(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, module Uitslagen """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    url_overzicht = '/bondscompetities/%s/'
    url_uitslagen_regio = '/bondscompetities/%s/uitslagen/%s/%s/regio-individueel/'
    url_uitslagen_regio_n = '/bondscompetities/%s/uitslagen/%s/%s/regio-individueel/%s/'
    url_uitslagen_regio_teams = '/bondscompetities/%s/uitslagen/%s/regio-teams/'
    url_uitslagen_regio_teams_n = '/bondscompetities/%s/uitslagen/%s/regio-teams/%s/'
    url_uitslagen_rayon = '/bondscompetities/%s/uitslagen/%s/rayon-individueel/'
    url_uitslagen_rayon_n = '/bondscompetities/%s/uitslagen/%s/rayon-individueel/%s/'
    url_uitslagen_bond = '/bondscompetities/%s/uitslagen/%s/bond/'
    url_uitslagen_ver = '/bondscompetities/%s/uitslagen/%s/vereniging/'
    url_uitslagen_indiv_ver_n = '/bondscompetities/%s/uitslagen/%s/vereniging/%s/individueel/'      # comp_bk, boog_type, ver_nr
    url_uitslagen_teams_ver_n = '/bondscompetities/%s/uitslagen/%s/vereniging/%s/teams/'            # comp_pk, team_type, ver_nr

    testdata = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        # deze test is afhankelijk van de standaard regio's
        self.regio101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = 1000
        ver.regio = self.regio101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.ver = ver

        self.functie_hwl = maak_functie("HWL 1000", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("HWL 1000", "HWL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak een volwassen test lid aan (komt in groep met klasse onbekend)
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        self.account_lid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_lid
        sporter.save()
        self.sporter_100001 = sporter

        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@gmail.com', 'Testertje')

        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Tester"
        sporter.email = "rdeooktester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=1, day=1)
        sporter.sinds_datum = datetime.date(year=2014, month=11, day=12)
        sporter.bij_vereniging = ver
        self.account_lid_100002 = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_lid_100002
        sporter.save()
        self.sporter_100002 = sporter

        # maak een aspirant aan
        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "M"
        sporter.voornaam = "Kleintje"
        sporter.achternaam = "de Tester"
        sporter.email = "ouders@gmail.not"
        sporter.geboorte_datum = datetime.date(year=2010, month=1, day=1)
        sporter.sinds_datum = datetime.date(year=2018, month=11, day=12)
        sporter.bij_vereniging = ver
        self.account_lid_100003 = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_lid_100003
        sporter.save()
        self.sporter_100003 = sporter

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # TODO: schrijf schutters in (als RCL --> HWL)

    def _competitie_aanmaken(self):

        # competitie aanmaken
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_b()

        # zet de 18m open voor inschrijving
        self.comp_18.begin_aanmeldingen = datetime.date(year=self.comp_18.begin_jaar, month=1, day=1)
        self.comp_18.save()
        self.comp_18.bepaal_fase()

        self.functie_bko = DeelCompetitie.objects.filter(competitie=self.comp_18, laag=LAAG_BK).all()[0].functie
        self.functie_rko = DeelCompetitie.objects.filter(competitie=self.comp_18, laag=LAAG_RK).all()[0].functie
        self.functie_rcl = DeelCompetitie.objects.filter(competitie=self.comp_18, laag=LAAG_REGIO).all()[0].functie

        # schrijf iemand in
        boog_ib = BoogType.objects.get(afkorting='IB')
        boog_r = BoogType.objects.get(afkorting='R')
        deelcomp = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio101).all()[0]

        # Schutter 1 aanmelden

        sporterboog1 = SporterBoog(sporter=self.sporter_100001,
                                   boogtype=boog_ib,
                                   voor_wedstrijd=True)
        sporterboog1.save()

        klasse = (CompetitieKlasse
                  .objects
                  .filter(competitie=self.comp_18,
                          indiv__boogtype=boog_ib,
                          indiv__is_onbekend=True))[0]

        aanmelding1 = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                  sporterboog=sporterboog1,
                                                  bij_vereniging=sporterboog1.sporter.bij_vereniging,
                                                  klasse=klasse)
        aanmelding1.aantal_scores = 6        # nodig om voor te komen in de rayon uitslagen
        aanmelding1.save()

        # Schutter 2 aanmelden

        klasse = (CompetitieKlasse
                  .objects
                  .filter(competitie=self.comp_18,
                          indiv__boogtype=boog_ib,
                          indiv__is_onbekend=False))[0]

        sporterboog2 = SporterBoog(sporter=self.sporter_100002,
                                   boogtype=boog_ib,
                                   voor_wedstrijd=True)
        sporterboog2.save()

        aanmelding2 = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                  sporterboog=sporterboog2,
                                                  bij_vereniging=sporterboog2.sporter.bij_vereniging,
                                                  klasse=klasse)
        aanmelding2.aantal_scores = 6        # nodig om voor te komen in de rayon uitslagen
        aanmelding2.save()

        # nog een aanmelding in dezelfde klasse
        sporterboog3 = SporterBoog(sporter=self.sporter_100003,
                                   boogtype=boog_ib,
                                   voor_wedstrijd=True)
        sporterboog3.save()

        aanmelding3 = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                  sporterboog=sporterboog3,
                                                  bij_vereniging=sporterboog3.sporter.bij_vereniging,
                                                  klasse=klasse)
        aanmelding3.aantal_scores = 6        # nodig om voor te komen in de rayon uitslagen
        aanmelding3.save()

        # Schutter 3 (aspirant) aanmelden
        self.sporter_100003.geboorte_datum = datetime.date(year=self.comp_18.begin_jaar - 10, month=1, day=1)
        self.sporter_100003.save()

        klasse = (CompetitieKlasse
                  .objects
                  .filter(competitie=self.comp_18,
                          indiv__boogtype=boog_r,
                          indiv__beschrijving__contains="Aspirant"))[0]

        sporterboog4 = SporterBoog(sporter=self.sporter_100003,
                                   boogtype=boog_r,
                                   voor_wedstrijd=True)
        sporterboog4.save()

        aanmelding4 = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                  sporterboog=sporterboog4,
                                                  bij_vereniging=sporterboog4.sporter.bij_vereniging,
                                                  klasse=klasse)
        aanmelding4.save()

        # maak teams aan
        team_type = TeamType.objects.get(afkorting='R')
        team_klasse = CompetitieKlasse.objects.get(
                                competitie=deelcomp.competitie,
                                team__volgorde=13)       # Recurve Klasse C
        team = RegiocompetitieTeam(
                    deelcompetitie=deelcomp,
                    vereniging=self.ver,
                    volg_nr=1,
                    team_type=team_type,
                    team_naam="Test team 1",
                    aanvangsgemiddelde=25.0,
                    klasse=team_klasse)
        team.save()

        team.gekoppelde_schutters.set([aanmelding1, aanmelding2, aanmelding3])

    def test_top(self):
        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        way_before = datetime.date(year=2018, month=1, day=1)   # must be before timezone.now()

        comp = Competitie.objects.get(afstand=25)               # let op: 18 werkt niet

        # fase A
        comp.begin_aanmeldingen = now + datetime.timedelta(days=1)      # morgen
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase < 'B', msg="comp.fase=%s (expected: below B)" % comp.fase)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in prep fase (B+)
        comp.begin_aanmeldingen = way_before   # fase B
        comp.einde_aanmeldingen = way_before   # fase C
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase >= 'B')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in scorende fase (E+)
        comp.einde_teamvorming = way_before    # fase D
        comp.eerste_wedstrijd = way_before     # fase E
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase >= 'E')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_regio(self):
        # als BB
        url = self.url_uitslagen_regio % (self.comp_18.pk, 'R', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_n % (self.comp_18.pk, 'IB', 'alle', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_regio_teams % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_teams_n % (self.comp_18.pk, 'IB', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # als BKO
        self.e2e_wissel_naar_functie(self.functie_bko)
        url = self.url_uitslagen_regio % (self.comp_18.pk, 'C', 'zes')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als RKO
        self.e2e_wissel_naar_functie(self.functie_rko)
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'IB', 'maakt-niet-uit')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als RCL
        self.e2e_wissel_naar_functie(self.functie_rcl)
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'LB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'R', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als WL
        self.e2e_wissel_naar_functie(self.functie_wl)
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'C', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als bezoeker
        self.client.logout()
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'LB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als Schutter
        self.e2e_login(self.account_lid)
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'BB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als 'kapotte' Schutter
        self.sporter_100001.is_actief_lid = False
        self.sporter_100001.save()
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'BB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # als 'kapotte' Schutter
        self.sporter_100001.account = None
        self.sporter_100001.save()
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'BB', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

    def test_regio_n(self):
        url = self.url_uitslagen_regio_n % (self.comp_18.pk, 'R', 'alle', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_regio_n % (self.comp_25.pk, 'LB', 'alle', 116)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        # regio 100 is valide maar heeft geen deelcompetitie
        url = self.url_uitslagen_regio_n % (self.comp_18.pk, 'R', 'alle', 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

    def test_regio_bad(self):
        # slecht boog type
        url = self.url_uitslagen_regio % (self.comp_25.pk, 'XXX', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_regio_n % (self.comp_18.pk, 'R', 'alle', 999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_regio_n % (self.comp_18.pk, 'R', 'alle', "NaN")
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_regio_n % (self.comp_18.pk, 'BAD', 'alle', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_regio_n % (99, 'r', 'alle', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_regio_n % ('X', 'r', 'alle', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

    def test_rayon(self):
        url = self.url_uitslagen_rayon % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

    def test_rayon_n(self):
        url = self.url_uitslagen_rayon_n % (self.comp_18.pk, 'IB', 1)      # bevat onze enige deelnemer met 6 scores
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

    def test_rayon_bad(self):
        # slecht boogtype
        url = self.url_uitslagen_rayon % (self.comp_18.pk, 'XXX')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_rayon % ('x', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_rayon % (99, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_rayon_n % (self.comp_18.pk, 'R', 'x')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_rayon_n % (self.comp_18.pk, 'R', '0')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

    def test_bond(self):
        url = self.url_uitslagen_bond % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-bond.dtl', 'plein/site_layout.dtl'))

    def test_bond_bad(self):
        url = self.url_uitslagen_bond % ('x', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_bond % (99, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        # BK voor al afgesloten competitie
        self.comp_18.is_afgesloten = True
        self.comp_18.save()
        url = self.url_uitslagen_bond % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

    def test_ver_indiv(self):
        url = self.url_uitslagen_ver % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_indiv_ver_n % (self.comp_18.pk, 'R', self.ver.ver_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        # als je de pagina ophaalt als een ingelogd lid, dan krijg je je eigen vereniging
        self.e2e_login(self.account_lid_100002)

        url = self.url_uitslagen_ver % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '[1000] Grote Club')
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        # tenzij je geen lid meer bent bij een vereniging
        sporter = self.account_lid_100002.sporter_set.all()[0]
        sporter.is_actief_lid = False
        sporter.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

    def test_ver_team(self):
        url = self.url_uitslagen_teams_ver_n % (self.comp_18.pk, 'R', self.ver.ver_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-teams.dtl', 'plein/site_layout.dtl'))

        # bad comp_pk
        url = self.url_uitslagen_teams_ver_n % (999999, 'R', self.ver.ver_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, expected_msg='Competitie niet gevonden')

        # bad ver_nr
        url = self.url_uitslagen_teams_ver_n % (self.comp_18.pk, 'R', 'xxx')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, expected_msg='Verkeerd verenigingsnummer')

        # niet bestaande ver_nr
        url = self.url_uitslagen_teams_ver_n % (self.comp_18.pk, 'R', 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, expected_msg='Vereniging niet gevonden')

        # bad team type
        url = self.url_uitslagen_teams_ver_n % (self.comp_18.pk, 'xxx', self.ver.ver_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, expected_msg='Team type niet bekend')

    def test_vereniging_hwl(self):
        functie = Functie.objects.get(rol='HWL', nhb_ver=self.ver)
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(functie)

        # als je de pagina ophaalt als functie SEC/HWL/WL, dan krijg je die vereniging
        url = self.url_uitslagen_ver % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, '[1000] Grote Club')

    def test_vereniging_regio_100(self):
        self.ver.regio = NhbRegio.objects.get(regio_nr=100)
        self.ver.save()

        url = self.url_uitslagen_indiv_ver_n % (self.comp_18.pk, 'R', self.ver.ver_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

    def test_vereniging_bad(self):
        url = self.url_uitslagen_ver % ('x', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_ver % (self.comp_18.pk, 'x')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_indiv_ver_n % (self.comp_18.pk, 'R', 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        url = self.url_uitslagen_indiv_ver_n % (self.comp_18.pk, 'R', 'nan')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % self.comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_regio % (self.comp_18.pk, 'R', 'alle'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_regio_n % (self.comp_18.pk, 'R', 'alle', 111))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-indiv.dtl', 'plein/site_layout.dtl'))

        url = self.url_uitslagen_regio_teams % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_teams_n % (self.comp_18.pk, 'IB', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_rayon % (self.comp_18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_rayon_n % (self.comp_18.pk, 'R', 2))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-rayon-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_bond % (self.comp_18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-bond.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_ver % (self.comp_18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_indiv_ver_n % (self.comp_18.pk, 'R', self.ver.ver_nr))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-vereniging-indiv.dtl', 'plein/site_layout.dtl'))

    def test_teams(self):
        url = self.url_uitslagen_regio_teams % (self.comp_18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslagen-regio-teams.dtl', 'plein/site_layout.dtl'))


# end of file
