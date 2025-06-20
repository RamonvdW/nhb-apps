# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from selenium.webdriver.common.keys import Keys
import time


class TestOverigTabelFilter(bh.BrowserTestCase):

    """ Test de Overig applicatie, gebruik van tabel_filter.js vanuit de browser """

    url_activiteit = '/overig/activiteit/'

    def test_tabel_filter(self):
        self.do_wissel_naar_bb()

        # controleer dat we ingelogd zijn
        # gebruik het tabel filter
        self.do_navigate_to(self.url_activiteit)
        # print(self.get_page_html())
        el_input = self.find_tabel_filter_input('tabel_nieuwe')
        self.assertIsNotNone(el_input)
        el_input.send_keys('2')
        time.sleep(0.1)
        el_input.send_keys(Keys.BACKSPACE)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
