# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.definities import BESTELLING_STATUS_BETALING_ACTIEF
from TestHelpers import browser_helper as bh
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
import time


class TestBrowserBestellingMandjeVerwijder(MyMgmtCommandHelper, bh.BrowserTestCase):

    """ Test de Bestelling applicatie, gebruik van mandje_verwijder.js vanuit de browser """

    url_afgerond = '/bestel/na-de-betaling/%s/'     # bestel_nr

    def test_bestelling_afgerond(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        self.bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        self.bestelling.save(update_fields=['status'])

        self.do_navigate_to(self.url_afgerond % self.bestelling.bestel_nr)
        time.sleep(1)
        return

        knop = self.find_element_type_with_text('button', 'Leg in mijn mandje')
        knop.click()
        # click doet een POST naar de webserver
        # deze wacht 3 seconden wacht op de achtergrondtaak voordat "Product is gereserveerd" volgt
        # TODO: voorkom wachten

        # laat de achtergrondtaak de mutatie verwerken, waardoor het product in het mandje komt
        self.verwerk_bestel_mutaties(show_all=True)

        # bekijk het mandje
        self.do_navigate_to(self.url_mandje)

        # verwijder het product uit het mandje
        button = self.find_elements_buttons()[0]
        button.click()
        # click doet een POST naar de webserver
        # deze wacht 3 seconden wacht op de achtergrondtaak voordat "Product is gereserveerd" volgt
        # TODO: voorkom wachten

        # laat verwijderen uit het mandje verwerken
        self.verwerk_bestel_mutaties(show_all=True)

        # bekijk het mandje
        self.do_navigate_to(self.url_mandje)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
