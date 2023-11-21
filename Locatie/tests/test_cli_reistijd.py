# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from BasisTypen.definities import SCHEIDS_BOND
from Locatie.models import Reistijd
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.mgmt_cmds_helper import TEST_GMAPS_API


class TestLocatieCliReistijd(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, management commando's """

    def setUp(self):
        scheids = Sporter(
                lid_nr=123456,
                voornaam='Scheids',
                achternaam='den Urste',
                unaccented_naam='Scheids den Urste',
                email='scheids@test.not',
                geboorte_datum='2000-01-01',
                geslacht='M',
                sinds_datum='2000-01-01',
                postadres_1='Spanboog 5',
                postadres_2='1234AB Pijlstad',
                postadres_3='',
                adres_code='1234AB',
                scheids=SCHEIDS_BOND)
        scheids.save()
        self.scheids = scheids

    def test_cli(self):
        # niets te doen
        with override_settings(GMAPS_API=TEST_GMAPS_API):
            f1, f2 = self.run_management_command('reistijd_bijwerken')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')

        # maak een reistijd verzoek
        reistijd = Reistijd(vanaf_lat='sr3_lat',
                            vanaf_lon='sr3_lon',
                            naar_lat='zelf_lat',
                            naar_lon='zelf_lon',
                            reistijd_min=0)         # 0 = nog niet uitgerekend
        reistijd.save()

        with override_settings(GMAPS_API=TEST_GMAPS_API):
            f1, f2 = self.run_management_command('reistijd_bijwerken')
        print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Duration '17 mins' is 1030 seconds is 17 minutes" in f2.getvalue())

        scheids = Sporter.objects.get(lid_nr=self.scheids.lid_nr)
        self.assertEqual(scheids.adres_lat, '42.000000')
        self.assertEqual(scheids.adres_lon, '5.123000')

        reistijd = Reistijd.objects.get(pk=reistijd.pk)
        self.assertEqual(reistijd.reistijd_min, 17)


# end of file
