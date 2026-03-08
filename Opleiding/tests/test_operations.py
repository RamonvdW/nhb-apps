# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management.base import OutputWrapper
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleiding.models import Opleiding, OpleidingInschrijving
from Opleiding.operations import opleiding_post_import_crm
from Sporter.models import Sporter
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


class TestOpleidingOperations(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit in operations """

    def setUp(self):
        """ initialisatie van de test case """

        now = timezone.now()
        sporter = Sporter(
                    lid_nr=100001,
                    voornaam='Thea',
                    achternaam='de Tester',
                    unaccented_naam='Thea de Tester',
                    email='normaal@test.not',
                    geboorte_datum="1970-11-15",
                    geboorteplaats='Pijlstad',
                    geslacht='V',
                    sinds_datum='2000-01-01',
                    telefoon='+123456789',
                    lid_tot_einde_jaar=now.year)
        sporter.save()

        # maak de basiscursus aan
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_begin="2024-11-01",
                        periode_einde="2024-12-01",
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True,
                        kosten_euro=10.00)
        opleiding.save()

        # maak een inschrijving aan met gelijke geboorteplaats
        OpleidingInschrijving.objects.create(
                opleiding=opleiding,
                sporter=sporter,
                aanpassing_geboorteplaats='Pijlstad')

        self.inschrijving = OpleidingInschrijving.objects.create(
                                    opleiding=opleiding,
                                    sporter=sporter,
                                    aanpassing_geboorteplaats='Bad Vizier')

    def test_taak(self):
        # 1e keer wordt de taak aangemaakt
        self.assertEqual(Taak.objects.count(), 0)
        stdout = OutputWrapper(io.StringIO())
        opleiding_post_import_crm(stdout)
        # print(stdout.getvalue())
        self.assertTrue('[INFO] Inschrijving voor opleiding met geboorteplaats die afwijkt van CRM:' in stdout.getvalue())
        self.assertTrue('[INFO] Maak taak voor Manager Opleidingen met deadline' in stdout.getvalue())
        self.assertEqual(Taak.objects.count(), 1)

        # 2e keer bestaat de taak al
        opleiding_post_import_crm(stdout)
        self.assertEqual(Taak.objects.count(), 1)

        # maak de taak verouderd
        taak = Taak.objects.first()
        taak.deadline -= datetime.timedelta(days=20)
        taak.save(update_fields=['deadline'])
        opleiding_post_import_crm(stdout)
        self.assertEqual(Taak.objects.count(), 2)

        # niets te melden
        self.inschrijving.delete()
        stdout = OutputWrapper(io.StringIO())
        opleiding_post_import_crm(stdout)
        print(stdout.getvalue())
        self.assertFalse('[INFO] Inschrijving voor opleiding met geboorteplaats die afwijkt van CRM:' in stdout.getvalue())


# end of file
