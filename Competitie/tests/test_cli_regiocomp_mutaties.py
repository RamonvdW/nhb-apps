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
import io


class TestCompetitieCliRegiocompMutaties(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command regiocomp_mutaties """

    # Let op: veel test coverage komt vanuit CompLaagRegio en CompLaagRayon

    def test_basis(self):

        # maak een verzoek aan dat een crash veroorzaakt
        CompetitieMutatie(mutatie=MUTATIE_INITIEEL).save()

        self.assertEqual(0, MailQueue.objects.count())

        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue('[ERROR] Onverwachte fout tijdens' in f1.getvalue())
        self.assertEqual(1, MailQueue.objects.count())

# end of file
