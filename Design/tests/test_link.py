# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Design.templatetags.design_link import sv_link_ext


class TestDesignTemplatetags(TestCase):

    """ tests voor de Design applicatie, module Template tags """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_link_ext(self):
        out = sv_link_ext(url='not://test.not/')
        self.assertTrue('href="not://test.not/"' in out)
        self.assertTrue('<svg ' in out)


# end of file
