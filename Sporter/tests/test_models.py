# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from Account.models import Account
from BasisTypen.models import BoogType
from Geo.models import Regio
from Sporter.models import Sporter, SporterBoog, Speelsterkte
from Vereniging.models import Vereniging
import datetime


class TestSporterModels(TestCase):

    """ tests voor de Sporter applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        user = get_user_model()
        user.objects.create_user('100001', 'rdetester@gmail.not', 'wachtwoord')
        account = Account.objects.get(username='100001')
        account.save()
        self.account_100001 = account

        # maak een test vereniging
        # maak een test vereniging
        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

        # maak een sporter aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_100001)
        sporter.save()

        self.sporter1 = sporter

    def test_sporter(self):
        sporter = Sporter.objects.get(lid_nr="100001")
        self.assertIsNotNone(sporter)
        self.assertIsNotNone(str(sporter))

        sporter.clean_fields()      # run field validators
        sporter.clean()             # run model validator

        # test validate_geboorte_datum, de field-validator voor geboorte_datum

        # geboortejaar in de toekomst
        now = datetime.datetime.now()
        sporter.geboorte_datum = now  + datetime.timedelta(days=10)
        with self.assertRaises(ValidationError) as exc:
            sporter.clean_fields()
        self.assertTrue("{'geboorte_datum': ['Geboortejaar 20" in str(exc.exception))
        self.assertTrue(" is niet valide (min=1900, max=20" in str(exc.exception))

        # geboortejaar te ver in het verleden (max is 1900)
        sporter.geboorte_datum = datetime.date(year=1890, month=1, day=1)
        with self.assertRaises(ValidationError) as exc:
            sporter.clean_fields()
        self.assertTrue("{'geboorte_datum': ['Geboortejaar 1890 is niet valide (min=1900, max=20" in str(exc.exception))

        # test de clean methode op het Sporter-object
        # deze controleert dat de geboorte_datum en [lid] sinds_datum niet te dicht op elkaar liggen

        # sinds_datum (2010) te dicht op geboortejaar (moet 5 jaar tussen zitten)
        sporter.geboorte_datum = datetime.date(year=2009, month=1, day=1)
        with self.assertRaises(ValidationError) as exc:
            sporter.clean()
        self.assertEqual(str(exc.exception),
                         "{'geboorte_datum': ['datum van lidmaatschap moet minimaal 5 jaar na geboortejaar zijn']}")

        # test validate_sinds_datum, de field-validator voor sinds_datum

        # mag niet lid worden in de toekomst
        sporter.sinds_datum = datetime.date(year=now.year + 1, month=11, day=12)
        with self.assertRaises(ValidationError) as exc:
            sporter.clean_fields()
        self.assertEqual(str(exc.exception),
                         "{'sinds_datum': ['datum van lidmaatschap mag niet in de toekomst liggen']}")

        self.assertEqual(sporter.voornaam, "Ramon")
        self.assertEqual(sporter.achternaam, "de Tester")
        self.assertEqual(sporter.volledige_naam(), "Ramon de Tester")

        sporter = Sporter.objects.get(lid_nr=100001)     # geboren 1972; bereikt leeftijd 40 in 2012
        self.assertEqual(sporter.bereken_wedstrijdleeftijd_wa(2012), 40)

        self.assertTrue(sporter.lid_nr_en_volledige_naam() != '')

    def test_str(self):
        # dekking van speciale functies
        obj = Speelsterkte(
                    beschrijving='test',
                    discipline='test',
                    category='test',
                    volgorde=1,
                    datum='2001-02-03',
                    sporter=self.sporter1)
        self.assertTrue(str(obj) != '')

        obj = SporterBoog(
                    sporter=None,
                    boogtype=BoogType.objects.first())
        self.assertTrue(str(obj) != '')
        obj.sporter = self.sporter1
        self.assertTrue(str(obj) != '')


# end of file
