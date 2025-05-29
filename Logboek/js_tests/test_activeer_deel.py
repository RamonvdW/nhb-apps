# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh


class TestLogboekActiveerDeel(bh.BrowserTestCase):

    """ Test de Logboek applicatie, gebruik van activeer_deel.js vanuit de browser """

    url_logboek = '/logboek/'

    def test_logboek(self):
        # log in als sporter en wissel naar de rol Manager MH
        self.do_wissel_naar_bb()

        # ga naar het logboek (dit controleert ook dat we beheerder zijn)
        self.do_navigate_to(self.url_logboek)
        h3 = self.find_element_type_with_text('h3', 'Logboek')
        self.assertIsNotNone(h3)

        # kies een het deel Records en klik op de activeer knop
        radio = self.find_element_by_id('id_records')        # radio button voor deel 'Records'
        self.get_following_sibling(radio).click()
        self.find_element_by_id('id_activeer_knop').click()
        self.wait_until_url_not(self.url_logboek)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = self.get_console_log()
        self.assertEqual(regels, [])


# end of file
