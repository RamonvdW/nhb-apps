# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.core import management
from Locatie.models import Reistijd
from Mailer.models import MailQueue, mailer_opschonen
from Mailer.operations import mailer_queue_email, mailer_notify_internal_error
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


class TestLocatieCliReistijd(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, management commando's """

    def test_geen_args(self):
        f1, f2 = self.run_management_command('reistijd_bijwerken')
        print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

    def test_(self):
        # maak een reistijd verzoek
        reistijd = Reistijd(vanaf_lat='sr3_lat',
                            vanaf_lon='sr3_lon',
                            naar_lat='zelf_lat',
                            naar_lon='zelf_lon',
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        f1, f2 = self.run_management_command('reistijd_bijwerken')
        print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

# end of file
