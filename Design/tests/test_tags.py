# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Design.templatetags.design_filters import (filter_highlight, filter_wbr_email, filter_wbr_dagdeel, filter_wbr_www,
                                                filter_wbr_seizoen)
from Design.templatetags.design_icons import sv_icon


class TestDesignTemplatetags(TestCase):

    """ tests voor de Design applicatie, module Template tags """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_filter_highlight(self):
        self.assertEqual(filter_highlight("", None), "")
        self.assertEqual(filter_highlight("ramon", None), "ramon")
        self.assertEqual(filter_highlight("ramon", ""), "ramon")
        self.assertEqual(filter_highlight("ramon", "jaja"), "ramon")
        self.assertEqual(filter_highlight("ramon", "ra"), '<b class="sv-rood-text">ra</b>mon')
        self.assertEqual(filter_highlight("ramon", "mo"), 'ra<b class="sv-rood-text">mo</b>n')
        self.assertEqual(filter_highlight("ramon", "on"), 'ram<b class="sv-rood-text">on</b>')

    def test_filter_wbr_email(self):
        self.assertEqual(filter_wbr_email("ramon@gmail.not"),
                         "ramon<wbr>@gmail<wbr>.not")

        self.assertEqual(filter_wbr_email("ramon.tester@gmail.not"),
                         "ramon<wbr>.tester<wbr>@gmail<wbr>.not")

        self.assertEqual(filter_wbr_email("ramon.tester@gmail.not"),
                         "ramon<wbr>.tester<wbr>@gmail<wbr>.not")

        self.assertEqual(filter_wbr_email("ramon@handboogsport.not"),
                         "ramon<wbr>@handboog<wbr>sport<wbr>.not")

        self.assertEqual(filter_wbr_email("handboogsport@ramon.not"),
                         "handboog<wbr>sport<wbr>@ramon<wbr>.not")

    def test_filter_wbr_www(self):
        self.assertEqual(filter_wbr_www('www.test.nl'),
                         'www.<wbr>test.<wbr>nl')

        self.assertEqual(filter_wbr_www('http://www.not'),
                         'http://<wbr>www.<wbr>not')

        # / aan het einde
        self.assertEqual(filter_wbr_www('https://www.not/test/'),
                         'https://<wbr>www.<wbr>not/<wbr>test/')

        # . na /
        self.assertEqual(filter_wbr_www('https://test/x.y'),
                         'https://<wbr>test/<wbr>x.<wbr>y')

        # underscore
        self.assertEqual(filter_wbr_www('https://test/x_y'),
                         'https://<wbr>test/<wbr>x_<wbr>y')

        # . na _
        self.assertEqual(filter_wbr_www('https://test/x_y/x.y'),
                         'https://<wbr>test/<wbr>x_<wbr>y/<wbr>x.<wbr>y')

        # lange woorden
        self.assertEqual(filter_wbr_www('handboogsport.nl/grensoverschreidend-gedrag'),
                         'handboog<wbr>sport.<wbr>nl/<wbr>grens<wbr>over<wbr>schreidend-gedrag')

        self.assertEqual(filter_wbr_www('grensoverschreidend.nl/handboogsport'),
                         'grens<wbr>over<wbr>schreidend.<wbr>nl/<wbr>handboog<wbr>sport')

        # lange url
        self.assertEqual(filter_wbr_www('https://dit-is-een-erg-lange-url-die-afgekapt-gaat-worden'),
                         'https://<wbr>dit-is-een-erg-lange-url-die-afgekapt-gaat...')

    def test_filter_wbr_dagdeel(self):
        self.assertEqual(filter_wbr_dagdeel("WO"),
                         '<span class="hide-on-med-and-up">W</span>' +
                         '<span class="hide-on-small-only">Woensdag</span>')

        self.assertEqual(filter_wbr_dagdeel("ZAo"),
                         '<span class="hide-on-med-and-up">Za-Och</span>' +
                         '<span class="hide-on-small-only">Zaterdag<wbr>ochtend</span>')

        self.assertEqual(filter_wbr_dagdeel("Huh??"), "Huh??")

    def test_filter_wbr_seizoen(self):
        self.assertEqual(filter_wbr_seizoen("Testje"), '<wbr>Testje')
        self.assertEqual(filter_wbr_seizoen("2022/2023"), '2022/<wbr>2023')

    def test_icon(self):
        self.assertEqual(sv_icon('email'), '<i class="notranslate material-symbol sv-rood-text">mail</i>')

        with self.assertRaises(ValueError):
            sv_icon('#does not exist')

        # varianten
        out = sv_icon('email', kleur='kleur', extra_class='klass', extra_style='stijl:1')
        self.assertEqual(out, '<i class="notranslate material-symbol kleur klass" style="stijl:1">mail</i>')

        out = sv_icon('email', kleur='')
        self.assertTrue('sv-rood-text' not in out)

# end of file
