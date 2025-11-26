# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh


class TestBrowserFunctieWisselNaarRol(bh.BrowserTestCase):

    url_wissel_van_rol = '/functie/wissel-van-rol/'

    def test_wissel(self):
        self.do_wissel_naar_bb()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
