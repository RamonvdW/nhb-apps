# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh


class TestOverigPaginaFilters(bh.BrowserTestCase):

    """ Test de Overig applicatie, gebruik van pagina_filters.js vanuit de browser """

    # wordt gebruikt in: CompUitslagen, HistComp, Records
    url_pagina_met_filters_1 = '/records/indiv/'

    def test_alles(self):
        self.do_wissel_naar_sporter()

        # ga naar de pagina waar de filters gebruikt worden
        self.do_navigate_to(self.url_pagina_met_filters_1)

        # klik op een van de radio buttons met mirroring
        mirror_radios = self.find_elements_with_class("sv-mirror-filter")
        for radio in mirror_radios:
            if not radio.is_selected():
                el_span = self.get_following_sibling(radio)
                # print('span.is_displayed: %s, radio.id=%s' % (el_span.is_displayed(), radio.get_attribute('id')))
                if el_span.is_displayed():
                    el_span.click()
                    break   # from the for
        # for

        # klik op een van de Activeer knoppen
        # dit roept de activeer_filter functie aan
        activeer_knoppen = self.find_elements_with_class("btn-sv-activeer-filter")
        activeer_knoppen[0].click()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
