# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh


class TestCompLaagRegioKiesZevenWedstrijden(bh.BrowserTestCase):

    url_sporter_zeven_wedstrijden = '/bondscompetities/regio/keuze-zeven-wedstrijden/%s/'  # deelnemer_pk

    def test_kies_zeven_wedstrijden(self):
        # inloggen (zonder OTP controle)
        self.do_login()

        # regio_deelnemer_c is in regio101 met inschrijfmethode 1
        deelnemer = self.regio_deelnemer_c

        # wijzig scherm opvragen
        url = self.url_sporter_zeven_wedstrijden % deelnemer.pk
        self.do_navigate_to(url)
        self.assertEqual(self._driver.title, 'Wedstrijden kiezen')

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()

        # zet een vinkje
        for el in self.find_elements_checkbox():
            if el.text:
                self.click_if_possible(el)
                break
        # for

        # druk op de knop om meer wedstrijden op te roepen
        knop = self.find_element_by_id('id_button_toon_meer_wedstrijden')
        knop.click()

        # controleer dat er geen fouten waren
        self.assert_no_console_log()

        # druk op de Opslaan knop
        knop = self.find_element_by_id('submit_knop')
        knop.click()


# end of file
