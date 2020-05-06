# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from Overig.e2ehelpers import E2EHelpers
from NhbStructuur.models import NhbVereniging, NhbRegio
from .models import maak_functie
import io


class TestAccountCLI(E2EHelpers, TestCase):
    """ unit tests voor de Functie command line interface (CLI) applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_tst = maak_functie("Test test", "x")

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = 1001
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

    def test_maak_cwz(self):
        self.assertFalse(self.account_normaal.is_staff)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_cwz', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is CWZ gemaakt van vereniging [1001] Grote Club" in f2.getvalue())

        # probeer nog een keer CWZ te maken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_cwz', 'normaal', '1001', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[WARNING] Account 'normaal' is al CWZ van vereniging [1001] Grote Club" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

# end of file
