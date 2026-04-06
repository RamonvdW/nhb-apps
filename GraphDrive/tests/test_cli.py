# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch


class TestGraphDriveCli(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, management commands """

    cli_metadata = 'graph_metadata'

    def test_basis(self):
        d = {'hi': 'test'}
        with patch('GraphDrive.operations.get_file_metadata', return_value=d):
            f1, f2 = self.run_management_command(self.cli_metadata, '/remote/does/not/exist/missing.txt')
            # print('\nf1:', f1.getvalue())
            # print('f2:', f2.getvalue())

# end of file
