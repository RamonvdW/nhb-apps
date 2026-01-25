# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Design.templatetags.design_knop import sv_knop_nav, sv_knop_mailto, sv_knop_ext, sv_knop_modal


class TestDesignTemplatetags(TestCase):

    """ tests voor de Design applicatie, module Template tags """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_knop_nav(self):
        sv_knop_nav.cache_clear()
        out = sv_knop_nav(icon='open url', tekst='Hello')
        self.assertTrue('btn-sv-rood' in out)
        self.assertTrue('Hello' in out)

        out = sv_knop_nav(icon='open url', kleur='blauw', extra_class="klasje", extra_style="stijl:1", tekst='')
        self.assertTrue('btn-sv-blauw' in out)
        self.assertTrue('klasje' in out)
        self.assertTrue('stijl:1' in out)

        out = sv_knop_nav(icon='open url', smal=True)
        out = sv_knop_nav(icon='open url', smal=True, extra_style='stijl:2', knop_id='my_id')
        self.assertTrue('stijl:2' in out)
        self.assertTrue('id="my_id"' in out)

    def test_knop_mailto(self):
        sv_knop_mailto.cache_clear()
        out = sv_knop_mailto(email='to@test.not')
        self.assertTrue('mailto:to@test.not' in out)
        self.assertTrue('btn-sv-rood' in out)

        out = sv_knop_mailto(email='to@test.not', kleur='blauw', icon='')
        self.assertTrue('mailto:to@test.not' in out)
        self.assertTrue('btn-sv-blauw' in out)

    def test_knop_ext(self):
        sv_knop_ext.cache_clear()
        out = sv_knop_ext(url='//test.not', icon='open kaart', tekst='')
        self.assertTrue('href="//test.not"' in out)
        self.assertTrue('<svg ' in out)
        self.assertTrue('btn-sv-rood' in out)

        out = sv_knop_ext(kleur='blauw', icon='email', tekst='hello', url='//test.not', extra_style='stijl')
        self.assertTrue('stijl' in out)
        self.assertTrue('hello' in out)
        self.assertTrue('<svg ' in out)
        self.assertTrue('href="//test.not"' in out)
        self.assertTrue('btn-sv-blauw' in out)

    def test_knop_modal(self):
        sv_knop_modal.cache_clear()
        out = sv_knop_modal('eerste_', 'tweede', tekst='test')
        self.assertTrue('#eerste_tweede' in out)
        self.assertTrue('modal-trigger' in out)

        out = sv_knop_modal('eerste_', 'tweede', tekst='test', icon='verwijder', extra_class='test')

# end of file
