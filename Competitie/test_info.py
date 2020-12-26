# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieInfo(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, module Informatie over de Competitie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
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

    def test_anon(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

    def test_geen_lid(self):
        self.e2e_login(self.account_geenlid)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

    def test_inactief(self):
        self.lid_100001.bij_vereniging = None
        self.lid_100001.save()

        self.e2e_login(self.account_lid)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

    def test_schutter(self):
        self.e2e_login(self.account_lid)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

# end of file
