# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.exceptions import ObjectDoesNotExist
from BasisTypen.models import BoogType
from Functie.models import Functie
from Geo.models import Regio
from Locatie.definities import BAAN_TYPE_BUITEN
from Locatie.models import WedstrijdLocatie
from Mailer.models import MailQueue
from Opleidingen.models import OpleidingDiploma
from Records.models import IndivRecord
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging, Secretaris
import datetime
import io


IMPORT_COMMAND = 'import_crm_json'
OPTION_DRY_RUN = '--dryrun'
OPTION_SIM = '--sim_now=2020-07-01'

TESTFILES_PATH = './ImportCRM/test-files/'

TESTFILE_NOT_EXISTING = TESTFILES_PATH + 'notexisting.json'
TESTFILE_01_EMPTY = TESTFILES_PATH + 'testfile_01.json'
TESTFILE_02_INCOMPLETE = TESTFILES_PATH + 'testfile_02.json'
TESTFILE_03_BASE_DATA = TESTFILES_PATH + 'testfile_03.json'
TESTFILE_04_UNICODE_ERROR = TESTFILES_PATH + 'testfile_04.json'
TESTFILE_05_MISSING_KEYS = TESTFILES_PATH + 'testfile_05.json'
TESTFILE_06_BAD_RAYON_REGIO = TESTFILES_PATH + 'testfile_06.json'
TESTFILE_07_NO_CLUBS = TESTFILES_PATH + 'testfile_07.json'
TESTFILE_08_VER_MUTATIES = TESTFILES_PATH + 'testfile_08.json'
TESTFILE_09_LID_MUTATIES = TESTFILES_PATH + 'testfile_09.json'
TESTFILE_10_TOEVOEGING_NAAM = TESTFILES_PATH + 'testfile_10.json'
TESTFILE_11_BAD_DATE = TESTFILES_PATH + 'testfile_11.json'
TESTFILE_12_MEMBER_INCOMPLETE_1 = TESTFILES_PATH + 'testfile_12.json'
TESTFILE_13_WIJZIG_GESLACHT_1 = TESTFILES_PATH + 'testfile_13.json'
TESTFILE_14_WIJZIG_GESLACHT_2 = TESTFILES_PATH + 'testfile_14.json'
TESTFILE_15_CLUB_1377 = TESTFILES_PATH + 'testfile_15.json'
TESTFILE_16_VERWIJDER_LID = TESTFILES_PATH + 'testfile_16.json'
TESTFILE_17_MEMBER_INCOMPLETE_2 = TESTFILES_PATH + 'testfile_17.json'
TESTFILE_18_LID_UITGESCHREVEN = TESTFILES_PATH + 'testfile_18.json'
TESTFILE_19_STR_NOT_NR = TESTFILES_PATH + 'testfile_19.json'
TESTFILE_20_SPEELSTERKTE = TESTFILES_PATH + 'testfile_20.json'
TESTFILE_21_IBAN_BIC = TESTFILES_PATH + 'testfile_21.json'
TESTFILE_22_CRASH = TESTFILES_PATH + 'testfile_22.json'
TESTFILE_23_DIPLOMA = TESTFILES_PATH + 'testfile_23.json'


class TestImportCRMImport(E2EHelpers, TestCase):

    """ tests voor de ImportCRM applicatie, management commando import_crm_json """

    def setUp(self):
        """ initialisatie van de test case """

        # maak een test vereniging
        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(pk=111))
        ver.save()

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()

    def test_file_not_found(self):
        # afhandelen niet bestaand bestand
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_NOT_EXISTING)

        self.assertTrue(f1.getvalue().startswith('[ERROR] Bestand kan niet gelezen worden'))
        # self.assertEqual(f2.getvalue(), '')

    def test_bad_json(self):
        # afhandelen slechte/lege JSON file
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_01_EMPTY)

        self.assertTrue(f1.getvalue().startswith('[ERROR] Probleem met het JSON formaat in bestand'))
        # self.assertEqual(f2.getvalue(), '')

    def test_toplevel_structuur_afwezig(self):
        # top-level keys afwezig
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_02_INCOMPLETE,
                                                 report_exit_code=False)
        # print("\nf1:\n%s" % f1.getvalue())
        # print("f2:\n%s" % f2.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'rayons' niet aanwezig in de 'top-level' data"
                        in f1.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'regions' niet aanwezig in de 'top-level' data"
                        in f1.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'clubs' niet aanwezig in de 'top-level' data"
                        in f1.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'members' niet aanwezig in de 'top-level' data"
                        in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_import(self):
        with self.assert_max_queries(131):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_03_BASE_DATA,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1000 (Grote Club) heeft geen secretaris!" in f2.getvalue())
        self.assertTrue("[ERROR] Kan secretaris 1 van vereniging 1001 niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100024 heeft geen valide e-mail (enige@khsn)" in f1.getvalue())
        self.assertTrue("[INFO] Wijziging naam rayon 4: 'Rayon 4' --> 'Rayon 99'" in f2.getvalue())
        self.assertTrue("[INFO] Wijziging naam regio 101: 'Regio 101' --> 'Regio 99'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: naam Ramon de Tester --> Voornaam van der Achternaam" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 e-mail: 'rdetester@gmail.not' --> ''" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geslacht: M --> V" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geboortedatum: 1972-03-04 --> 2000-02-01" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: sinds_datum: 2010-11-12 --> 2000-01-01" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: nieuwe speelsterkte 1990-01-01, Recurve, Recurve 1000" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1000 heeft geen KvK nummer" in f2.getvalue())
        self.assertTrue("[INFO] Wijziging van website van vereniging 1000:  --> https://www.groteclub.archery"
                        in f2.getvalue())
        self.assertTrue(
            "[WARNING] Vereniging 1042 website url: 'www.vasteclub.archery' bevat fout (['Voer een geldige URL in.'])"
            in f2.getvalue())
        self.assertTrue("[INFO] Lidmaatschap voor 100101 gaat pas in op datum: '2080-06-06'" in f2.getvalue())
        ver = Vereniging.objects.get(ver_nr=1001)
        self.assertEqual(ver.website, "http://www.somewhere.test")
        self.assertEqual(ver.telefoonnummer, "+316666666")
        self.assertEqual(ver.kvk_nummer, "12345678")

    def test_unicode_error(self):
        # UnicodeDecodeError
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_04_UNICODE_ERROR)
        self.assertTrue(
            "[ERROR] Bestand heeft unicode problemen ('rawunicodeescape' codec can't decode bytes in position 180-181:"
            in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_missing_keys(self):
        # missing/extra keys
        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_05_MISSING_KEYS,
                                             report_exit_code=False)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'name' niet aanwezig in de 'rayon' data" in f1.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'name' niet aanwezig in de 'regio' data" in f1.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'name' niet aanwezig in de 'club' data" in f1.getvalue())
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'name' niet aanwezig in de 'member' data" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'rayon' data: ['name1']" in f2.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'regio' data: ['name2']" in f2.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'club' data: ['name3']" in f2.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'member' data: ['name4']" in f2.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_extra_geo_structuur(self):
        # extra rayon/regio
        with self.assert_max_queries(62):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_06_BAD_RAYON_REGIO)
        self.assertTrue("[ERROR] Onbekend rayon {'rayon_number': 0, 'name': 'Rayon 0'}" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekende regio {'region_number': 0, 'name': 'Regio 0', 'rayon_number': 1}"
                        in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_geen_data(self):
        # lege dataset
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_07_NO_CLUBS)
        self.assertTrue("[ERROR] Geen data voor top-level sleutel 'clubs'" in f1.getvalue())

    def test_vereniging_mutaties(self):
        # vereniging mutaties
        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_03_BASE_DATA,
                                             OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Nieuwe locatie voor adres 'Oude pijlweg 1\\n1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1000] Grote Club gekoppeld aan locatie 'Oude pijlweg 1\\n1234 AB Doelstad'"
                        in f2.getvalue())

        ver = Vereniging.objects.get(ver_nr=1000)

        locatie = WedstrijdLocatie(
                        naam="Ergens buiten",
                        baan_type=BAAN_TYPE_BUITEN)
        locatie.save()
        locatie.verenigingen.add(ver)

        with self.assert_max_queries(136):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_08_VER_MUTATIES,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Wijziging van regio van vereniging 1000: 111 --> 112" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van naam van vereniging 1000: "Grote Club" --> "Nieuwe Grote Club"' in
                        f2.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 1001 niet wijzigen naar onbekende regio 199" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1002 hoort bij onbekende regio 199" in f1.getvalue())
        self.assertTrue("[INFO] Vereniging 1001 secretarissen: geen --> 100001" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van plaats van vereniging 1000: "Stad" --> "Stadia"' in f2.getvalue())
        self.assertTrue(
            'Wijziging van secretaris email voor vereniging 1000: "test@groteclub.archery" --> "andere@groteclub.archer'
            in f2.getvalue())
        self.assertTrue("[INFO] Nieuwe locatie voor adres 'Nieuwe pijlweg 1\\n1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue(
            "Vereniging [1000] Nieuwe Grote Club ontkoppeld van locatie met adres 'Oude pijlweg 1\\n1234 AB Doelstad"
            in f2.getvalue())
        self.assertTrue(
            "[INFO] Vereniging [1000] Nieuwe Grote Club gekoppeld aan locatie 'Nieuwe pijlweg 1\\n1234 AB Doelstad'"
            in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1002 KvK nummer 'X15' moet 8 cijfers bevatten" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1042 KvK nummer '1234' moet 8 cijfers bevatten" in f2.getvalue())

        locatie1 = ver.locatie_set.exclude(baan_type=BAAN_TYPE_BUITEN).get(plaats='Stadia')
        locatie1.plaats = 'Ja maar'
        locatie1.save(update_fields=['plaats'])

        with self.assert_max_queries(114):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_08_VER_MUTATIES,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Vereniging 1000: Aanpassing locatie plaats 'Ja maar' --> 'Stadia'" in f2.getvalue())

        locatie1 = WedstrijdLocatie.objects.get(pk=locatie1.pk)
        self.assertEqual(locatie1.plaats, 'Stadia')

    def test_lid_mutaties(self):
        # lid mutaties
        self.run_management_command(IMPORT_COMMAND,
                                    TESTFILE_03_BASE_DATA,
                                    OPTION_SIM)

        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        sporter = Sporter.objects.get(lid_nr=100098)
        self.assertEqual(sporter.bij_vereniging.ver_nr, 1000)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)
        self.assertEqual(sporter.adres_code, "1111AA111")
        self.assertEqual(sporter.geboorteplaats, 'Papendal')
        self.assertEqual(sporter.telefoon, '+31234567890')

        sporter = Sporter.objects.get(lid_nr=100025)
        self.assertEqual(sporter.wa_id, '90025')

        with self.assert_max_queries(64):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_09_LID_MUTATIES,
                                                 OPTION_SIM)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Lid 100001 heeft geen valide geboortedatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100099 heeft geen valide geboortedatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100100 heeft geen valide e-mail (bad_email)" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100001 heeft onbekend geslacht: Y (moet zijn: M of F)" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100009 heeft geen voornaam of initials" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100099 heeft geen valide datum van overlijden: 'bad-stuff" in f1.getvalue())
        self.assertTrue("[INFO] Lid 100024: is_actief_lid nee --> ja" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: is_actief_lid: ja --> nee" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100024: para_classificatie: 'W1' --> ''" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: is_actief_lid ja --> nee (want blocked)" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100025 is overleden op 2018-05-05 en wordt op inactief gezet" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: vereniging 1000 Grote Club --> 1001 HBS Dichtbij" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100098: adres_code '1111AA111' --> '1115AB5'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100098: geboorteplaats 'Papendal' --> 'Arnhem'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100098: telefoonnummer '+31234567890' --> 'phone_prio_1'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100024: is_erelid False --> True" in f2.getvalue())

        # 100099 is geen lid meer, maar moet toch nog gebruik kunnen blijven maken van de diensten
        sporter = Sporter.objects.get(lid_nr=100098)
        self.assertNotEqual(sporter.bij_vereniging, None)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)
        self.assertEqual(sporter.adres_code, "1115AB5")
        self.assertEqual(sporter.geboorteplaats, 'Arnhem')
        self.assertEqual(sporter.telefoon, 'phone_prio_1')
        self.assertFalse(sporter.is_erelid)

        sporter = Sporter.objects.get(lid_nr=100024)
        self.assertEqual(sporter.postadres_1, 'Dorpsstraat 50')
        self.assertEqual(sporter.postadres_2, '9999ZZ Pijldorp')
        self.assertEqual(sporter.postadres_3, 'Ander land')
        self.assertTrue(sporter.is_erelid)

        sporter = Sporter.objects.get(lid_nr=100025)
        self.assertFalse(sporter.is_actief_lid)      # want: overleden

        # nog een keer hetzelfde commando geeft geen nieuwe log regels
        with self.assert_max_queries(82):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_09_LID_MUTATIES,
                                                 OPTION_SIM)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertFalse("[INFO] Lid 100025 is overleden op 2018-05-05 en wordt op inactief gezet" in f2.getvalue())

    def test_haakjes(self):
        # sommige leden hebben de toevoeging " (Erelid NHB)" aan hun achternaam toegevoegd
        # andere leden hebben een toevoeging achter hun voornaam: "Tineke (Tini)" - niet over klagen
        # some ontbreekt er een haakje
        # import verwijderd dit
        with self.assert_max_queries(73):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_10_TOEVOEGING_NAAM,
                                                 OPTION_SIM)
        # print(f2.getvalue())
        self.assertTrue("Lid 100998" not in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100997: onbalans in haakjes in " in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100996: rare tekens in naam " in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100995: verwijder toevoeging achternaam: 'Dienbaar (Tini)' --> 'Dienbaar'"
                        in f2.getvalue())

    def test_datum_zonder_eeuw(self):
        # sommige leden hebben een geboortedatum zonder eeuw
        with self.assert_max_queries(67):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_11_BAD_DATE,
                                                 OPTION_SIM)

        # print(f1.getvalue(), f2.getvalue())
        self.assertTrue("[WARNING] Lid 100999 geboortedatum gecorrigeerd van 0030-05-05 naar 1930-05-05"
                        in f2.getvalue())
        sporter = Sporter.objects.get(lid_nr=100999)
        self.assertEqual(sporter.geboorte_datum.year, 1930)

        self.assertTrue("[WARNING] Lid 100998 geboortedatum gecorrigeerd van 0010-05-05 naar 2010-05-05"
                        in f2.getvalue())
        sporter = Sporter.objects.get(lid_nr=100998)
        self.assertEqual(sporter.geboorte_datum.year, 2010)
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide geboortedatum: 1810-05-05" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide datum lidmaatschap: 1815-06-06" in f1.getvalue())

    def test_skip_member(self):
        # sommige leden worden niet geïmporteerd
        # geen (valide) geboortedatum
        # geen (valid) datum van lidmaatschap
        with self.assert_max_queries(61):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_12_MEMBER_INCOMPLETE_1,
                                        OPTION_SIM)
        with self.assertRaises(ObjectDoesNotExist):
            Sporter.objects.get(lid_nr=101711)

    def test_del_vereniging(self):
        # test het verwijderen van een lege vereniging

        # maak een test vereniging die verwijderd kan worden
        ver = Vereniging(
                    naam="Weg is weg Club",
                    ver_nr=1998,
                    regio=Regio.objects.get(pk=116))
        ver.save()

        with self.assert_max_queries(77):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_12_MEMBER_INCOMPLETE_1,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1998] Weg is weg Club is verwijderd" in f2.getvalue())

    def test_weer_actief(self):
        # mutatie van inactief lid naar actief lid

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=110000,
                    geslacht="M",
                    voornaam="Zweven",
                    achternaam="de Tester",
                    email="zdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=None,
                    is_actief_lid=False)
        sporter.save()

        with self.assert_max_queries(63):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_13_WIJZIG_GESLACHT_1,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 110000: vereniging geen --> 1000 Grote Club" in f2.getvalue())

        sporter = Sporter.objects.get(pk=sporter.pk)
        self.assertTrue(sporter.bij_vereniging is not None)
        self.assertTrue(sporter.is_actief_lid)

    def test_wijzig_geslacht(self):
        # mutatie van geslacht M naar X voor sporter 100001

        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_13_WIJZIG_GESLACHT_1,
                                             OPTION_SIM)

        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geslacht: M --> X" in f2.getvalue())

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertEqual(sporter.geslacht, 'X')

        # nog een keer, nu met sporter voorkeuren
        sporter.geslacht = 'V'
        sporter.save(update_fields=['geslacht'])

        voorkeuren = SporterVoorkeuren(sporter=sporter,
                                       wedstrijd_geslacht_gekozen=True,
                                       wedstrijd_geslacht='V')
        voorkeuren.save()

        with self.assert_max_queries(25):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_13_WIJZIG_GESLACHT_1,
                                                 OPTION_SIM)
        self.assertTrue("[INFO] Lid 100001 geslacht: V --> X" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 voorkeuren: wedstrijd geslacht instelbaar gemaakt" in f2.getvalue())

        # nu weer de andere kant op (X --> M)
        with self.assert_max_queries(66):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geslacht: X --> M" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 voorkeuren: wedstrijd geslacht vastgezet" in f2.getvalue())

    def test_maak_secretaris(self):
        # een lid secretaris maken
        with self.assert_max_queries(100):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue('[WARNING] Vereniging 1000 heeft geen adres' in f2.getvalue())
        self.assertTrue("[INFO] Vereniging 1000 secretarissen: geen --> 100001" in f2.getvalue())
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 heeft nog geen account" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging 2000 secretarissen: geen --> 100024+100001" in f2.getvalue())
        self.assertTrue("[WARNING] Secretaris 100001 is geen lid bij vereniging 2000" in f2.getvalue())

        ver = Vereniging.objects.get(ver_nr="1000")
        functie = Functie.objects.get(rol="SEC", vereniging=ver)
        self.assertEqual(functie.accounts.count(), 1)

        secs = Secretaris.objects.prefetch_related('sporters').get(vereniging__ver_nr=2000)
        self.assertEqual(2, secs.sporters.count())

        ver = Vereniging.objects.get(ver_nr="2000")
        functie = Functie.objects.get(rol="SEC", vereniging=ver)
        self.assertEqual(functie.accounts.count(), 1)

        # 100024 is nog geen SEC omdat ze geen account heeft
        # maak het account van 100024 aan en probeer het nog een keer
        sporter = Sporter.objects.get(lid_nr="100024")
        sporter.account = self.e2e_create_account(sporter.lid_nr, 'maakt.niet.uit@gratis.net', sporter.voornaam)
        sporter.save()

        # corner-case: nog geen bevestigde emailadres
        account = sporter.account
        account.email_is_bevestigd = False
        account.save(update_fields=['email_is_bevestigd'])

        with self.assert_max_queries(34):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Secretaris 100024 van vereniging 2000 heeft nog geen bevestigd e-mailadres"
                        in f2.getvalue())
        self.assertEqual(functie.accounts.count(), 1)

        # koppelen aan functie SEC na bevestigen e-mailadres
        account.email_is_bevestigd = True
        account.save(update_fields=['email_is_bevestigd'])

        with self.assert_max_queries(34):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan SEC functie" in f2.getvalue())
        self.assertEqual(functie.accounts.count(), 2)

    def test_club_1377(self):
        # een paar speciale import gevallen

        with self.assert_max_queries(92):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_15_CLUB_1377,
                                        OPTION_SIM)

        # controleer de geen_wedstrijden vlag voor 1377 en normale clubs
        ver = Vereniging.objects.get(ver_nr=1000)
        self.assertFalse(ver.geen_wedstrijden)

        ver = Vereniging.objects.get(ver_nr=1377)
        self.assertTrue(ver.geen_wedstrijden)

        # verifieer verwijderen van "(geen deelname wedstrijden)" uit de naam
        self.assertEqual(ver.naam, "Persoonlijk")

        # controleer dat de mutatie achteraf werkt
        ver = Vereniging.objects.get(ver_nr=1000)
        ver.geen_wedstrijden = True
        ver.save()

        ver = Vereniging.objects.get(ver_nr=1377)
        ver.geen_wedstrijden = False
        ver.save()

        with self.assert_max_queries(28):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_15_CLUB_1377,
                                                 OPTION_SIM)
        self.assertTrue("[INFO] Wijziging van 'geen wedstrijden' van vereniging 1377: False --> True" in f2.getvalue())
        self.assertTrue("[INFO] Wijziging van 'geen wedstrijden' van vereniging 1000: True --> False" in f2.getvalue())
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

    def test_verwijder_secretaris_fail(self):
        # verwijderen van de secretaris geeft een fout

        # maak 100024 aan
        self.run_management_command(IMPORT_COMMAND,
                                    TESTFILE_14_WIJZIG_GESLACHT_2,
                                    OPTION_SIM)

        # maak het account van 100024 aan, zodat deze secretaris kan worden
        # maak het account van 100024 aan en probeer het nog een keer
        sporter = Sporter.objects.get(lid_nr="100024")
        sporter.account = self.e2e_create_account(sporter.lid_nr, 'maakt.niet.uit@gratis.net', sporter.voornaam)
        sporter.save()

        # maak 100024 secretaris
        with self.assert_max_queries(32):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        self.assertTrue('[WARNING] Vereniging 1000 heeft geen adres' in f2.getvalue())
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan SEC functie" in f2.getvalue())

        # probeer 100024 te verwijderen
        with self.assert_max_queries(58):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_16_VERWIJDER_LID,
                                                 OPTION_SIM)
        self.assertTrue("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())

    def test_verwijder_recordhouder_fail(self):
        # maak 100024 aan
        self.run_management_command(IMPORT_COMMAND,
                                    TESTFILE_14_WIJZIG_GESLACHT_2,
                                    OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        # maak een record aan op naam van 100024
        sporter = Sporter.objects.get(lid_nr="100024")
        IndivRecord(volg_nr=1,
                    sporter=sporter,
                    score=1,
                    datum="2018-01-01").save()

        # probeer 100024 te verwijderen
        with self.assert_max_queries(31):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_16_VERWIJDER_LID,
                                                 OPTION_SIM)
        self.assertFalse("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())

    def test_verwijder_score_fail(self):
        # maak 100024 aan
        self.run_management_command(IMPORT_COMMAND,
                                    TESTFILE_14_WIJZIG_GESLACHT_2,
                                    OPTION_SIM)

        # maak een sporter-boog aan
        boog_r = BoogType.objects.get(afkorting='R')
        sporter = Sporter.objects.get(lid_nr="100024")
        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=boog_r)
        sporterboog.save()
        score_indiv_ag_opslaan(sporterboog, 18, 5.678, None, "")

        # probeer 100024 te verwijderen
        with self.assert_max_queries(48):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_16_VERWIJDER_LID,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())
        self.assertTrue('[ERROR] Onverwachte fout bij het verwijderen van een lid' in f1.getvalue())

    def test_import_nhb_crm_dryrun(self):
        # dryrun
        with self.assert_max_queries(51):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_08_VER_MUTATIES,
                                                 OPTION_SIM,
                                                 OPTION_DRY_RUN)
        self.assertTrue("DRY RUN" in f2.getvalue())

        with self.assert_max_queries(104):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_03_BASE_DATA,
                                        OPTION_SIM)

        ver = Vereniging.objects.get(ver_nr=1000)
        ver.geen_wedstrijden = True
        ver.save()

        with self.assert_max_queries(40):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_08_VER_MUTATIES,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)
        with self.assert_max_queries(28):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_09_LID_MUTATIES,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)
        with self.assert_max_queries(41):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_14_WIJZIG_GESLACHT_2,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)

        # maak een test vereniging die verwijderd kan worden
        ver = Vereniging(
                    naam="Weg is weg Club",
                    ver_nr=1999,
                    regio=Regio.objects.get(pk=116))
        ver.save()
        with self.assert_max_queries(26):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_12_MEMBER_INCOMPLETE_1,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)

    def test_incomplete_data(self):
        # test import met een incomplete entry van een nieuw lid
        with self.assert_max_queries(77):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_17_MEMBER_INCOMPLETE_2,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Lid 100002 heeft geen achternaam" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100007 heeft geen valide geboortedatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100008 heeft geen valide lidmaatschapsdatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100009 heeft geen voornaam of initials" in f1.getvalue())

    def test_bad_sim_now(self):
        # puur voor de coverage
        with self.assert_max_queries(0):
            f1, f2 = self.run_management_command(IMPORT_COMMAND, 'x', '--sim_now=y-m-d')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] geen valide sim_now" in f1.getvalue())

    def test_uitschrijven(self):
        # lid schrijft zich uit bij een vereniging en mag tot einde jaar diensten gebruiken
        self.run_management_command(IMPORT_COMMAND,
                                    TESTFILE_03_BASE_DATA,
                                    OPTION_SIM)

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is not None)

        # lid 100001 heeft zich uitgeschreven tijdens het jaar
        with self.assert_max_queries(54):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_18_LID_UITGESCHREVEN,
                                                 '--sim_now=2020-07-02')
            # print("f1: %s" % f1.getvalue())
            # print("f2: %s" % f2.getvalue())

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is not None)

        # lid 100001 is nog steeds uitgeschreven - geen verandering tot 15 januari
        with self.assert_max_queries(63):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_18_LID_UITGESCHREVEN,
                                        '--sim_now=2021-01-15')

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is not None)

        # lid 100001 is nog steeds uitgeschreven - verandering komt na 15 januari
        with self.assert_max_queries(32):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_18_LID_UITGESCHREVEN,
                                        OPTION_DRY_RUN,
                                        '--sim_now=2021-01-16')

        with self.assert_max_queries(39):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_18_LID_UITGESCHREVEN,
                                        '--sim_now=2021-01-16')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertFalse(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is None)

        _ = (f1 == f2)

    def test_bad_nrs(self):
        # controleer dat de import tegen niet-nummers kan
        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_19_STR_NOT_NR)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Foutief rayon nummer: 'x' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekend rayon {'rayon_number': 'x', 'name': 'Rayon 1'}" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekend rayon {'rayon_number': 5, 'name': 'Rayon 5'}" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief regio nummer: 'a101' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekende regio {'region_number': 'a101', 'name': 'Regio 99', 'rayon_number': 1}"
                        in f1.getvalue())
        self.assertTrue("[ERROR] Onbekende regio {'region_number': '99', 'name': 'Regio 99', 'rayon_number': 'x'}"
                        in f1.getvalue())
        self.assertTrue("[ERROR] Foutief verenigingsnummer: 'y' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief regio nummer: 'z' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1001 hoort bij onbekende regio z" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief bondsnummer: x (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief verenigingsnummer: 'y' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 'y' voor lid 100024 niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief bondsnummer: ggg (geen getal)" in f1.getvalue())
        self.assertTrue("[WARNING] Kan speelsterkte volgorde niet vaststellen voor" in f2.getvalue())
        self.assertTrue(
            "[ERROR] Vereniging 1001 heeft BIC '1234' met foute lengte 4 (niet 8 of 11) horende bij IBAN '1234'"
            in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1001 heeft IBAN '1234' met foute lengte 4 (niet 18)" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1042 heeft IBAN 'Wat een grap' met foute lengte 12 (niet 18)"
                        in f1.getvalue())

    def test_speelsterkte(self):
        # controleer dat de import tegen niet-nummers kan
        self.run_management_command(IMPORT_COMMAND,
                                    TESTFILE_03_BASE_DATA,
                                    OPTION_SIM)

        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_20_SPEELSTERKTE)
        self.assertTrue("[INFO] Lid 100001: nieuwe speelsterkte 1991-01-01, Recurve, Recurve 1100" in f2.getvalue())

    def test_iban_bic(self):
        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_21_IBAN_BIC)

        self.assertTrue("[WARNING] Vereniging 1001 heeft een IBAN zonder BIC: None, 'NL91ABNA0417164300'"
                        in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1042 heeft een BIC zonder IBAN: 'ABNANL2A', None" in f2.getvalue())   # noqa
        self.assertTrue(
            "[WARNING] Vereniging 1000 heeft een onbekende BIC code 'HUH2HUH2' horende bij IBAN 'NL91ABNA0417164300'"  # noqa
            in f2.getvalue())
        self.assertTrue("ERROR] Vereniging 1043 heeft een foutieve IBAN: 'NL91ABNA0417164309'" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1044 heeft IBAN 'NL91ABNA0TEKORT' met foute lengte 15 (niet 18)"
                        in f1.getvalue())

    def test_crash(self):
        self.assertEqual(0, MailQueue.objects.count())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(SystemExit):
            f1, f2 = call_command(IMPORT_COMMAND,
                                  OPTION_DRY_RUN,
                                  TESTFILE_22_CRASH,    # triggers crash
                                  stderr=f1,            # noodzakelijk voor de test!
                                  stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Onverwachte fout tijdens import_crm_json: crash test" in f1.getvalue())

        self.assertEqual(1, MailQueue.objects.count())

    def test_diploma(self):
        # importeer diploma's

        test_opleiding_codes = [
            ('042', 'Pas ja', 'Test code 42', ())
        ]

        with override_settings(OPLEIDING_CODES=test_opleiding_codes):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_23_DIPLOMA)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue("[WARNING] Opleiding code 043 is niet bekend (1 keer in gebruik)" in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100001 heeft een dubbele opleiding: code 042" in f2.getvalue())

        self.assertEqual(OpleidingDiploma.objects.count(), 1)
        diploma = OpleidingDiploma.objects.first()

        self.assertEqual(diploma.code, '042')
        self.assertEqual(diploma.sporter.lid_nr, 100001)
        self.assertEqual(diploma.beschrijving, 'Test code 42')
        self.assertTrue(diploma.toon_op_pas)
        self.assertEqual(str(diploma.datum_begin), '2009-04-05')
        self.assertEqual(str(diploma.datum_einde), '2012-04-24')

        # gedrag bij opnieuw importeren
        with override_settings(OPLEIDING_CODES=test_opleiding_codes):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_23_DIPLOMA,
                                                 '--dryrun')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        # controleer dat er geen mutaties zijn
        self.assertFalse('datum_begin' in f2.getvalue())
        self.assertFalse('datum_einde' in f2.getvalue())

        self.assertEqual(OpleidingDiploma.objects.count(), 1)
        diploma.beschrijving = "oud"
        diploma.datum_begin = '2999-01-01'
        diploma.datum_einde = '2999-02-02'
        diploma.save()

        with override_settings(OPLEIDING_CODES=test_opleiding_codes):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_23_DIPLOMA)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        # controleer dat er mutaties zijn
        self.assertTrue('datum_begin' in f2.getvalue())
        self.assertTrue('datum_einde' in f2.getvalue())

        self.assertEqual(OpleidingDiploma.objects.count(), 1)
        diploma = OpleidingDiploma.objects.first()
        self.assertEqual(diploma.code, '042')
        self.assertEqual(diploma.sporter.lid_nr, 100001)
        self.assertEqual(diploma.beschrijving, 'Test code 42')
        self.assertTrue(diploma.toon_op_pas)
        self.assertEqual(str(diploma.datum_begin), '2009-04-05')
        self.assertEqual(str(diploma.datum_einde), '2012-04-24')

    def test_demo_club(self):
        # in settings.CRM_IMPORT_BEHOUD_CLUB kunnen we een clubnummer zetten dat niet verwijderd wordt
        # dit wordt gebruikt voor demos en screenshots in de handleiding

        ver_nr = settings.CRM_IMPORT_BEHOUD_CLUB[0]

        self.assertEqual(0, Vereniging.objects.filter(ver_nr=ver_nr).count())

        # maak de speciale club aan
        ver = Vereniging(
                    ver_nr=ver_nr,
                    naam="Demo Club",
                    regio=Regio.objects.get(pk=115))
        ver.save()

        # koppel een lid aan deze club
        sporter = Sporter(
                    lid_nr=100888,
                    geslacht="M",
                    voornaam="Demo",
                    achternaam="Lid",
                    email="demolid@test.not",
                    geboorte_datum=datetime.date(year=1970, month=3, day=4),
                    sinds_datum=datetime.date(year=2012, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()

        self.assertEqual(2, Sporter.objects.count())

        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_23_DIPLOMA)
        _ = (f1 == f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertEqual(1, Vereniging.objects.filter(ver_nr=ver_nr).count())
        self.assertEqual(3, Sporter.objects.count())

        # nog een keer, maar dan met lege configuratie
        # dus dan wordt de club wel verwijderd
        sporter.delete()

        with override_settings(CRM_IMPORT_BEHOUD_CLUB=()):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_23_DIPLOMA)
        _ = (f1 == f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertEqual(0, Vereniging.objects.filter(ver_nr=ver_nr).count())


# end of file
