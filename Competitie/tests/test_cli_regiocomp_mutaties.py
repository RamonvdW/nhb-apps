# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from Competitie.definities import MUTATIE_INITIEEL
from Competitie.models import CompetitieMutatie
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import time
import io


class TestCompetitieCliRegiocompMutaties(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command regiocomp_mutaties """

    # Let op: veel test coverage komt vanuit CompLaagRegio en CompLaagRayon

    def test_basis(self):

        # maak een verzoek aan dat een crash veroorzaakt
        CompetitieMutatie(mutatie=MUTATIE_INITIEEL).save()

        self.assertEqual(0, MailQueue.objects.count())

        # vraag de achtergrondtaak om de mutaties te verwerken
        f1, f2 = self.run_management_command('regiocomp_mutaties', '1', '--quick')

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue('[ERROR] Onverwachte fout tijdens' in f1.getvalue())
        self.assertEqual(1, MailQueue.objects.count())

    def test_stop_exactly(self):
        now = datetime.datetime.now()
        if now.minute == 0:
            print('Waiting until clock is past xx:00')
            while now.minute == 0:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        now = datetime.datetime.now()
        if now.second > 55:
            print('Waiting until clock is past xx:xx:59')
            while now.second > 55:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the current minute
        f1, f2 = self.run_management_command('regiocomp_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % now.minute)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # trigger the negative case
        f1, f2 = self.run_management_command('regiocomp_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute - 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        now = datetime.datetime.now()
        if now.minute == 59:
            print('Waiting until clock is past xx:59')
            while now.minute == 59:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the positive case
        f1, f2 = self.run_management_command('regiocomp_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute + 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

# end of file
