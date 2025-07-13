# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.definities import (BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_AFGEROND,
                                   BESTELLING_STATUS_MISLUKT)
from TestHelpers import browser_helper as bh
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
import time


class TestBrowserBestellingMandjeVerwijder(MyMgmtCommandHelper, bh.BrowserTestCase):

    """ Test de Bestelling applicatie, gebruik van bestelling_afgerond.js vanuit de browser """

    url_afgerond = '/bestel/na-de-betaling/%s/'     # bestel_nr

    def test_bestelling_afgerond(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        # GET kan wachten op de achtergrondtaak, maar dat willen we hier niet
        snel = '?snel=1'
        url = self.url_afgerond % self.bestelling.bestel_nr + snel

        # betaling actief --> afgerond
        self.bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)

        # eerste check is na 250ms, daarna volgt een retry
        time.sleep(0.5)

        self.bestelling.status = BESTELLING_STATUS_AFGEROND
        self.bestelling.save(update_fields=['status'])
        time.sleep(1)     # wacht tot de nieuwe status opgepikt is (1250ms minimum)

        # betaling actief --> mislukt
        self.bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)
        self.bestelling.status = BESTELLING_STATUS_MISLUKT
        self.bestelling.save(update_fields=['status'])
        time.sleep(0.5)     # wacht tot de nieuwe status opgepikt is (eerste query is na 250ms)

        # test afhandeling van timeouts
        self.set_short_xhr_timeouts()
        self.bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)
        time.sleep(0.5)     # eerste check wordt na 250ms gedaan

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
