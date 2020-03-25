# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .helpers import get_safe_from_ip
from .templatetags.overig_filters import filter_highlight


class TestOverigHelpers(TestCase):
    """ unit tests voor de Overig applicatie, module Helpers """

    def setUp(self):
        """ initializatie van de test case """
        pass

    def test_get_safe_from_ip(self):
        self.assertEqual(get_safe_from_ip(None), "")

        self.assertEqual(get_safe_from_ip(self.client), "")

        self.client.META = dict()
        self.assertEqual(get_safe_from_ip(self.client), "")

        self.client.META['REMOTE_ADDR'] = '1.2.3.4'
        self.assertEqual(get_safe_from_ip(self.client), "1.2.3.4")

        self.client.META['REMOTE_ADDR'] = '100.200.300.400'
        self.assertEqual(get_safe_from_ip(self.client), "100.200.300.400")

        self.client.META['REMOTE_ADDR'] = ''
        self.assertEqual(get_safe_from_ip(self.client), "")

        self.client.META['REMOTE_ADDR'] = '0000:1111:2222:3344:5555:6666:aabb:ccdd:EEFF'
        self.assertEqual(get_safe_from_ip(self.client), '0000:1111:2222:3344:5555:6666:aabb:ccdd:EEFF')

        self.client.META['REMOTE_ADDR'] = 'wat een puinhoop\0<li>'
        self.assertEqual(get_safe_from_ip(self.client), 'aee')

    def test_filter_highlight(self):
        self.assertEqual(filter_highlight("", None), "")
        self.assertEqual(filter_highlight("ramon", None), "ramon")
        self.assertEqual(filter_highlight("ramon", ""), "ramon")
        self.assertEqual(filter_highlight("ramon", "jaja"), "ramon")
        self.assertEqual(filter_highlight("ramon", "ra"), "<b>ra</b>mon")
        self.assertEqual(filter_highlight("ramon", "mo"), "ra<b>mo</b>n")
        self.assertEqual(filter_highlight("ramon", "on"), "ram<b>on</b>")

# end of file
