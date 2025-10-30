# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.models import Bestelling, BestellingMutatie
from TestHelpers import browser_helper as bh
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
import time


class TestBrowserBestellingMandjeVerwijder(MyMgmtCommandHelper, bh.BrowserTestCase):

    """ Test de Bestelling applicatie, gebruik van mandje_verwijder.js vanuit de browser """

    url_mandje = '/bestel/mandje/'
    url_webwinkel_product = '/webwinkel/product-%s/'    # webwinkelproduct.pk

    def test_mandje_verwijder(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        Bestelling.objects.all().delete()
        c1 = BestellingMutatie.objects.count()

        # leg een product in het mandje
        url = self.url_webwinkel_product % self.webwinkel_product.pk
        self.do_navigate_to(url)

        page = self.get_page_html()
        knop = self.find_element_type_with_text('button', 'Leg in mijn mandje')
        if not knop:            # pragma: no cover
            self.fail('Kan knop "Leg in mijn mandje" niet vinden')

        print('click')
        self.click_not_blocking(knop)
        # click handler JS script heeft een POST gedaan
        # de POST handler maakt een mutatie record voor de achtergrond taak
        # en wacht daarna tot 3 seconden op de achtergrondtaak
        # geeft daarna de http response ("Product is toegevoegd aan je mandje" pagina)
        # maar de URL is nog steeds die van de webwinkel

        # geef de achtergrondtaak wat tijd
        print('sleep begin')
        time.sleep(2.0)     # 1.0 is te kort!
        print('sleep klaar')

        c2 = BestellingMutatie.objects.count()
        if c1 == c2:        # pragma: no cover
            #page = self.get_page_html()
            print('geen mutatie gevonden. page:\n%s' % page)
            self.fail('geen mutatie gevonden')

        # ga naar het mandje
        self.do_navigate_to(self.url_mandje)

        leeg = self.find_element_type_with_text('p', 'Je mandje is leeg')
        if leeg:            # pragma: no cover
            self.assert_no_console_log()
            self.fail('Mandje is onverwachts leeg')

        # verwijder het product uit het mandje
        buttons = self.find_elements_buttons()
        if len(buttons) == 0:       # pragma: no cover
            page = self.get_page_html()
            self.fail('Verwijder knop niet gevonden! page:\n%s' % page)

        button = buttons[0]
        self.click_not_blocking(button)

        # geef het script wat tijd om de POST te doen --> form POST laadt de pagina opnieuw
        # geef de achtergrondtaak wat tijd om de bestelmutatie te verwerken
        time.sleep(0.5)

        # bekijk het mandje
        leeg = self.find_element_type_with_text('p', 'Je mandje is leeg')
        self.assertIsNotNone(leeg, 'Tekst "Je mandje is leeg" niet gevonden')

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
