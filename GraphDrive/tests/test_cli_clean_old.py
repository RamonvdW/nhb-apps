# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch


class TestGraphDriveCliCleanOld(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, management command graph_clean_old """

    cli_clean_old = 'graph_clean_old'

    list_results = (None, [(None, None, 'file1', 'item1'), (None, None, 'file2', 'item2')])

    def setUp(self):
        self.mock_list = patch('GraphDrive.management.commands.graph_clean_old.list_folders_and_files',
                                        return_value=self.list_results)
        self.mock_delete = patch('GraphDrive.management.commands.graph_clean_old.delete_item', return_value=None)

    def test_clean_old(self):
        site_index = 1
        limiet = 100
        folder = '/'

        self.mock_list.start()
        self.mock_delete.start()

        f1, f2 = self.run_management_command(self.cli_clean_old, site_index, folder, limiet)
        self.assertEqual(f1.getvalue(), '')
        #print('f2:', f2.getvalue())
        self.assertTrue('[INFO] Niets te verwijderen (er zijn 2 bestanden)' in f2.getvalue())

        limiet = 1
        f1, f2 = self.run_management_command(self.cli_clean_old, site_index, folder, limiet)
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.assertTrue('[INFO] Verwijder oudste bestand: file1' in f2.getvalue())

        self.mock_delete.stop()
        self.mock_list.stop()

        f1, f2 = self.run_management_command(self.cli_clean_old, 9999, folder, limiet)
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan site index 9999 niet vinden in GRAPH_IDS" in f2.getvalue())


# end of file
