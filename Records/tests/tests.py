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
        sporter = Sporter()
        sporter.lid_nr = 123457
        sporter.voornaam = 'Petra'
        sporter.achternaam = 'Schutter'
        sporter.email = 'petra@test.nl'
        sporter.geboorte_datum = parse_date('1970-01-30')
        sporter.woon_straatnaam = 'Arnhem'
        sporter.geslacht = 'V'
        sporter.sinds_datum = parse_date("1991-02-05")  # Y-M-D
        sporter.save()

        # Record 42
        rec = IndivRecord()
        rec.volg_nr = 42
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Test record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = MATERIAALKLASSE[0][0]     # R
        rec.sporter = sporter
        rec.naam = 'Top Schutter'
        rec.datum = parse_date('2017-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 1234
        rec.max_score = 5678
        rec.x_count = 56
        rec.save()

    def test_create(self):
        rec = IndivRecord.objects.all()[0]
        rec.clean_fields()      # run field validators
        rec.clean()             # run model validator
        self.assertIsNotNone(str(rec))      # use the __str__ method (only used by admin interface)


# end of file
