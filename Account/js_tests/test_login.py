# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
import time


class TestAccountLogin(bh.BrowserTestCase):

    url_login = '/account/login/'

    def test_login(self):
        # de support functies doen al een groot deel van de test die we willen doen

        # inloggen (voor het geval we uitgelogd waren)
        self.do_login()

        # uitloggen (voor het geval we ingelogd waren)
        self.do_logout()

        # inloggen dialoog oproepen
        self.do_navigate_to(self.url_login)
        self.assertEqual(self._driver.title, 'Inloggen')

        # move_label_after_autofill draaien op timers
        # totale tijd: 1000+500+200+100+50 = 1750ms
        time.sleep(2)

        self.assert_no_console_log()

        # capture the coverage before it gets lost due to the page load
        self.fetch_js_cov()

        self.find_element_by_id('id_login_naam').send_keys(self.account.username)
        self.find_element_by_id('id_wachtwoord').send_keys(TEST_WACHTWOORD)
        login_vink = self.find_element_by_name('aangemeld_blijven')
        self.assertTrue(login_vink.is_selected())
        # clickable = bh.get_following_sibling(login_vink)
        # login_vink.click()
        # self.assertFalse(login_vink.is_selected())
        self.find_element_by_id('submit_knop').click()

        # controleer dat we ingelogd zijn
        # self.do_navigate_to(self.url_plein)
        menu = self.find_element_type_with_text('a', 'Uitloggen')
        self.assertIsNotNone(menu)

        # zorg dat de volgende test niet in de war raakt (alternatief is weer uitloggen)
        self.session_state = "logged in"


# end of file
