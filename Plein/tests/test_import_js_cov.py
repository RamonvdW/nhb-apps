# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, tag
from TestHelpers import browser_helper as bh


@tag("browser")     # deze tag voorkomt het uitvoeren van deze test tijden de main test run
class TestPleinImportJsCov(TestCase):

    """ Importeer de coverage van de Javascript bestanden. """

    def import_js_cov(self):
        res = bh.js_cov_import()
        self.assertEqual(res, 1)


# end of file
