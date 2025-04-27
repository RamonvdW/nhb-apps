# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Locatie.models import Reistijd
from Locatie.operations.reistijd_bepalen import TEST_TRIGGER
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers


class TestLocatieCliReistijd(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, management commando's """

    def setUp(self):
        pass

    def test_basic(self):
        # niets te doen
        f1, f2 = self.run_management_command('reistijd_bijwerken')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')

        with override_settings(GMAPS_KEY='garbage'):
            f1, f2 = self.run_management_command('reistijd_bijwerken')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[ERROR] Fout tijdens gmaps init: Invalid API key provided' in f1.getvalue())

        # unexpected exception handling
        Reistijd(
            vanaf_lat=TEST_TRIGGER,
            vanaf_lon=TEST_TRIGGER,
            naar_lat=TEST_TRIGGER,
            naar_lon=TEST_TRIGGER,
        ).save()

        f1, f2 = self.run_management_command('reistijd_bijwerken', report_exit_code=False)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[ERROR] Onverwachte fout' in f1.getvalue())
        self.assertTrue('Traceback:' in f1.getvalue())
        self.assertTrue('[WARNING] Stuur crash mail naar ontwikkelaar' in f2.getvalue())
        self.assertEqual(MailQueue.objects.count(), 1)


# end of file
