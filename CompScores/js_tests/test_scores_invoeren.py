# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
import time


class TestCompScoresInvoeren(bh.BrowserTestCase):

    """ Test de CompScores applicatie, gebruik van scores_invoeren.js vanuit de browser """

    url_uitslag_invoeren = '/bondscompetities/scores/uitslag-invoeren/%s/'          # match_pk

    def test_invoeren(self):
        self.do_wissel_naar_hwl()       # redirect naar /vereniging/

        # ga naar de uitslag invoeren pagina
        url = self.url_uitslag_invoeren % self.match.pk
        self.do_navigate_to(url)

        # zoek op bondsnummer
        self.find_element_by_id('id_lid_nr').send_keys(str(self.sporter.lid_nr))
        self.find_element_by_id('id_zoek_knop').click()
        # JS: dynamische interactie met server + update van de getoonde lijst
        time.sleep(0.5)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # result is opgehaald, wordt getoond en kan toegevoegd worden aan de lijst
        btn = self.find_element_by_id('id_btn_toevoegen')
        btn.click()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # kaartje "lijst ophalen"
        kaartje = self.find_kaartje_met_titel('Lijst ophalen')
        kaartje.click()
        # JS: dynamische interactie met server + update van getoonde lijst
        time.sleep(0.5)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # TODO: knop "opslaan" (nadat score ingevoerd is)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

# end of file
