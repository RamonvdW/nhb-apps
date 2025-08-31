# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from Competitie.models import Competitie
from GoogleDrive.models import Transactie, Token, Bestand
from GoogleDrive.storage_base import Storage, StorageError
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch
import io


class TestGoogleDriveStorageTemplate(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, module storage_template """

    def test_all(self):
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']
        storage = Storage(out, 2025, share_with_emails)

        res = storage.check_access()
        self.assertTrue(res)

        # initialisatie + bestand gevonden
        storage.maak_sheet_van_template(18, False, False, 1, 4, 'fname')

        # slechte parameter
        with self.assertRaises(StorageError) as exc:
            storage.maak_sheet_van_template(42, False, False, 1, 4, 'fname')
        self.assertEqual(str(exc.exception), "Folder '42 Indiv RK' niet gevonden")

        # bestand niet gevonden; wordt aangemaakt
        with patch.object(storage, '_vind_comp_bestand', return_value=''):
            templates = {'18 Indiv RK': '1234'}
            with patch.object(storage, '_comp2template_file_id', templates):
                storage.maak_sheet_van_template(18, False, False, 1, 4, 'fname')

        text_out = out.getvalue()
        self.assertFalse('[WARN' in text_out)
        self.assertFalse('[ERROR]' in text_out)

        out = OutputWrapper(io.StringIO())
        storage = Storage(out, 2025, share_with_emails)
        with patch.object(storage, '_list_folder', return_value={}):
            with self.assertRaises(StorageError) as exc:
                storage.maak_sheet_van_template(18, False, False, 1, 4, 'fname')
            self.assertEqual(str(exc.exception), 'Could not find all templates')

    def test_vind_top(self):
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']
        storage = Storage(out, 2025, share_with_emails)
        with patch.object(storage, '_vind_globale_folder', return_value=None):
            with self.assertRaises(StorageError) as exc:
                storage.maak_sheet_van_template(18, False, False, 1, 4, 'fname')
            self.assertEqual(str(exc.exception), "{vind_top_folder} Top folder 'top' not found")

    @staticmethod
    def _iter_vind_results(arg):
        if arg == 'templates':
            return None
        return 'ok'

    def test_vind_templates(self):
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']
        storage = Storage(out, 2025, share_with_emails)
        with patch.object(storage, '_vind_globale_folder', side_effect=self._iter_vind_results):
            with self.assertRaises(StorageError) as exc:
                storage.maak_sheet_van_template(18, False, False, 1, 3, 'fname')
            self.assertEqual(str(exc.exception), "{vind_templates_folder} Templates folder 'templates' not found")

# end of file
