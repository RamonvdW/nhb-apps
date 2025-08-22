# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Registreer import admin
from Registreer.models import GastRegistratie
from TestHelpers.e2ehelpers import E2EHelpers


class TestRegistreerAdmin(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, Admin interface """

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        pass

    def test_filters(self):
        # GastRegistratieFaseFilter
        worker = admin.GastRegistratieFaseFilter(None,
                                                 {'fase_filter': None},
                                                 GastRegistratie,
                                                 admin.GastRegistratieAdmin)
        _ = worker.queryset(None, GastRegistratie.objects.all())

        worker = (admin.GastRegistratieFaseFilter(None,
                                                  {'fase_filter': 99},
                                                  GastRegistratie,
                                                  admin.GastRegistratieAdmin))
        _ = worker.queryset(None, GastRegistratie.objects.all())


# end of file
