# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.helpers import get_safe_from_ip, maak_unaccented


class TestOverigHelpers(TestCase):

    """ tests voor de Overig applicatie, module Helpers """

    def setUp(self):
        """ initialisatie van de test case """
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

        self.client.META['REMOTE_ADDR'] = '0000:1111:2222:3344:5555:6666:aabb:ccdd:EEFF'                    # noqa
        self.assertEqual(get_safe_from_ip(self.client), '0000:1111:2222:3344:5555:6666:aabb:ccdd:EEFF')     # noqa

        self.client.META['REMOTE_ADDR'] = 'wat een puinhoop\0<li>'
        self.assertEqual(get_safe_from_ip(self.client), 'aee')

        self.assertEqual(maak_unaccented('Ramõn'), 'Ramon')
        self.assertEqual(maak_unaccented('Hé däär ên ìetsỳ'), 'He daar en ietsy')       # noqa

# end of file
