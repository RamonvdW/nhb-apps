# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestLocatieEvenementLocatie(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, functie Evenement Locatie """

    def _maak_vereniging(self, ver_nr, naam, regio):
        # maak een test vereniging
        ver = Vereniging(
                    ver_nr=ver_nr,
                    naam=naam,
                    regio=regio)
        ver.save()

        return ver

    @staticmethod
    def _maak_evenement_locatie(ver):
        # maak een locatie aan
        loc = EvenementLocatie(naam='Grote Hal', adres='Grote baan\n1234XX Pijlstad', vereniging=ver)
        loc.save()
        return loc

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio = Regio.objects.get(regio_nr=101)
        self.ver = self._maak_vereniging(1000, "Noordelijke club", regio)

    def test_simpel(self):
        loc = self._maak_evenement_locatie(self.ver)

        self.assertTrue(str(loc) != '')
        self.assertEqual(loc.adres_oneliner(), 'Grote baan, 1234XX Pijlstad')

        loc.zichtbaar = False
        self.assertTrue(str(loc) != '')


# end of file
