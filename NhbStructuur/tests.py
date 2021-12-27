# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging


class TestNhbStructuur(TestCase):

    """ tests voor de NhbStructuur applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()
        self.nhbver1 = ver

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

    def test_vereniging(self):
        ver = NhbVereniging.objects.all()[0]
        self.assertIsNotNone(str(ver))
        ver.clean_fields()      # run validators
        ver.clean()             # run model validator

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
