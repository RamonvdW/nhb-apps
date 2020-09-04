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

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_tst = maak_functie("Test test", "x")

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = 1001
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

    def test_maak_hwl(self):
        self.assertFalse(self.account_normaal.is_staff)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_hwl', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is HWL gemaakt van vereniging [1001] Grote Club" in f2.getvalue())

        # probeer nog een keer HWL te maken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_hwl', 'normaal', '1001', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[WARNING] Account 'normaal' is al HWL van vereniging [1001] Grote Club" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_bad_account(self):
        # niet bestaand account
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_hwl', 'abnormaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue("Account matching query does not exist" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_bad_vereniging(self):
        # niet bestaande vereniging
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_hwl', 'normaal', '9999', stderr=f1, stdout=f2)
        self.assertTrue("NhbVereniging matching query does not exist" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_bad_functie(self):
        # niet bestaande functie
        self.functie_hwl.delete()
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_hwl', 'normaal', '1001', stderr=f1, stdout=f2)
        self.assertTrue("Functie matching query does not exist" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_maak_rcl(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_rcl', 'normaal', '18', '101', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Account 'normaal' is nu RCL Regio 101 Indoor" in f2.getvalue())

        # probeer nog een keer RCL te maken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_rcl', 'normaal', '18', '101', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[WARNING] Account 'normaal' is al RCL Regio 101 Indoor" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

    def test_maak_rcl_bad(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('maak_rcl', 'bestaatniet', '18', '000', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        print('f2:', f2.getvalue())
        self.assertTrue("Account matching query does not exist" in f1.getvalue())
        self.assertTrue("Functie matching query does not exist" in f1.getvalue())
        self.assertTrue(f2.getvalue() == '')

# end of file
