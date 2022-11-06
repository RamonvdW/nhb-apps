# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbRegio, NhbVereniging
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers


class TestWedstrijdenLocatie(E2EHelpers, TestCase):

    """ Tests voor de Wedstrijden applicatie, module wedstrijdlocatie """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_111
        ver.save()
        self.nhbver1 = ver

    def test_locatie(self):
        locatie = WedstrijdLocatie()
        locatie.adres = 'Hallo\ndaar'
        self.assertTrue(str(locatie) != '')

        locatie.discipline_25m1pijl = True
        locatie.discipline_outdoor = True
        locatie.discipline_indoor = True
        locatie.discipline_clout = True
        locatie.discipline_veld = True
        locatie.discipline_run = True
        locatie.discipline_3d = True
        self.assertTrue(str(locatie) != '')

        locatie.zichtbaar = False
        self.assertTrue(str(locatie) != '')

# end of file
