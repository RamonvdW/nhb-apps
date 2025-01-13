# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management import CommandError
from TestHelpers.e2ehelpers import E2EHelpers


class TestInstaptoetsCli(E2EHelpers, TestCase):
    """ unittests voor de Instaptoets applicatie, management command import_instaptoets """

    file_toets_1_krak = 'Instaptoets/test-files/toets_1_kapot.json'
    file_toets_1b_header = 'Instaptoets/test-files/toets_1b_foute_header.json'
    file_toets_2_vraag = 'Instaptoets/test-files/toets_2_vraag.json'
    file_toets_3a_wijzig = 'Instaptoets/test-files/toets_3a_wijzig.json'
    file_toets_3b_wijzig = 'Instaptoets/test-files/toets_3b_wijzig.json'
    file_toets_3c_wijzig = 'Instaptoets/test-files/toets_3c_wijzig.json'
    file_toets_3d_wijzig = 'Instaptoets/test-files/toets_3d_wijzig.json'
    file_toets_3e_wijzig = 'Instaptoets/test-files/toets_3e_wijzig.json'    # alle antwoorden zijn aangepast
    file_toets_3v_wijzig = 'Instaptoets/test-files/toets_3v_wijzig.json'    # kleine wijziging vraag tekst
    file_toets_3w_wijzig = 'Instaptoets/test-files/toets_3w_wijzig.json'    # grote wijziging vraag tekst
    file_toets_4_dubbel = 'Instaptoets/test-files/toets_4_dubbel.json'      # dubbele vraag

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_basis(self):
        with self.assertRaises(CommandError):
            self.run_management_command('import_instaptoets')

        f1, f2 = self.run_management_command('import_instaptoets', 'bestaat-niet')
        self.assertTrue("[ERROR] Kan bestand bestaat-niet niet lezen" in f1.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_1_krak)
        self.assertTrue("[ERROR] Probleem met het JSON formaat in bestand" in f1.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_1b_header)
        self.assertTrue("[ERROR] Kan correcte header niet vinden. Geen vragen ingelezen voor deze categorie."
                        in f1.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_2_vraag)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Aantal vragen was 0" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())
        self.assertTrue("[INFO] 1 voor de toets" in f2.getvalue())
        self.assertTrue("[INFO] 0 voor de quiz" in f2.getvalue())

        # geen wijziging
        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_2_vraag)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Aantal vragen was 1" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_3a_wijzig)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord A is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_3b_wijzig)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord B is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_3c_wijzig)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord C is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_3d_wijzig)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("antwoord D is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())
        self.assertTrue("[INFO] 0 voor de toets" in f2.getvalue())
        self.assertTrue("[INFO] 1 voor de quiz" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_3e_wijzig)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("alle antwoorden zijn aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_3v_wijzig)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("vraag is aangepast" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 1" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_3w_wijzig)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Matching ratio on pk=" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 2" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_2_vraag)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Verouderde vragen: pks=" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 3" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_4_dubbel)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Verouderde vragen: pks=" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 3" in f2.getvalue())


# end of file
