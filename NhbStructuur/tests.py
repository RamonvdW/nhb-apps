# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Account.models import Account
import datetime
from dateutil.relativedelta import relativedelta


class TestNhbStructuur(TestCase):
    """ unit tests voor de NhbStructuur applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('100001', 'rdetester@gmail.not', 'wachtwoord')
        account = Account.objects.get(username='100001')
        account.save()
        self.account_100001 = account

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()
        self.nhbver1 = ver

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_100001
        lid.save()

    def test_rayons(self):
        self.assertEqual(NhbRayon.objects.count(), 4)
        rayon = NhbRayon.objects.get(pk=3)
        self.assertEqual(rayon.naam, "Rayon 3")
        self.assertIsNotNone(str(rayon))

    def test_regios(self):
        self.assertEqual(NhbRegio.objects.count(), 17)
        regio = NhbRegio.objects.get(pk=111)
        self.assertEqual(regio.naam, "Regio 111")
        self.assertIsNotNone(str(regio))

    def test_lid(self):
        lid = NhbLid.objects.get(nhb_nr="100001")
        self.assertIsNotNone(lid)
        self.assertIsNotNone(str(lid))

        lid.clean_fields()      # run field validators
        lid.clean()             # run model validator

        # test: geboortejaar in de toekomst
        now = datetime.datetime.now()
        lid.geboorte_datum = now - relativedelta(years=1)   # avoid leap-year issue
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

        self.assertEqual(lid.voornaam, "Ramon")
        self.assertEqual(lid.achternaam, "de Tester")
        self.assertEqual(lid.volledige_naam(), "Ramon de Tester")

    def test_vereniging(self):
        ver = NhbVereniging.objects.all()[0]
        self.assertIsNotNone(str(ver))
        ver.clean_fields()      # run validators
        ver.clean()             # run model validator

    def test_bereken_wedstrijdleeftijd(self):
        lid = NhbLid.objects.get(nhb_nr=100001)     # geboren 1972; bereikt leeftijd 40 in 2012
        self.assertEqual(lid.bereken_wedstrijdleeftijd(2012), 40)

    def test_cluster(self):
        ver = self.nhbver1

        # maak een cluster aan
        cluster = NhbCluster()
        cluster.regio = ver.regio
        cluster.letter = 'Z'        # mag niet overeen komen met standaard clusters
        cluster.gebruik = '18'
        cluster.naam = "Testje"
        cluster.save()
        self.assertEqual(str(cluster), '111Z voor Indoor (Testje)')

        # stop the vereniging in het cluster
        ver.clusters.add(cluster)

        # naam is optioneel
        cluster.naam = ""
        self.assertEqual(str(cluster), '111Z voor Indoor')


# end of file
