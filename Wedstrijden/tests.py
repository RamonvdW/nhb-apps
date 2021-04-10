# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Overig.e2ehelpers import E2EHelpers
from NhbStructuur.models import NhbRegio, NhbVereniging
from .models import CompetitieWedstrijd, WedstrijdLocatie, CompetitieWedstrijdUitslag
import datetime


class TestWedstrijden(E2EHelpers, TestCase):

    """ Tests voor de Wedstrijden applicatie """

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
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

    def test_wedstrijd(self):
        wedstrijd = CompetitieWedstrijd()
        wedstrijd.datum_wanneer = datetime.date(year=2020, month=9, day=10)
        wedstrijd.tijd_begin_aanmelden = datetime.time(hour=13, minute=59, second=59)
        wedstrijd.tijd_begin_wedstrijd = wedstrijd.tijd_begin_aanmelden
        wedstrijd.tijd_einde_wedstrijd = wedstrijd.tijd_begin_aanmelden
        self.assertTrue(str(wedstrijd) != '')

        wedstrijd.vereniging = self.nhbver1
        self.assertTrue(str(wedstrijd) != '')

    def test_locatie(self):
        locatie = WedstrijdLocatie()
        locatie.adres = 'Hallo\ndaar'
        self.assertTrue(str(locatie) != '')

        locatie.discipline_outdoor = True
        locatie.discipline_indoor = True
        locatie.discipline_clout = True
        locatie.discipline_veld = True
        locatie.discipline_run = True
        locatie.discipline_3d = True
        self.assertTrue(str(locatie) != '')

        locatie.zichtbaar = False
        self.assertTrue(str(locatie) != '')

    def test_uitslag(self):
        uitslag = CompetitieWedstrijdUitslag(max_score=123, afstand_meter=45)
        self.assertTrue(str(uitslag) != '')
        uitslag.is_bevroren = True
        self.assertTrue(str(uitslag) != '')


# end of file
