# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from selenium.webdriver.common.keys import Keys


class TestCompBeheerWijzigDatum(bh.BrowserTestCase):

    url_wijzig_datum = '/bondscompetities/beheer/%s/wijzig-datums/'  # comp_pk

    def test_wijzig_datums(self):
        # inloggen en OTP controle doen
        self.do_pass_otp()
        self.do_wissel_naar_bb()

        # wijzig datums scherm oproepen
        url = self.url_wijzig_datum % self.comp.pk
        self.do_navigate_to(url)
        self.assertEqual(self._driver.title, 'Wijzig datums')

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()

        el = self.find_element_by_id('datum11')
        el.clear()
        el.send_keys('1 december 2024')
        el.send_keys(Keys.TAB)      # triggers onchange() event

        # controleer dat er geen fouten waren
        self.assert_no_console_log()

        # druk op de Opslaan knop
        knop = self.find_element_by_id('opslaan_knop')
        knop.click()


# end of file
