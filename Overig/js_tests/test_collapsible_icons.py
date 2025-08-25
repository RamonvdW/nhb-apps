# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from selenium.webdriver.common.keys import Keys
import time


class TestOverigCollapsibleIcons(bh.BrowserTestCase):

    """ Test de Overig applicatie, gebruik van collapsible_icons.js vanuit de browser """

    url_activiteit = '/overig/activiteit/'

    def test_collapsible(self):
        self.do_wissel_naar_bb()

        # zoek naar accounts
        self.do_navigate_to(self.url_activiteit + '?zoekterm=de')

        # find the clickable header (including plus icon) of the collapsible list
        els = self.find_elements_with_class("collapsible-header")
        el = els[0]
        el.click()          # click to open
        time.sleep(0.3)     # animation takes 300ms

        el.click()          # click to close
        time.sleep(0.3)     # animation takes 300ms


# end of file
