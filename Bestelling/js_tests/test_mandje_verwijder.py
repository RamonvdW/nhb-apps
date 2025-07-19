# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.models import BestellingMutatie
from TestHelpers import browser_helper as bh
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
import time


class TestBrowserBestellingMandjeVerwijder(MyMgmtCommandHelper, bh.BrowserTestCase):

    """ Test de Bestelling applicatie, gebruik van mandje_verwijder.js vanuit de browser """

    url_mandje = '/bestel/mandje/'
    url_webwinkel_product = '/webwinkel/product-%s/'    # webwinkelproduct.pk

    def test_mandje_verwijder(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        BestellingMutatie.objects.all().delete()

        # leg een product in het mandje
        self.do_navigate_to(self.url_webwinkel_product % self.webwinkel_product.pk)

        knop = self.find_element_type_with_text('button', 'Leg in mijn mandje')
        self.click_not_blocking(knop)
        # geef het script en de server wat tijd om de bestelmutatie te maken
        time.sleep(0.25)

        # click handler JS script heeft een POST gedaan
        # die maakt een mutatie record voor de achtergrond taak
        # wacht daarna tot 3 seconden op de achtergrondtaak (welke niet draait)
        # en geeft daarna de http response ("Product is gereserveerd" pagina)
        # hier willen we niet op wachten

        # laat de achtergrondtaak de mutatie verwerken, waardoor het product in het mandje komt
        self.verwerk_bestel_mutaties()

        # bekijk het mandje
        self.do_navigate_to(self.url_mandje)

        # verwijder het product uit het mandje
        buttons = self.find_elements_buttons()
        if len(buttons) == 0:
            # print('[ERROR] Verwijder knop niet gevonden - sleep 30')
            # time.sleep(30)
            self.fail('Verwijder knop niet gevonden!')

        button = buttons[0]
        self.click_not_blocking(button)

        # geef het script wat tijd om de POST te doen --> form POST laadt de pagina opnieuw
        # geef de achtergrondtaak wat tijd om de bestelmutatie te verwerken
        time.sleep(0.5)

        # bekijk het mandje
        el_p_je_mandje_is_leeg = self.find_element_type_with_text('p', 'Je mandje is leeg')
        self.assertIsNotNone(el_p_je_mandje_is_leeg)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
