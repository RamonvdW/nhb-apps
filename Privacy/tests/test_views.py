# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers


class TestPrivacyViews(E2EHelpers, TestCase):

    """ tests voor de Privacy-applicatie, views """

    url_overzicht = '/privacy/'
    url_verklaring = '/privacy/verklaring/'

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_overzicht(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('privacy/overzicht.dtl', 'design/site_layout.dtl'))
            self.assert_html_ok(resp)

    def test_verklaring(self):
        # let op: deze test met de echte verklaring
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verklaring)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('privacy/verklaring.dtl',))
            self.assert_html_ok(resp)


# end of file
