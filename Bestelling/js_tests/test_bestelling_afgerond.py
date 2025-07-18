# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.definities import (BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_AFGEROND,
                                   BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD)
from Bestelling.models import Bestelling
from TestHelpers import browser_helper as bh
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
import time


class TestBrowserBestellingAfgerond(MyMgmtCommandHelper, bh.BrowserTestCase):

    """ Test de Bestelling applicatie, gebruik van bestelling_afgerond.js vanuit de browser """

    url_mandje = '/bestel/mandje/'
    url_afgerond = '/bestel/na-de-betaling/%s/'     # bestel_nr
    url_webwinkel_product = '/webwinkel/product-%s/'    # webwinkelproduct.pk

    def test_bestelling_afgerond(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        # leg een product in het mandje
        self.do_navigate_to(self.url_webwinkel_product % self.webwinkel_product.pk)
        knop = self.find_element_type_with_text('button', 'Leg in mijn mandje')
        knop.click()
        time.sleep(0.5)

        # mandje omzetten in een bestelling
        self.do_navigate_to(self.url_mandje)
        knop = self.find_element_type_with_text('button', 'Bestelling afronden')
        knop.click()
        time.sleep(0.5)     # wacht op de achtergrondtaak

        bestelling = Bestelling.objects.first()
        # print('bestelling: %s' % bestelling)

        # GET kan wachten op de achtergrondtaak (betaling ontvangen van CPSP)
        snel = '?snel=1'        # we willen niet wachten
        url = self.url_afgerond % bestelling.bestel_nr + snel

        # betaling actief --> afgerond
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)
        time.sleep(0.5)     # eerste check is na 250ms, daarna volgt een retry

        bestelling.status = BESTELLING_STATUS_AFGEROND
        bestelling.save(update_fields=['status'])
        time.sleep(1)       # wacht tot de nieuwe status opgepikt is (1250ms minimum)

        # betaling actief --> mislukt
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)

        # aanpassen voordat de status opgehaald is
        bestelling.status = BESTELLING_STATUS_MISLUKT
        bestelling.save(update_fields=['status'])
        time.sleep(0.5)     # wacht tot de nieuwe status opgepikt is (eerste check is na 250ms)

        # 404 antwoord
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)

        bestelling.status = BESTELLING_STATUS_GEANNULEERD       # resulteert in Http404
        bestelling.save(update_fields=['status'])
        time.sleep(1)       # wacht tot de nieuwe status opgepikt is (eerste check na 250ms)

        # test afhandeling van timeouts
        self.set_short_xhr_timeouts()
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)
        time.sleep(0.5)     # eerste check wordt na 250ms gedaan

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
