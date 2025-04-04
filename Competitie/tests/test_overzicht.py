# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from Competitie.test_utils.tijdlijn import zet_competitie_fases
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieOverzicht(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, pagina Overzicht """

    test_after = ('Competitie.tests.test_tijdlijn',)

    url_overzicht = '/bondscompetities/%s/'

    def test_top(self):
        # now = timezone.now()
        # now = datetime.date(year=now.year, month=now.month, day=now.day)
        # way_before = datetime.date(year=2018, month=1, day=1)   # must be before timezone.now()

        comp_18, comp_25 = maak_competities_en_zet_fase_c(startjaar=2020)

        comp = comp_25

        # fase A
        zet_competitie_fases(comp, 'A', 'A')
        comp.bepaal_fase()
        self.assertTrue(comp.fase_indiv < 'C', msg="comp.fase_indiv=%s (expected: below C)" % comp.fase_indiv)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # zet competitie fase B zodat we in mogen schrijven
        zet_competitie_fases(comp, 'B', 'B')

        # uitslagen met competitie in prep fase (C+)
        zet_competitie_fases(comp, 'C', 'C')
        comp.bepaal_fase()
        self.assertTrue(comp.fase_indiv >= 'C', msg="comp.fase_indiv=%s (expected: not below C)" % comp.fase_indiv)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in scorende fase (F+)
        zet_competitie_fases(comp, 'F', 'F')
        comp.bepaal_fase()
        self.assertTrue(comp.fase_indiv >= 'F')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))

    def test_bestaat_niet(self):
        # niet bestaande comp_pk / seizoen
        resp = self.client.get(self.url_overzicht % 999999)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bestaat-niet.dtl', 'plein/site_layout.dtl'))


# end of file
