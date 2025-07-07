# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time


class TestCompScoresInvoeren(bh.BrowserTestCase):

    """ Test de CompScores applicatie, gebruik van scores_invoeren.js vanuit de browser """

    url_uitslag_invoeren = '/bondscompetities/scores/uitslag-invoeren/%s/'          # match_pk

    def test_invoeren(self):
        self.do_wissel_naar_hwl()       # redirect naar /vereniging/

        # ga naar de uitslag invoeren pagina
        url = self.url_uitslag_invoeren % self.match.pk
        self.do_navigate_to(url)

        if True:
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

        if True:
            # score invoeren: dit triggert de controleer_score functie
            td = self.find_element_type_with_text('td', str(self.sporter.lid_nr))
            tr = self.get_parent(td)
            # doorzoek de regel naar input velden - dit is er maar 1
            the_inp = None
            for inp in tr.find_elements(By.XPATH, ".//input"):
                the_inp = inp
            # for
            if the_inp:
                # bad score
                the_inp.send_keys('666')
                the_inp.send_keys(Keys.TAB)     # go to next field, triggers oninput

                # ok score
                #the_inp = self.get_active_element()
                the_inp.clear()
                the_inp.send_keys('111')
                the_inp.send_keys(Keys.TAB)     # go to next field, triggers oninput

            # controleer dat er geen meldingen van de browser zijn over de JS bestanden
            self.assert_no_console_log()

        if True:
            # druk op de opslaan knop
            self.find_element_by_id('id_opslaan_knop').click()
            # JS: dynamische interactie met server
            time.sleep(0.5)

            # controleer dat er geen meldingen van de browser zijn over de JS bestanden
            self.assert_no_console_log()

        # ververs de pagina
        #self.do_navigate_to(url)
        # toont alleen het lid met de ingevoerde score

        if True:
            # nog een keer hetzelfde lid zoeken en toevoegen
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

        if True:
            # kaartje "lijst ophalen"
            kaartje = self.find_kaartje_met_titel('Lijst ophalen')
            kaartje.click()
            # JS: dynamische interactie met server + update van getoonde lijst
            time.sleep(0.5)

            # controleer dat er geen meldingen van de browser zijn over de JS bestanden
            self.assert_no_console_log()

        if True:
            # geen input
            self.find_element_by_id('id_lid_nr').clear()        # empties the input field
            self.find_element_by_id('id_zoek_knop').click()

            # geen interactie met server omdat input leeg was

            # controleer dat er geen meldingen van de browser zijn over de JS bestanden
            self.assert_no_console_log()

        if True:
            # zoek op niet bestaand bondsnummer + gebruik van Enter toets
            self.find_element_by_id('id_lid_nr').send_keys("999999")
            self.find_element_by_id('id_lid_nr').send_keys(Keys.RETURN)
            # JS: dynamische interactie met server + update van de getoonde lijst
            time.sleep(0.5)

            # controleer dat er geen meldingen van de browser zijn over de JS bestanden
            self.assert_no_console_log()

        if True:
            # rare input ipv bondsnummer
            self.find_element_by_id('id_lid_nr').clear()        # empties the input field
            self.find_element_by_id('id_lid_nr').send_keys('"')
            self.find_element_by_id('id_zoek_knop').click()
            # JS: dynamische interactie met server + update van de getoonde lijst
            time.sleep(0.5)

            # controleer dat er geen meldingen van de browser zijn over de JS bestanden
            self.assert_no_console_log()


# end of file
