# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch


class TestGraphDriveCliDownload(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, management command graph_download """

    cli_download = 'graph_download'

    bad_metadata = {'hi': 'test'}
    good_metadata = {'@microsoft.graph.downloadUrl': 'whatever'}

    def setUp(self):
        self.mock_metadata_none = patch('GraphDrive.management.commands.graph_download.get_file_metadata', return_value=None)
        self.mock_metadata_bad = patch('GraphDrive.management.commands.graph_download.get_file_metadata', return_value=self.bad_metadata)
        self.mock_metadata_good = patch('GraphDrive.management.commands.graph_download.get_file_metadata', return_value=self.good_metadata)

        self.mock_download_none = patch('GraphDrive.management.commands.graph_download.download', return_value=None)
        self.mock_download_good = patch('GraphDrive.management.commands.graph_download.download', return_value='/tmp/local')

    def test_download(self):
        self.mock_metadata_none.start()

        f1, f2 = self.run_management_command(self.cli_download, '/remote/does/not/exist/missing.txt', '/tmp/local')
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())

        self.mock_metadata_none.stop()

        self.mock_metadata_bad.start()
        f1, f2 = self.run_management_command(self.cli_download, '/remote/does/not/exist/missing.txt', '/tmp/local')
        self.assertEqual(f1.getvalue(), '')
        self.mock_metadata_bad.stop()

        self.mock_metadata_good.start()

        self.mock_download_none.start()
        f1, f2 = self.run_management_command(self.cli_download, '/remote/does/not/exist/missing.txt', '/tmp/local')
        self.assertEqual(f1.getvalue(), '')
        self.mock_download_none.stop()

        self.mock_download_good.start()
        f1, f2 = self.run_management_command(self.cli_download, '/remote/does/not/exist/missing.txt', '/tmp/local')
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.assertTrue("[INFO] Download gelukt naar '/tmp/local'" in f2.getvalue())
        self.mock_download_good.stop()

        self.mock_metadata_good.stop()

# end of file
