# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.sessions.backends.db import SessionStore
from TestHelpers import browser_helper as bh
from Plein.views import SESSIONVAR_VORIGE_POST


class TestBrowserPleinStuurPing(bh.BrowserTestCase):

    """ Test de Plein applicatie, gebruik van stuur_ping.js vanuit de browser """

    def _check_ping(self):
        mh_session_id = self.get_browser_cookie_value('mh_session_id')
        # print('mh_session_id cookie value: %s' % mh_session_id)
        session = SessionStore(session_key=mh_session_id)
        session[SESSIONVAR_VORIGE_POST] = 'forceer'
        session.save()

        self.do_navigate_to(self.url_plein)

        html = self.get_page_html()
        has_ping = "stuur_ping" in html
        # print('has_ping: %s' % has_ping)
        # if not has_ping:
        #     print(html[:500])
        #     print(html[-500:])
        self.assertTrue(has_ping)

        # wacht even en check daarna dat de post gedaan is door de js load event handler
        # time.sleep(1)

        session = SessionStore(session_key=mh_session_id)
        stamp = session.get(SESSIONVAR_VORIGE_POST, '')
        self.assertFalse(stamp == '')

    def test_sporter(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/
        # pagina is gebaseerd op template plein-sporter.dtl

        # controleer dat we ingelogd zijn
        menu = self.find_element_type_with_text('a', 'Wissel van rol')
        self.assertIsNotNone(menu)
        menu = self.find_element_type_with_text('a', 'Mijn pagina')
        self.assertIsNotNone(menu)
        menu = self.find_element_type_with_text('a', 'Toon bondspas')
        self.assertIsNotNone(menu)
        menu = self.find_element_type_with_text('a', 'Uitloggen')
        self.assertIsNotNone(menu)

        self._check_ping()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

    def test_beheerder(self):
        self.do_wissel_naar_hwl()               # redirect naar /vereniging/
        self.do_navigate_to(self.url_plein)     # geeft pagina is plein-beheerder.dtl

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # controleer dat we beheerder zijn
        h3 = self.find_element_type_with_text('h3', 'Beheerders Plein')
        self.assertIsNotNone(h3)

        # check dat de ping gedaan is
        self._check_ping()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
