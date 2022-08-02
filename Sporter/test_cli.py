# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from .models import Sporter
from NhbStructuur.models import NhbVereniging, NhbRegio
from Sporter.models import SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import io


class TestSporterCli(E2EHelpers, TestCase):
    """ unittests voor de Sporter applicatie, management commando's """

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters(ook_ifaa_bogen=True)

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_dev_koppel_sporter(self):
        lid_nr = 123456

        # niet bestaand account
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('dev_koppel_sporter', 'niet_bestaand_account', stderr=f1, stdout=f2)
        self.assertTrue("Geen account met username 'niet_bestaand_account' gevonden" in f1.getvalue())

        # username is geen nummer (lid_nr is een nummer)
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('dev_koppel_sporter', self.testdata.account_admin.username, stderr=f1, stdout=f2)
        self.assertTrue("Geen sporter met lid_nr 'admin' gevonden" in f1.getvalue())

        # corrigeer de username
        self.testdata.account_admin.username = str(lid_nr)
        self.testdata.account_admin.save(update_fields=['username'])
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('dev_koppel_sporter', self.testdata.account_admin.username, stderr=f1, stdout=f2)
        self.assertTrue("Geen sporter met lid_nr '123456' gevonden" in f1.getvalue())

        # maak de sporter aan
        Sporter(
            lid_nr=lid_nr,
            voornaam='Tester',
            achternaam='de Test',
            unaccented_naam='Tester de Test',
            email='test@sporters.not',
            geboorte_datum='1972-01-01',
            geslacht='M',
            is_actief_lid=True,
            sinds_datum='2000-01-01',
            bij_vereniging=None,
            lid_tot_einde_jaar=2019,
            account=None).save()

        sporter = Sporter.objects.get(lid_nr=lid_nr)
        self.assertIsNone(sporter.account)

        self.testdata.account_admin.username = '123456'
        self.testdata.account_admin.save(update_fields=['username'])
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('dev_koppel_sporter', self.testdata.account_admin.username, stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("Account '123456' gekoppeld aan bijbehorende sporter" in f2.getvalue())

        sporter = Sporter.objects.get(lid_nr=lid_nr)
        self.assertIsNotNone(sporter.account)

    def test_dev_koppel_ver(self):
        # niet bestaande vereniging
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('dev_koppel_ver', '999999', '999999', stderr=f1, stdout=f2)
        self.assertTrue("Vereniging '999999' niet gevonden" in f1.getvalue())

        # maak een test vereniging
        ver_nr = 1000
        self.regio_111 = NhbRegio.objects.get(regio_nr=111)
        ver = NhbVereniging(
                    ver_nr=ver_nr,
                    naam="Grote Club",
                    # secretaris kan nog niet ingevuld worden
                    regio=self.regio_111)
        ver.save()

        # niet bestaande sporter
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('dev_koppel_ver', '999999', ver_nr, stderr=f1, stdout=f2)
        self.assertTrue("Sporter met lid_nr '999999' niet gevonden" in f1.getvalue())

        # maak de sporter aan
        lid_nr = 345678
        Sporter(
            lid_nr=lid_nr,
            voornaam='Tester',
            achternaam='de Test',
            unaccented_naam='Tester de Test',
            email='test@sporters.not',
            geboorte_datum='1972-01-01',
            geslacht='M',
            is_actief_lid=False,
            sinds_datum='2000-01-01',
            bij_vereniging=None,
            lid_tot_einde_jaar=2019,
            account=None).save()

        # koppel de twee
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('dev_koppel_ver', lid_nr, ver_nr, stderr=f1, stdout=f2)
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue("Sporter 345678 gekoppeld aan vereniging 1000" in f2.getvalue())

        sporter = Sporter.objects.get(lid_nr=lid_nr)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.bij_vereniging.ver_nr, ver_nr)

    def test_keuzes_bogen(self):
        f1, f2 = self.run_management_command('keuzes_bogen')
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('met boog voorkeuren' in f2.getvalue())

# end of file
