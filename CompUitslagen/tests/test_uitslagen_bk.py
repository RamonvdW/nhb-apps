# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import Competitie, CompetitieMatch
from Competitie.tests.test_helpers import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData
import datetime


class TestCompUitslagenBK(E2EHelpers, TestCase):

    """ tests voor de CompUitslagen applicatie, module Uitslagen BK """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_beheerders')

    url_uitslagen_bond = '/bondscompetities/uitslagen/%s/%s/bond/'     # comp_pk, comp_boog

    regio_nr = 101
    ver_nr = 0      # wordt in setupTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('CompUitslagenBK: populating testdata start')
        s1 = timezone.now()
        cls.testdata = TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][2]
        #cls.testdata.maak_sporterboog_aanvangsgemiddelden(18, cls.ver_nr)
        #cls.testdata.maak_sporterboog_aanvangsgemiddelden(25, cls.ver_nr)
        cls.testdata.maak_bondscompetities()
        #cls.testdata.regio_teamcompetitie_ronde_doorzetten(cls.testdata.deelcomp18_regio[cls.regio_nr])
        s2 = timezone.now()
        d = s2 - s1
        print('CompUitslagenBK: populating testdata took %s seconds' % d.seconds)

    def test_bond(self):
        url = self.url_uitslagen_bond % (self.testdata.comp18.pk, 'R')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk.dtl', 'plein/site_layout.dtl'))

        # illegale parameters
        url = self.url_uitslagen_bond % ('x', 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_uitslagen_bond % (99, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # BK voor al afgesloten competitie
        comp = self.testdata.comp18
        comp.is_afgesloten = True
        comp.save(update_fields=['is_afgesloten'])
        url = self.url_uitslagen_bond % (comp.pk, 'R')
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslagen_bond % (self.testdata.comp18.pk, 'R'))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compuitslagen/uitslagen-bk.dtl', 'plein/site_layout.dtl'))


# end of file
