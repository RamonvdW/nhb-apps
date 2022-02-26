# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from Overig.background_sync import BackgroundSync


class TestOverigBackgroundSync(TestCase):

    """ unit tests voor de Overig applicatie, module Background Sync """

    def test(self):
        sync = BackgroundSync(settings.BACKGROUND_SYNC_POORT)

        got_ping = sync.wait_for_ping(timeout=0.01)
        self.assertFalse(got_ping)

        sync.ping()

        got_ping = sync.wait_for_ping(timeout=0.01)
        self.assertTrue(got_ping)

# end of file
