# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch


class TestGraphDriveCliMetadata(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, management commands """

    cli_metadata = 'graph_metadata'

    bad_metadata = {'hi': 'test'}

    def setUp(self):
        self.mock_metadata_none = patch('GraphDrive.management.commands.graph_metadata.get_file_metadata', return_value=None)
        self.mock_metadata_bad = patch('GraphDrive.management.commands.graph_metadata.get_file_metadata', return_value=self.bad_metadata)

    def test_metadata(self):
        self.mock_metadata_none.start()
        f1, f2 = self.run_management_command(self.cli_metadata, '/remote/does/not/exist/missing.txt')
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.assertTrue('[ERROR] No data' in f2.getvalue())
        self.mock_metadata_none.stop()

        self.mock_metadata_bad.start()
        f1, f2 = self.run_management_command(self.cli_metadata, '/remote/does/not/exist/missing.txt')
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.mock_metadata_bad.stop()


# end of file
