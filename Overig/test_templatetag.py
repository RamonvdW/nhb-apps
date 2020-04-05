# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .templatetags.overig_filters import filter_highlight


class TestOverigTemplatetags(TestCase):
    """ unit tests voor de Overig applicatie, module Template tags """

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

# end of file
