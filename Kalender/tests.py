# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers


class TestKalender(E2EHelpers, TestCase):
    """ unit tests voor de Kalender applicatie """

    def setUp(self):
        """ initialisatie van de test case """

        self.url_kalender = '/kalender/'

    def test_view(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender)


# end of file
