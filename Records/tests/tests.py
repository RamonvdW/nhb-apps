# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from Records.definities import LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Records.models import IndivRecord
from Sporter.models import Sporter


class TestRecordsRest(TestCase):
    """ unittests voor de Records applicatie """

    def setUp(self):
        """ initialisatie van de test case """

        # NhbLib
        sporter = Sporter(
                    lid_nr=123457,
                    voornaam='Petra',
                    achternaam='Schutter',
                    email='petra@test.nl',
                    geboorte_datum=parse_date('1970-01-30'),
                    adres_code='Arnhem',
                    geslacht='V',
                    sinds_datum=parse_date("1991-02-05"))  # Y-M-D
        sporter.save()

        # Record 42
        rec = IndivRecord(
                    volg_nr=42,
                    discipline=DISCIPLINE[0][0],   # OD
                    soort_record='Test record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    sporter=sporter,
                    naam='Top Schutter',
                    datum=parse_date('2017-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    score=1234,
                    max_score=5678,
                    x_count=56)
        rec.save()

    def test_create(self):
        rec = IndivRecord.objects.first()
        rec.clean_fields()      # run field validators
        rec.clean()             # run model validator
        self.assertIsNotNone(str(rec))      # use the __str__ method (only used by admin interface)


# end of file
