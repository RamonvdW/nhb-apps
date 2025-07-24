# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
import time


class TestBondspasOphalen(bh.BrowserTestCase):

    url_bondspas = '/bondspas/toon/'

    def test_login(self):
        # de support functies doen al een groot deel van de test die we willen doen

        # inloggen (voor het geval we uitgelogd waren)
        self.do_login()

        # haal de bondspas pagina op
        # deze gaat automatisch het plaatje opvragen (via een POST)
        self.do_navigate_to(self.url_bondspas)

        # wacht even totdat het plaatje binnen is
        time.sleep(0.5)

        # controleer dat er geen fouten in de console log staan
        self.assert_no_console_log()

        # gast account mag geen bondspas krijgen, dus 404
        # dit triggert een apart pad in het JS

        # haal de bondspas pagina opnieuw op
        self.do_navigate_to(self.url_bondspas)

        # snelle wijziging voordat de browser de pagina opgehaald heeft
        # we hebben 100ms
        self.sporter.is_gast = True
        self.sporter.save(update_fields=['is_gast'])

        # wacht even totdat het plaatje binnen is
        time.sleep(0.5)

        # controleer dat er geen fouten in de console log staan
        self.assert_no_console_log()

        self.sporter.is_gast = False
        self.sporter.save(update_fields=['is_gast'])

        # forceer de timeout hantering in de JS code
        self.set_short_xhr_timeouts()
        self.do_navigate_to(self.url_bondspas)
        time.sleep(0.1)

        # controleer dat er geen fouten in de console log staan
        self.assert_no_console_log()


# end of file
