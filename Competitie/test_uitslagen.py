# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, CompetitieKlasse, DeelCompetitie,
                               RegioCompetitieSchutterBoog,
                               LAAG_BK, LAAG_RK, LAAG_REGIO, AG_NUL)
from Functie.models import maak_functie, Functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieUitslagen(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, module Uitslagen """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # deze test is afhankelijk van de standaard regio's
        self.regio101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = 1000
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

        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@gmail.com', 'Testertje')

        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Tester"
        lid.email = "rdeooktester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=1, day=1)
        lid.sinds_datum = datetime.date(year=2014, month=11, day=12)
        lid.bij_vereniging = ver
        self.account_lid_100002 = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.account = self.account_lid_100002
        lid.save()
        self.lid_100002 = lid

        self.url_info = '/competitie/info/'
        self.url_uitslagen = '/competitie/uitslagen/'
        self.url_uitslagen_regio = '/competitie/uitslagen/%s-%s/regio/'
        self.url_uitslagen_regio_n = '/competitie/uitslagen/%s-%s/regio/%s/'
        self.url_uitslagen_regio_alt = '/competitie/uitslagen/%s-%s/regio-alt/'
        self.url_uitslagen_regio_alt_n = '/competitie/uitslagen/%s-%s/regio-alt/%s/'
        self.url_uitslagen_rayon = '/competitie/uitslagen/%s-%s/rayon/'
        self.url_uitslagen_rayon_n = '/competitie/uitslagen/%s-%s/rayon/%s/'
        self.url_uitslagen_bond = '/competitie/uitslagen/%s-%s/bond/'
        self.url_uitslagen_ver = '/competitie/uitslagen/%s-%s/vereniging/'
        self.url_uitslagen_ver_n = '/competitie/uitslagen/%s-%s/vereniging/%s/'

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # TODO: schrijf schutters in (als RCL --> HWL)

    def _competitie_aanmaken(self):
        url_overzicht = '/competitie/'
        url_aanmaken = '/competitie/aanmaken/'
        url_ag_vaststellen = '/competitie/ag-vaststellen/'
        url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        url_klassegrenzen_vaststellen_25 = '/competitie/klassegrenzen/vaststellen/25/'

        # competitie aanmaken
        with self.assert_max_queries(20):
            resp = self.client.post(url_aanmaken)
        self.assert_is_redirect(resp, url_overzicht)

        # aanvangsgemiddelden vaststellen
        with self.assert_max_queries(5):
            resp = self.client.post(url_ag_vaststellen)

        # klassegrenzen vaststellen
        with self.assert_max_queries(20):
            resp = self.client.post(url_klassegrenzen_vaststellen_18)
        with self.assert_max_queries(20):
            resp = self.client.post(url_klassegrenzen_vaststellen_25)

        # zet de 18m open voor inschrijving
        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_18.begin_aanmeldingen = datetime.date(year=self.comp_18.begin_jaar, month=1, day=1)
        self.comp_18.save()
        self.comp_18.zet_fase()

        self.functie_bko = DeelCompetitie.objects.filter(competitie=self.comp_18, laag=LAAG_BK).all()[0].functie
        self.functie_rko = DeelCompetitie.objects.filter(competitie=self.comp_18, laag=LAAG_RK).all()[0].functie
        self.functie_rcl = DeelCompetitie.objects.filter(competitie=self.comp_18, laag=LAAG_REGIO).all()[0].functie

        # schrijf iemand in
        boog_ib = BoogType.objects.get(afkorting='IB')
        deelcomp = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio101).all()[0]

        # Schutter 1 aanmelden

        schutterboog = SchutterBoog(nhblid=self.lid_100001,
                                    boogtype=boog_ib,
                                    voor_wedstrijd=True)
        schutterboog.save()

        klasse = (CompetitieKlasse
                  .objects
                  .filter(competitie=self.comp_18,
                          indiv__boogtype=boog_ib,
                          indiv__is_onbekend=True))[0]

        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                 schutterboog=schutterboog,
                                                 bij_vereniging=schutterboog.nhblid.bij_vereniging,
                                                 aanvangsgemiddelde=AG_NUL,
                                                 klasse=klasse)
        aanmelding.aantal_scores = 6        # nodig om voor te komen in de rayon uitslagen
        aanmelding.save()

        # Schutter 2 aanmelden

        klasse = (CompetitieKlasse
                  .objects
                  .filter(competitie=self.comp_18,
                          indiv__boogtype=boog_ib,
                          indiv__is_onbekend=False))[0]

        schutterboog = SchutterBoog(nhblid=self.lid_100002,
                                    boogtype=boog_ib,
                                    voor_wedstrijd=True)
        schutterboog.save()

        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                 schutterboog=schutterboog,
                                                 bij_vereniging=schutterboog.nhblid.bij_vereniging,
                                                 aanvangsgemiddelde=AG_NUL,
                                                 klasse=klasse)
        aanmelding.aantal_scores = 6        # nodig om voor te komen in de rayon uitslagen
        aanmelding.save()

        # nog een aanmelding in dezelfde klasse
        schutterboog = SchutterBoog(nhblid=self.lid_100002,
                                    boogtype=boog_ib,
                                    voor_wedstrijd=True)
        schutterboog.save()

        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                 schutterboog=schutterboog,
                                                 bij_vereniging=schutterboog.nhblid.bij_vereniging,
                                                 aanvangsgemiddelde=AG_NUL,
                                                 klasse=klasse)
        aanmelding.aantal_scores = 6        # nodig om voor te komen in de rayon uitslagen
        aanmelding.save()

    def test_top(self):
        comp = Competitie.objects.all()[0]
        way_before = datetime.date(year=2018, month=1, day=1)   # must be before timezone.now()

        # fase A1
        comp.zet_fase()
        self.assertTrue(comp.fase < 'B')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in prep fase (B+)
        comp.begin_aanmeldingen = way_before   # fase B
        comp.einde_aanmeldingen = way_before   # fase C
        comp.save()
        comp.zet_fase()
        self.assertTrue(comp.fase >= 'B')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in scorende fase (E+)
        comp.einde_teamvorming = way_before    # fase D
        comp.eerste_wedstrijd = way_before     # fase E
        comp.save()
        comp.zet_fase()
        self.assertTrue(comp.fase >= 'E')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen zonder competitie actief
        Competitie.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_regio(self):
        # als BB
        url = self.url_uitslagen_regio % (18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # lijst met onze deelnemers
        url = self.url_uitslagen_regio_n % (18, 'IB', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als BKO
        self.e2e_wissel_naar_functie(self.functie_bko)
        url = self.url_uitslagen_regio % (18, 'C')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als RKO
        self.e2e_wissel_naar_functie(self.functie_rko)
        url = self.url_uitslagen_regio % (25, 'IB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als RCL
        self.e2e_wissel_naar_functie(self.functie_rcl)
        url = self.url_uitslagen_regio % (25, 'LB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        url = self.url_uitslagen_regio % (25, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als WL
        self.e2e_wissel_naar_functie(self.functie_wl)
        url = self.url_uitslagen_regio % (25, 'C')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als bezoeker
        self.client.logout()
        url = self.url_uitslagen_regio % (25, 'LB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als Schutter
        self.e2e_login(self.account_lid)
        url = self.url_uitslagen_regio % (25, 'BB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als 'kapotte' Schutter
        self.lid_100001.is_actief_lid = False
        self.lid_100001.save()
        url = self.url_uitslagen_regio % (25, 'BB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als 'kapotte' Schutter
        self.lid_100001.account = None
        self.lid_100001.save()
        url = self.url_uitslagen_regio % (25, 'BB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_regio_n(self):
        url = self.url_uitslagen_regio_n % (18, 'R', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        url = self.url_uitslagen_regio_n % (25, 'LB', 116)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # regio 100 is valide maar heeft geen deelcompetitie
        url = self.url_uitslagen_regio_n % (18, 'R', 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_regio_alt(self):
        url = self.url_uitslagen_regio_alt % (25, 'BB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        url = self.url_uitslagen_regio_alt_n % (18, 'R', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        self.client.logout()

        url = self.url_uitslagen_regio_alt % (25, 'BB')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert_is_redirect(resp, self.url_uitslagen_regio % (25, 'BB'))

        url = self.url_uitslagen_regio_alt_n % (18, 'R', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert_is_redirect(resp, self.url_uitslagen_regio_n % (18, 'R', 101))

    def test_regio_bad(self):
        # slecht boog type
        url = self.url_uitslagen_regio % (25, 'XXX')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_regio_n % (18, 'R', 999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_regio_n % (18, 'R', "NaN")
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_regio_n % (18, 'BAD', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_regio_n % (99, 'r', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_regio_n % ('X', 'r', 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_rayon(self):
        url = self.url_uitslagen_rayon % (18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_rayon_n(self):
        url = self.url_uitslagen_rayon_n % (18, 'IB', 1)      # bevat onze enige deelnemer met 6 scores
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_rayon_bad(self):
        # slecht boogtype
        url = self.url_uitslagen_rayon % (18, 'XXX')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_rayon % ('x', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_rayon % (99, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_rayon_n % (18, 'R', 'x')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_bond(self):
        url = self.url_uitslagen_bond % (18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_bond_bad(self):
        url = self.url_uitslagen_bond % ('x', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_bond % (99, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_vereniging(self):
        url = self.url_uitslagen_ver % (18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        url = self.url_uitslagen_ver_n % (18, 'R', self.ver.nhb_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # als je de pagina ophaalt als een ingelogd lid, dan krijg je je eigen vereniging
        self.e2e_login(self.account_lid_100002)

        url = self.url_uitslagen_ver % (18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '[1000] Grote Club')
        self.assert_html_ok(resp)

        # tenzij je geen lid meer bent bij een vereniging
        nhblid = self.account_lid_100002.nhblid_set.all()[0]
        nhblid.is_actief_lid = False
        nhblid.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_vereniging_hwl(self):
        functie = Functie.objects.get(rol='HWL', nhb_ver=self.ver)
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(functie)

        # als je de pagina ophaalt als functie SEC/HWL/WL, dan krijg je die vereniging
        url = self.url_uitslagen_ver % (18, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '[1000] Grote Club')
        self.assert_html_ok(resp)

    def test_vereniging_regio_100(self):
        self.ver.regio = NhbRegio.objects.get(regio_nr=100)
        self.ver.save()

        url = self.url_uitslagen_ver_n % (18, 'R', self.ver.nhb_nr)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_vereniging_bad(self):
        url = self.url_uitslagen_ver % ('x', 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_ver % (18, 'x')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_ver_n % (18, 'R', 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_uitslagen_ver_n % (18, 'R', 'nan')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


# end of file
