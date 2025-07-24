# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from TestHelpers import browser_helper as bh
import time


class TestBrowserSporterProfiel(bh.BrowserTestCase):

    """ Test de Sporter applicatie, gebruik van profiel.js vanuit de browser """

    url_profiel = '/sporter/'

    def test_profiel(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        zet_competitie_fase_regio_inschrijven(self.comp)
        self.do_navigate_to(self.url_profiel)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # afmelden voor het RK
        span = self.find_element_type_with_text('span', 'Afmelden')
        knop = self.get_parent(span)
        knop.click()        # opent model dialog

        button = self.find_active_button_on_open_modal_dialog()
        button.click()
        time.sleep(0.1)     # browser submits the form and reloads the page

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # uitschrijven voor de regiocompetitie
        span = self.find_element_type_with_text('span', 'Uitschrijven')
        knop = self.get_parent(span)
        knop.click()        # opent model dialog

        button = self.find_active_button_on_open_modal_dialog()
        button.click()

        # wacht tot de form post uitgevoerd is en de pagina opnieuw ingeladen is
        time.sleep(0.1)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
