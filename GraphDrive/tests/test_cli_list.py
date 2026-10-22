# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch


class TestGraphDriveCliList(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, management command graph_list """

    cli_list = 'graph_list'

    def setUp(self):
        pass

    def test_list(self):
        site_index = 1
        remote_folder = '/'
        dir_lijst = ['dir_naam']
        file_lijst = [('last_mod', 'size', 'naam', None),]

        with patch('GraphDrive.management.commands.graph_list.list_folders_and_files', return_value=(dir_lijst, file_lijst)):
            f1, f2 = self.run_management_command(self.cli_list, site_index, remote_folder)
            self.assertEqual(f1.getvalue(), '')
            # print('f2:', f2.getvalue())
            self.assertTrue("""modified                    size name
--------------------- ---------- --------------------------------------------------
(folder)                         dir_naam
last_mod                    size naam""" in f2.getvalue())
            self.assertFalse('[WARNING]' in f2.getvalue())
            self.assertFalse('[ERROR]' in f2.getvalue())

        f1, f2 = self.run_management_command(self.cli_list, 9999, remote_folder)
        self.assertEqual(f1.getvalue(), '')
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Kan site index 9999 niet vinden in GRAPH_IDS" in f2.getvalue())


# end of file
