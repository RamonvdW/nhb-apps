# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch
from tempfile import NamedTemporaryFile


class TestGraphDriveCliUpload(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, management command graph_upload """

    cli_upload = 'graph_upload'

    def setUp(self):
        pass

    def test_upload(self):
        site_index = 1
        remote_folder = '/remote/does/not/exist'

        f1, f2 = self.run_management_command(self.cli_upload, site_index, '/does/not/exist', remote_folder)
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.assertTrue('[ERROR] Kan lokaal bestand niet vinden:' in f2.getvalue())

        remote_folder += '/'
        local_file = NamedTemporaryFile()       # creates zero-byte file, which is enough

        with patch('GraphDrive.management.commands.graph_upload.upload_file', return_value=None):
            f1, f2 = self.run_management_command(self.cli_upload, site_index, local_file.name, remote_folder)
            self.assertEqual(f1.getvalue(), '')
            # print('f2:', f2.getvalue())
            self.assertTrue('[INFO] Done' in f2.getvalue())
            self.assertFalse('[WARNING]' in f2.getvalue())
            self.assertFalse('[ERROR]' in f2.getvalue())

        f1, f2 = self.run_management_command(self.cli_upload, 9999, local_file.name, remote_folder)
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan site index 9999 niet vinden in GRAPH_IDS" in f2.getvalue())


# end of file
