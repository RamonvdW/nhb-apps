# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Design.templatetags.design_icons import sv_icon, sv_icon_op_button
from Design.icon_svg.Material_Symbols.icon_svg import MATERIAL_ICONS_SVG


class TestDesignTemplatetags(TestCase):

    """ tests voor de Design applicatie, module Template tags """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_icon(self):
        sv_icon.cache_clear()           # in verband met functools.cache gebruik

        out = sv_icon('email')
        self.assertTrue(out.startswith('<svg '))

        with self.assertRaises(ValueError):
            sv_icon('#does not exist')

        # varianten
        out = sv_icon('email', kleur='kleur')
        self.assertTrue(out.startswith('<svg '))
        self.assertTrue('kleur' in out or 'green-text' in out)      # TODO: tijdelijk

        out = sv_icon('email', kleur='')
        self.assertTrue(out.startswith('<svg '))

        # toevoeging commentaar met icoon naam
        sv_icon.cache_clear()  # in verband met functools.cache gebruik
        with override_settings(DEBUG=True):
            out = sv_icon('email')
            self.assertTrue('<!-- ' in out)

        # exception handling
        temp = MATERIAL_ICONS_SVG['download']       # backup
        del MATERIAL_ICONS_SVG['download']
        with self.assertRaises(ValueError):
            sv_icon('download')
        MATERIAL_ICONS_SVG['download'] = temp       # restore

    def test_icon_op_button(self):
        sv_icon.cache_clear()           # in verband met functools.cache gebruik

        out = sv_icon_op_button('email')
        self.assertTrue('<svg ' in out)
        self.assertFalse('Hello' in out)

        out = sv_icon_op_button('email', tekst='Hello')
        self.assertTrue('Hello' in out)

        out = sv_icon_op_button('email', extra_class='klasje')
        self.assertTrue('klasje' in out)

        out = sv_icon_op_button('email', extra_style='stijl')
        self.assertTrue('stijl' in out)


# end of file
