# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .templatetags.overig_filters import filter_highlight, filter_wbr_email, filter_wbr_dagdeel


class TestOverigTemplatetags(TestCase):

    """ tests voor de Overig applicatie, module Template tags """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_filter_highlight(self):
        self.assertEqual(filter_highlight("", None), "")
        self.assertEqual(filter_highlight("ramon", None), "ramon")
        self.assertEqual(filter_highlight("ramon", ""), "ramon")
        self.assertEqual(filter_highlight("ramon", "jaja"), "ramon")
        self.assertEqual(filter_highlight("ramon", "ra"), "<b>ra</b>mon")
        self.assertEqual(filter_highlight("ramon", "mo"), "ra<b>mo</b>n")
        self.assertEqual(filter_highlight("ramon", "on"), "ram<b>on</b>")

    def test_filter_wbr_email(self):
        self.assertEqual(filter_wbr_email("ramon@gmail.not"), "ramon<wbr>@gmail<wbr>.not")
        self.assertEqual(filter_wbr_email("ramon.tester@gmail.not"), "ramon<wbr>.tester<wbr>@gmail<wbr>.not")

    def test_filter_wbr_dagdeel(self):
        self.assertEqual(filter_wbr_dagdeel("WO"),
                         '<span class="hide-on-med-and-up">W</span>' +
                         '<span class="hide-on-small-only">Woensdag</span>')

        self.assertEqual(filter_wbr_dagdeel("ZAo"),
                         '<span class="hide-on-med-and-up">Za-Och</span>' +
                         '<span class="hide-on-small-only">Zaterdag<wbr>ochtend</span>')

        self.assertEqual(filter_wbr_dagdeel("Huh??"), "Huh??")

# end of file
