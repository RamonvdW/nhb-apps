# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.models import DataApiVereniging, DataApiLidmaatschap
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import os


CLI_IMPORT_HISTCRM = 'import_histcrm_json'

TESTFILE_NOT_EXISTING = './DataApi/does-not-exist'
TEST_KISS_PAD = './DataApi/test/'
AFMELD_DATUM = '2026-09-07'


class TestDataApiCliImportHistCrmJson(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, management commando import_histcrm_json """

    def setUp(self):
        # maak een paar testbestanden aan
        self._tmp_dir = None
        self.csv_path = ''
        self.jaar = 2020

    def tearDown(self):
        if self._tmp_dir:
            self._tmp_dir.cleanup()

    def test_histcrm(self):
        f1, f2 = self.run_management_command(CLI_IMPORT_HISTCRM,
                                             TESTFILE_NOT_EXISTING,
                                             AFMELD_DATUM)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

# end of file
