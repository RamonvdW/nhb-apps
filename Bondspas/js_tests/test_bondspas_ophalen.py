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
        time.sleep(5)

        # controleer dat er geen fouten in de console log staan
        self.assert_no_console_log()


# end of file
