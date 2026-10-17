# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.models import DataApiVereniging, DataApiLidmaatschap
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import json
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

    def tearDown(self):
        self._tmp_dir.cleanup()

    def test_histcrm(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        json_path = self._tmp_dir.name

        json_fname = os.path.join(json_path, 'test.json')
        d = {
            # top-level sleutel ontbreekt
        }
        with open(json_fname, "w", encoding='utf-8') as f:
            json.dump(d, f)

        f1, f2 = self.run_management_command(CLI_IMPORT_HISTCRM,
                                             json_fname,
                                             AFMELD_DATUM,
                                             '--dryrun',
                                             '--alleen_verenigingen',
                                             report_exit_code=False)
        self.assertTrue('[TEST] Management command raised SystemExit(2)' in f1.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'rayons' niet aanwezig" in f2.getvalue())

        d = {
            'rayons': [],       # geen data voor top-level sleutel
            'regions': [],
            'clubs': [],
            'members': [],
            'extra': []
        }
        with open(json_fname, "w", encoding='utf-8') as f:
            json.dump(d, f)

        f1, f2 = self.run_management_command(CLI_IMPORT_HISTCRM,
                                             json_fname,
                                             AFMELD_DATUM,
                                             '--dryrun')
        print(f2.getvalue())
        self.assertTrue("[ERROR] Geen data voor top-level sleutel 'rayons'" in f2.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de" in f2.getvalue())

        d = {
            'rayons': [True],
            'regions': [True],
            'clubs': [{'hi': True}],
            'members': [{'hi': True}]
        }
        with open(json_fname, "w", encoding='utf-8') as f:
            json.dump(d, f)

        f1, f2 = self.run_management_command(CLI_IMPORT_HISTCRM,
                                             json_fname,
                                             AFMELD_DATUM,
                                             '--dryrun',
                                             '--alleen_verenigingen')

        f1, f2 = self.run_management_command(CLI_IMPORT_HISTCRM,
                                             json_fname,
                                             AFMELD_DATUM)
        self.assertEqual(f1.getvalue(), '')

        f1, f2 = self.run_management_command(CLI_IMPORT_HISTCRM,
                                             TESTFILE_NOT_EXISTING,
                                             AFMELD_DATUM)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue('[ERROR] Bestand kan niet gelezen worden' in f2.getvalue())

# end of file
