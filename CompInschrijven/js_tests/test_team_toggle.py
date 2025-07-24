# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from TestHelpers import browser_helper as bh
import time


class TestBrowserCompInschrijvenTeamToggle(bh.BrowserTestCase):

    url_hwl_leden_ingeschreven = '/bondscompetities/deelnemen/leden-ingeschreven/%s/'  # deelcomp_pk

    def test_team_toggle(self):
        # inloggen en HWL worden
        self.do_pass_otp()
        self.do_wissel_naar_hwl()

        zet_competitie_fase_regio_inschrijven(self.comp)

        # haal de pagina met ingeschreven leden op
        url = self.url_hwl_leden_ingeschreven % self.regio_comp.pk
        self.do_navigate_to(url)

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()

        knop = self.find_element_type_with_text('a', 'Maak Nee')
        knop.click()        # doet page reload

        time.sleep(0.5)

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()

        knop = self.find_element_type_with_text('a', 'Maak Ja')
        knop.click()        # doet page reload


# end of file
