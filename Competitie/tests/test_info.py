# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbRegio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestCompetitieInfo(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, module Informatie over de Competitie """

    url_info = '/bondscompetities/info/'

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # deze test is afhankelijk van de standaard regio's
        regio = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio)
        ver.save()

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

    def test_info(self):
        # anon
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # geen lid
        self.e2e_login(self.account_geenlid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # sporter
        self.client.logout()
        self.e2e_login(self.account_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # inactief
        self.sporter_100001.bij_vereniging = None
        self.sporter_100001.save(update_fields=['bij_vereniging'])
        self.client.logout()
        self.e2e_login(self.account_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # redirect oud naar nieuw
        resp = self.client.get('/bondscompetities/info/leeftijden/')
        self.assert_is_redirect(resp, '/sporter/leeftijden/')

# end of file
