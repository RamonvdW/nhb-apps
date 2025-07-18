# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.definities import (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_STATUS_BETALING_ACTIEF)
from Bestelling.models import Bestelling
from Betaal.models import BetaalMutatie
from TestHelpers import browser_helper as bh
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
import time


class TestBrowserBestellingAfrekenen(MyMgmtCommandHelper, bh.BrowserTestCase):

    """ Test de Bestelling applicatie, gebruik van bestelling_afrekenen.js vanuit de browser """

    url_mandje = '/bestel/mandje/'
    url_afrekenen = '/bestel/afrekenen/%s/'             # bestel_nr
    url_webwinkel_product = '/webwinkel/product-%s/'    # webwinkelproduct.pk
    url_bestelling_details = '/bestel/details/%s/'      # bestel_nr

    def test_bestelling_afrekenen(self):
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
        time.sleep(0.5)

        bestelling = Bestelling.objects.first()
        # print('bestelling: %s' % bestelling)

        url = self.url_bestelling_details % bestelling.bestel_nr
        self.do_navigate_to(url)
        knop = self.find_element_type_with_text('button', 'Betalen')
        knop.click()

        # TODO: waarom geen redirect naar betaal pagina??

        time.sleep(20)
        return


        url = self.url_afrekenen % self.bestelling.bestel_nr

        # betaling nieuw --> mislukt
        self.bestelling.status = BESTELLING_STATUS_NIEUW
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)

        # na 250ms begint het JS script de status op te vragen door middel van een POST
        # vraag wordt elke seconde herhaald, maximaal 20 keer
        time.sleep(2)

        self.bestelling.status = BESTELLING_STATUS_MISLUKT
        self.bestelling.save(update_fields=['status'])
        time.sleep(1.2)

        # betaling nieuw --> geannuleerd --> geeft 404 + exception in JSON parsing in JS
        self.bestelling.status = BESTELLING_STATUS_NIEUW
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)

        # na 250ms begint het JS script de status op te vragen door middel van een POST
        # vraag wordt elke seconde herhaald, maximaal 20 keer
        time.sleep(0.5)

        self.bestelling.status = BESTELLING_STATUS_GEANNULEERD
        self.bestelling.save(update_fields=['status'])
        time.sleep(1.2)

        # betaling nieuw --> actief (zonder betaal mutatie) --> error
        self.bestelling.status = BESTELLING_STATUS_NIEUW
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)

        # na 250ms begint het JS script de status op te vragen door middel van een POST
        # vraag wordt elke seconde herhaald, maximaal 20 keer
        time.sleep(0.5)

        self.bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        self.bestelling.save(update_fields=['status'])
        time.sleep(1.2)

        # betaling nieuw --> actief, met betaal mutatie --> checkout_url
        self.bestelling.status = BESTELLING_STATUS_NIEUW
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)

        # na 250ms begint het JS script de status op te vragen door middel van een POST
        # vraag wordt elke seconde herhaald, maximaal 20 keer
        time.sleep(0.5)

        betaal_mutatie = BetaalMutatie(
                            beschrijving='test',
                            url_checkout=self.live_server_url + '/bondscompetities/',       # bestaand, detecteerbaar
                            payment_id='1234')
        betaal_mutatie.save()

        self.bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        self.bestelling.betaal_mutatie = betaal_mutatie
        self.bestelling.save(update_fields=['status', 'betaal_mutatie'])
        time.sleep(1.2)

        # controleer dat we op de de bondscompetities pagina beland zijn
        curr_url = self.get_current_url()
        # print('current url: %s' % curr_url)
        self.assertTrue(curr_url.endswith('/bondscompetities/'))
        title = self.find_title()
        self.assertEqual(title, 'Bondscompetities')

        # test afhandeling van timeouts
        self.set_short_xhr_timeouts()
        self.bestelling.status = BESTELLING_STATUS_NIEUW
        self.bestelling.save(update_fields=['status'])
        self.do_navigate_to(url)
        time.sleep(0.5)     # eerste check wordt na 250ms gedaan

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
