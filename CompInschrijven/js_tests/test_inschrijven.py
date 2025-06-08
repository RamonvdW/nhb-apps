# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
import time


class TestAccountLogin(bh.BrowserTestCase):

    url_login = '/account/login/'
    url_login_as = '/account/account-wissel/'

    def test_login(self):
        # uitloggen (voor het geval we ingelogd waren)
        self.do_logout()

        # inloggen dialoog oproepen
        self.do_navigate_to(self.url_login)
        self.assertEqual(self._driver.title, 'Inloggen')

        # move_label_after_autofill draaien op timers
        # totale tijd: 1000+500+200+100+50 = 1750ms
        time.sleep(2)

        self.assert_no_console_log()

        self.find_element_by_id('id_login_naam').send_keys(self.account_bb.username)
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

    def test_login_as(self):
        # inloggen
        self.do_login()

        # wordt Manager MH
        self.do_wissel_naar_bb()

        # ga naar de login-as pagina en zoek op een van de accounts
        self.do_navigate_to(self.url_login_as + '?zoekterm=%s' % self.account.username)

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()

        # vind de knop
        i = self.find_element_type_with_text('i', 'play_arrow')
        button = self.get_parent(i)
        button.click()

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()


# end of file
