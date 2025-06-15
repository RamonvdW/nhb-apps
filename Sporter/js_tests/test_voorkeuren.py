# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from TestHelpers import browser_helper as bh
import time


class TestBrowserSporterVoorkeuren(bh.BrowserTestCase):

    """ Test de Sporter applicatie, gebruik van voorkeuren.js vanuit de browser """

    url_voorkeuren = '/sporter/voorkeuren/'

    def test_voorkeuren(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        self.do_navigate_to(self.url_voorkeuren)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # klik op een checkbox
        # hierdoor wordt de "opslaan" knop getoond

        boxes = self.find_elements_checkbox()
        box = boxes[0]
        box.click()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
