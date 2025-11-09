# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Design.templatetags.design_icons import sv_icon, sv_icon_op_button
from Design.icon_svg.Material_Symbols.symbol_svg import MATERIAL_SYMBOL_SVG
from Design.icon_svg.sv_symbols.symbol_svg import SV_SYMBOL_SVG


class TestDesignTemplatetags(TestCase):

    """ tests voor de Design applicatie, module Template tags """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_icon_material_symbol(self):
        sv_icon.cache_clear()           # in verband met functools.cache gebruik

        out = sv_icon('email')
        self.assertTrue(out.startswith('<svg '))

        with self.assertRaises(ValueError):
            sv_icon('#does not exist')

        # varianten
        out = sv_icon('email', kleur='groen')
        self.assertTrue(out.startswith('<svg '))
        self.assertTrue('green-text' in out)

        out = sv_icon('email', kleur='')
        self.assertTrue(out.startswith('<svg '))

        out = sv_icon('email', kleur='', extra_style='stijl:1')
        self.assertTrue(out.startswith('<svg '))
        self.assertTrue('stijl:1' in out)

        with self.assertRaises(ValueError):
            sv_icon('email', kleur='not-a-color')

        # toevoeging commentaar met icoon naam
        sv_icon.cache_clear()  # in verband met functools.cache gebruik
        with override_settings(DEBUG=True):
            out = sv_icon('email')
            self.assertTrue('<!-- ' in out)

        # exception handling
        temp = MATERIAL_SYMBOL_SVG['download']       # backup
        del MATERIAL_SYMBOL_SVG['download']
        with self.assertRaises(ValueError):
            sv_icon('download')
        MATERIAL_SYMBOL_SVG['download'] = temp       # restore

    def test_icon_sv_symbol(self):
        sv_icon_name = 'zoom details'
        sv_icon.cache_clear()           # in verband met functools.cache gebruik

        out = sv_icon(sv_icon_name)
        self.assertTrue(out.startswith('<svg '))

        # toevoeging commentaar met icoon naam
        sv_icon.cache_clear()  # in verband met functools.cache gebruik
        with override_settings(DEBUG=True):
            out = sv_icon(sv_icon_name)
            self.assertTrue('<!-- ' in out)

        sv_icon.cache_clear()  # in verband met functools.cache gebruik
        out = sv_icon(sv_icon_name, kleur='', extra_style='stijl:1')
        self.assertTrue(out.startswith('<svg '))
        self.assertTrue('stijl:1' in out)

        # exception handling
        sv_icon.cache_clear()  # in verband met functools.cache gebruik
        temp = SV_SYMBOL_SVG['zoom_in']       # backup
        del SV_SYMBOL_SVG['zoom_in']
        with self.assertRaises(ValueError):
            sv_icon(sv_icon_name)
        SV_SYMBOL_SVG['zoom_in'] = temp       # restore

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
