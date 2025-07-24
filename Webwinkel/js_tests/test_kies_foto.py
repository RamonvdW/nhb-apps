# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh


class TestBrowserWebwinkelKiesFoto(bh.BrowserTestCase):

    """ Test de Webwinkel applicatie, gebruik van kies_foto.js vanuit de browser """

    url_webwinkel = '/webwinkel/'
    url_webwinkel_product = '/webwinkel/product-%s/'    # webwinkelproduct.pk

    def test_kies(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/
        # pagina is gebaseerd op template plein-sporter.dtl

        # controleer dat we ingelogd zijn
        menu = self.find_element_type_with_text('a', 'Mijn pagina')
        self.assertIsNotNone(menu)
        menu = self.find_element_type_with_text('a', 'Uitloggen')
        self.assertIsNotNone(menu)

        # ga naar de webwinkel
        url = self.url_webwinkel_product % self.webwinkel_product.pk
        self.do_navigate_to(url)

        # klik op de volgende thumbnail
        thumb = self.find_element_by_id('id_thumb_2')
        thumb.click()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

# end of file
