# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management import CommandError
from TestHelpers.e2ehelpers import E2EHelpers


class TestInstaptoetsCli(E2EHelpers, TestCase):
    """ unittests voor de Instaptoets applicatie, management command laad_instaptoets """

    file_vragen_1 = 'Instaptoets/test-files/vragen_1.csv'
    file_vragen_1a = 'Instaptoets/test-files/vragen_1a.csv'
    file_vragen_1b = 'Instaptoets/test-files/vragen_1b.csv'
    file_vragen_1c = 'Instaptoets/test-files/vragen_1c.csv'
    file_vragen_1d = 'Instaptoets/test-files/vragen_1d.csv'
    file_vragen_1v = 'Instaptoets/test-files/vragen_1v.csv'
    file_vragen_1w = 'Instaptoets/test-files/vragen_1w.csv'

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_basis(self):
        with self.assertRaises(CommandError):
            self.run_management_command('laad_instaptoets')

        f1, f2 = self.run_management_command('laad_instaptoets', 'bestaat-niet')
        self.assertTrue("[ERROR] Kan bestand bestaat-niet niet lezen" in f1.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Aantal vragen was 0" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Aantal vragen was 1" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1a)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord A is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1b)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord B is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1c)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord C is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1d)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord D is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("alle antwoorden zijn aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1v)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("vraag is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1w)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Matching ratio on pk=" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 2" in f2.getvalue())

        f1, f2 = self.run_management_command('laad_instaptoets', self.file_vragen_1)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Verouderde vragen: pks=" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 2" in f2.getvalue())



# end of file
