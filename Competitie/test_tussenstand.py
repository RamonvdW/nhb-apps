# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import Competitie, competitie_aanmaken
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieTussenstand(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, module Informatie over de Competitie """

    test_after = ('Competitie.test_beheerders', 'Competitie.test_competitie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # deze test is afhankelijk van de standaard regio's
        regio = NhbRegio.objects.get(regio_nr=101)

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

        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@gmail.com', 'Testertje')

        self.url_info = '/competitie/info/'
        self.url_tussenstand = '/competitie/tussenstand/'
        self.url_tussenstand_regio = '/competitie/tussenstand/%s-%s/regio/'
        self.url_tussenstand_regio_n = '/competitie/tussenstand/%s-%s/regio/%s/'
        self.url_tussenstand_rayon = '/competitie/tussenstand/%s-%s/rayon/'
        self.url_tussenstand_rayon_n = '/competitie/tussenstand/%s-%s/rayon/%s/'
        self.url_tussenstand_bond = '/competitie/tussenstand/%s-%s/bond/'

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        self.comp_18 = Competitie.objects.get(afstand='18')

        # TODO: schrijf schutters in (als RCL --> HWL)

    def _competitie_aanmaken(self):
        url_overzicht = '/competitie/'
        url_aanmaken = '/competitie/aanmaken/'
        url_ag_vaststellen = '/competitie/ag-vaststellen/'
        url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        url_klassegrenzen_vaststellen_25 = '/competitie/klassegrenzen/vaststellen/25/'

        # competitie aanmaken
        resp = self.client.post(url_aanmaken)
        self.assert_is_redirect(resp, url_overzicht)

        # aanvangsgemiddelden vaststellen
        resp = self.client.post(url_ag_vaststellen)

        # klassegrenzen vaststellen
        resp = self.client.post(url_klassegrenzen_vaststellen_18)
        resp = self.client.post(url_klassegrenzen_vaststellen_25)

    def test_top(self):
        Competitie.objects.all().delete()

        # tussenstand zonder competitie actief
        resp = self.client.get(self.url_tussenstand)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # creëer een competitie met deelcompetities
        now = timezone.now()
        competitie_aanmaken(jaar=now.year)
        way_before = datetime.date(year=2018, month=1, day=1)   # must be before timezone.now()

        # TODO: klassen moeten vastgesteld worden. Doe dit via de BB ipv direct.

        # tussenstand met competitie in prep fase (<B)
        resp = self.client.get(self.url_tussenstand)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # tussenstand met competitie in prep fase (B+)
        comp = Competitie.objects.all()[0]
        comp.begin_aanmeldingen = way_before   # fase B
        comp.einde_aanmeldingen = way_before   # fase C
        comp.save()
        resp = self.client.get(self.url_tussenstand)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # tussenstand met competitie in scorende fase (E+)
        comp.einde_teamvorming = way_before    # fase D
        comp.eerste_wedstrijd = way_before     # fase E
        comp.save()
        resp = self.client.get(self.url_tussenstand)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_regio(self):
        url = self.url_tussenstand_regio % (18, 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        url = self.url_tussenstand_regio % (18, 'C')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        url = self.url_tussenstand_regio % (25, 'IB')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_regio_n(self):
        url = self.url_tussenstand_regio_n % (18, 'R', 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        url = self.url_tussenstand_regio_n % (25, 'LB', 116)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_regio_bad(self):
        url = self.url_tussenstand_regio_n % (18, 'R', 999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_tussenstand_regio_n % (18, 'BAD', 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_tussenstand_regio_n % (99, 'r', 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_tussenstand_regio_n % ('X', 'r', 101)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_rayon(self):
        url = self.url_tussenstand_rayon % (18, 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_rayon_n(self):
        url = self.url_tussenstand_rayon_n % (18, 'R', 1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_rayon_bad(self):
        url = self.url_tussenstand_rayon % ('x', 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_tussenstand_rayon % (99, 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_tussenstand_rayon_n % (18, 'R', 'x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_bond(self):
        url = self.url_tussenstand_bond % (18, 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_bond_bad(self):
        url = self.url_tussenstand_bond % ('x', 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = self.url_tussenstand_bond % (99, 'R')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

# end of file
