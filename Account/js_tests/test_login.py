# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD


class TestAccountLogin(bh.BrowserTestCase):

    url_login = '/account/login/'

    def test_login(self):

        # inloggen is al gedaan in Plein/tests/test_js_in_browser voordat wij aangeroepen werden

        # log in
        # self.do_navigate_to(self.url_login)
        # self.find_element_by_id('id_login_naam').send_keys(self.account.username)
        # self.find_element_by_id('id_wachtwoord').send_keys(TEST_WACHTWOORD)
        # login_vink = self.find_element_by_name('aangemeld_blijven')
        # self.assertTrue(login_vink.is_selected())
        # # clickable = bh.get_following_sibling(login_vink)
        # # login_vink.click()
        # # self.assertFalse(login_vink.is_selected())
        # self.find_element_by_id('submit_knop').click()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = self.get_console_log()
        if len(regels):
            for regel in regels:
                print('regel: %s' % repr(regel))
        # for
        self.assertEqual(regels, [])

        self.wait_until_url_not(self.url_login)     # redirect naar /plein/

        # controleer dat we ingelogd zijn
        # self.do_navigate_to(self.url_plein)
        menu = self.find_element_type_with_text('a', 'Uitloggen')
        self.assertIsNotNone(menu)


# end of file
