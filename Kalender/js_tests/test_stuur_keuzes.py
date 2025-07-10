# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from selenium.webdriver.common.keys import Keys
import time


class TestBrowserKalenderStuurKeuzes(bh.BrowserTestCase):

    url_maand = '/kalender/maand/%s/%s/'                # jaar, maand
    url_jaar = '/kalender/jaar/%s/%s/alle/alle/'        # jaar, maand, soort, bogen

    def test_jaar(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        url = self.url_jaar % (self.wedstrijd_1.datum_begin.year,
                               self.wedstrijd_1.datum_begin.month)

        self.do_navigate_to(url)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # filters uitklappen
        filter_knop = self.find_element_by_id('id_filter_knop')
        filter_knop.click()
        time.sleep(0.25)     # wait for the animation to complete

        # filters inklappen
        filter_knop.click()
        time.sleep(0.25)     # wait for the animation to complete

        # click the 'prev' button
        prev_knop = self.find_element_by_id('id_prev')
        prev_knop.click()
        time.sleep(0.25)        # wait for page to load

        # click the 'next' button
        prev_knop = self.find_element_by_id('id_next')
        prev_knop.click()
        time.sleep(0.25)        # wait for page to load

        # zoek
        filter_knop = self.find_element_by_id('id_filter_knop')
        filter_knop.click()
        time.sleep(0.25)     # wait for the animation to complete

        zoek = self.find_element_by_id('id_zoekterm')
        zoek.send_keys('test')
        zoek.send_keys(Keys.ENTER)
        time.sleep(0.25)        # wait for page to load

        # filters uitklappen
        filter_knop = self.find_element_by_id('id_filter_knop')
        filter_knop.click()
        time.sleep(0.25)     # wait for the animation to complete

        # wijzig iets in het filter
        nr = 0
        for el in self.find_elements_radio(exclude_selected=True):
            nr += 1
            if nr in (1, 4, 8):
                el.click()
        # for

        activeer_knop = self.find_element_by_id('id_activeer_1')
        activeer_knop.click()
        time.sleep(0.25)        # wait for page to load

        # wissel naar maandoverzicht
        switch_knop = self.find_element_by_id('id_switch')
        switch_knop.click()
        time.sleep(0.25)        # wait for page to load

    def test_maand(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        url = self.url_maand % (self.wedstrijd_1.datum_begin.year,
                                self.wedstrijd_1.datum_begin.month)

        self.do_navigate_to(url)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # filters uitklappen
        filter_knop = self.find_element_by_id('id_filter_knop')
        filter_knop.click()
        time.sleep(0.5)     # wait for the animation to complete

        # filters inklappen
        filter_knop.click()
        time.sleep(0.5)     # wait for the animation to complete

        # click the 'prev' button
        prev_knop = self.find_element_by_id('id_prev')
        prev_knop.click()
        time.sleep(0.25)        # wait for page to load

        # click the 'next' button
        prev_knop = self.find_element_by_id('id_next')
        prev_knop.click()
        time.sleep(0.25)        # wait for page to load

        # zoek
        filter_knop = self.find_element_by_id('id_filter_knop')
        filter_knop.click()
        time.sleep(0.25)     # wait for the animation to complete

        zoek = self.find_element_by_id('id_zoekterm')
        zoek.send_keys('zoek dit')

        # gebruik de zoek-knop
        zoek_knop = self.find_element_by_id('id_zoek')
        zoek_knop.click()

        # wissel naar jaaroverzicht
        switch_knop = self.find_element_by_id('id_switch')
        switch_knop.click()
        time.sleep(0.25)        # wait for page to load

        # filters uitklappen
        filter_knop = self.find_element_by_id('id_filter_knop')
        filter_knop.click()
        time.sleep(0.25)     # wait for the animation to complete

        # wijzig de filters
        nr = 0
        for el in self.find_elements_radio(exclude_selected=True):
            nr += 1
            if nr in (1, 3, 7):
                el.click()
        # for

        activeer_knop = self.find_element_by_id('id_activeer_2')
        activeer_knop.click()


# end of file
