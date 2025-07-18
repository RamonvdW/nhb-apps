# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management import CommandError
from Geo.models import Regio
from Instaptoets.models import Instaptoets
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


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
    file_toets_5_deel = 'Instaptoets/test-files/toets_5_deel.json'          # deel van antwoorden ontbreekt

    def setUp(self):
        """ initialisatie van de test case """
        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=102),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver.save()

        self.lid_nr = 100000
        sporter = Sporter(
                        lid_nr=self.lid_nr,
                        voornaam='Jan',
                        achternaam='van de Toets',
                        geboorte_datum='1977-07-07',
                        sinds_datum='2024-02-02',
                        account=None,
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        self.sporter_100000 = sporter

    def test_basis(self):
        f1, f2 = self.run_management_command('import_instaptoets',
                                             report_exit_code=False)
        # print('\nf1:', f1.getvalue())
        self.assertTrue("raised CommandError('Error: the following arguments are required: filename" in f1.getvalue())

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
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("[INFO] Verouderde vragen: pks=" in f2.getvalue())
        self.assertTrue("[INFO] Aantal vragen is nu 3" in f2.getvalue())

        f1, f2 = self.run_management_command('import_instaptoets', self.file_toets_5_deel)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('[WARNING] Incomplete vraag wordt overgeslagen' in f2.getvalue())

    def test_fake(self):
        f1, f2 = self.run_management_command('fake_instaptoets_gehaald', 'NaN', '2000-01-01',
                                             report_exit_code=False)
        # print('\nf1:', f1.getvalue())
        self.assertTrue(' raised CommandError("Error: argument bondsnummer: invalid int value' in f1.getvalue())

        f1, f2 = self.run_management_command('fake_instaptoets_gehaald', 1234, '1234')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] '1234' is geen valide datum. Moet voldoen aan YYYY-MM-DD" in f1.getvalue())
        self.assertTrue("[ERROR] Sporter met bondsnummer 1234 niet gevonden" in f1.getvalue())

        # foute datum
        f1, f2 = self.run_management_command('fake_instaptoets_gehaald', self.lid_nr, '2000-01-01')
        self.assertTrue("[ERROR] Datum moet in de afgelopen 365 dagen liggen" in f1.getvalue())

        self.assertEqual(Instaptoets.objects.count(), 0)
        datum_str = (timezone.now() - datetime.timedelta(days=40)).date().strftime("%Y-%m-%d")
        f1, f2 = self.run_management_command('fake_instaptoets_gehaald', self.lid_nr, datum_str)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()
        self.assertTrue(toets.is_afgerond)
        self.assertTrue(toets.geslaagd)


# end of file
