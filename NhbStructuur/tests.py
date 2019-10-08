# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from django.core.exceptions import ValidationError
import datetime


class TestNhbStructuur(TestCase):
    """
        Test Suite voor de NhbStructuur code
    """

    def setUp(self):
        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.postcode = "1234PC"
        lid.huisnummer = "42bis"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()


    def test_rayons(self):
        self.assertEqual(NhbRayon.objects.all().count(), 4)
        rayon = NhbRayon.objects.get(pk=3)
        self.assertEqual(rayon.naam, "Rayon 3")
        self.assertEqual(rayon.geografisch_gebied, "Oost Brabant en Noord Limburg")
        self.assertIsNotNone(str(rayon))

    def test_regios(self):
        self.assertEqual(NhbRegio.objects.all().count(), 16)
        regio = NhbRegio.objects.get(pk=111)
        self.assertEqual(regio.naam, "Regio 111")
        self.assertIsNotNone(str(regio))


    def test_lid(self):
        lid = NhbLid.objects.all()[0]
        self.assertIsNotNone(str(lid))

        lid.clean_fields()      # run field validators
        lid.clean()             # run model validator

        # test: geboortejaar in de toekomst
        now = datetime.datetime.now()
        lid.geboorte_datum = datetime.date(year=now.year+1, month=now.month, day=now.day)
        with self.assertRaises(ValidationError):
            lid.clean_fields()

        # test: geboortejaar te ver in het verleden
        lid.geboorte_datum = datetime.date(year=1890, month=1, day=1)
        with self.assertRaises(ValidationError):
            lid.clean_fields()

        # test: sinds_datum (2010) te dicht op geboortejaar
        lid.geboorte_datum = datetime.date(year=2009, month=1, day=1)
        with self.assertRaises(ValidationError):
            lid.clean()

        lid.sinds_datum = datetime.date(year=2100, month=11, day=12)
        with self.assertRaises(ValidationError):
            lid.clean_fields()

    def test_vereniging(self):
        ver = NhbVereniging.objects.all()[0]
        self.assertIsNotNone(str(ver))
        ver.clean_fields()      # run validators
        ver.clean()             # run model validator

# end of file
