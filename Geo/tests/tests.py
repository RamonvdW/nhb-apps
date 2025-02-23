# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Geo.admin import RayonAdmin, RegioAdmin
from Geo.models import Rayon, Regio, Cluster
from Vereniging.models import Vereniging


class TestGeo(TestCase):

    """ tests voor de Geo applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

    def test_rayons(self):
        self.assertEqual(Rayon.objects.count(), 4)
        rayon = Rayon.objects.get(pk=3)
        self.assertEqual(rayon.naam, "Rayon 3")
        self.assertIsNotNone(str(rayon))

    def test_regios(self):
        self.assertEqual(Regio.objects.count(), 17)
        regio = Regio.objects.get(pk=111)
        self.assertEqual(regio.naam, "Regio 111")
        self.assertIsNotNone(str(regio))

    def test_admin(self):
        request = self.client

        admin = RayonAdmin(Rayon, None)
        self.assertFalse(admin.has_change_permission(request))
        self.assertFalse(admin.has_add_permission(request))
        self.assertFalse(admin.has_delete_permission(request))

        admin = RegioAdmin(Regio, None)
        self.assertFalse(admin.has_change_permission(request))
        self.assertFalse(admin.has_add_permission(request))
        self.assertFalse(admin.has_delete_permission(request))

    def test_cluster(self):
        ver = self.ver1

        # maak een cluster aan
        cluster = Cluster()
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
