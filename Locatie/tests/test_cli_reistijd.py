# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.mgmt_cmds_helper import TEST_GMAPS_API_URL


class TestLocatieCliReistijd(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, management commando's """

    def setUp(self):
        pass

    def test_basic(self):
        # niets te doen
        with override_settings(GMAPS_API_URL=TEST_GMAPS_API_URL):
            f1, f2 = self.run_management_command('reistijd_bijwerken')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')

        with override_settings(GMAPS_API_URL=TEST_GMAPS_API_URL, GMAPS_KEY='garbage'):
            f1, f2 = self.run_management_command('reistijd_bijwerken')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[ERROR] Fout tijdens gmaps init: Invalid API key provided' in f1.getvalue())


# end of file
