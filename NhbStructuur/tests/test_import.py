# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ObjectDoesNotExist
from BasisTypen.models import BoogType
from Functie.models import Functie
from Mailer.models import MailQueue
from NhbStructuur.models import NhbRegio, NhbVereniging
from Records.models import IndivRecord
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


IMPORT_COMMAND = 'import_nhb_crm'
OPTION_DRY_RUN = '--dryrun'
OPTION_SIM = '--sim_now=2020-07-01'

TESTFILES_PATH = './NhbStructuur/management/testfiles/'

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


class TestNhbStructuurImport(E2EHelpers, TestCase):

    """ tests voor de NhbStructuur applicatie, functie Import uit CRM """

    def setUp(self):
        """ initialisatie van de test case """

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
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

        self.assertTrue("[ERROR] Verplichte sleutel 'rayons' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'regions' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'clubs' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'members' niet aanwezig in de 'top-level' data" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_import(self):
        with self.assert_max_queries(93):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_03_BASE_DATA,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1000 (Grote Club) heeft geen secretaris!" in f1.getvalue())
        self.assertTrue("[ERROR] Kan secretaris 1 van vereniging 1001 niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100024 heeft geen valide e-mail (enige@nhb)" in f1.getvalue())
        self.assertTrue("[INFO] Wijziging naam rayon 4: 'Rayon 4' --> 'Rayon 99'" in f2.getvalue())
        self.assertTrue("[INFO] Wijziging naam regio 101: 'Regio 101' --> 'Regio 99'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: naam Ramon de Tester --> Voornaam van der Achternaam" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 e-mail: 'rdetester@gmail.not' --> ''" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geslacht: M --> V" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geboortedatum: 1972-03-04 --> 2000-02-01" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: sinds_datum: 2010-11-12 --> 2000-01-01" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: nieuwe speelsterkte 1990-01-01, Recurve, Recurve 1000" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1000 heeft geen KvK nummer" in f2.getvalue())
        self.assertTrue("[INFO] Wijziging van website van vereniging 1000:  --> https://www.groteclub.archery" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1042 website url: 'www.vasteclub.archery' bevat fout (['Voer een geldige URL in.'])" in f2.getvalue())

        ver = NhbVereniging.objects.get(ver_nr=1001)
        self.assertEqual(ver.website, "http://www.somewhere.test")
        self.assertEqual(ver.telefoonnummer, "+316666666")
        self.assertEqual(ver.kvk_nummer, "12345678")

    def test_unicode_error(self):
        # UnicodeDecodeError
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_04_UNICODE_ERROR)
        self.assertTrue("[ERROR] Bestand heeft unicode problemen ('rawunicodeescape' codec can't decode bytes in position 180-181: truncated" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_missing_keys(self):
        # missing/extra keys
        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_05_MISSING_KEYS,
                                             report_exit_code=False)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'rayon' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'regio' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'club' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'member' data" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'rayon' data: ['name1']" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'regio' data: ['name2']" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'club' data: ['name3']" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'member' data: ['name4']" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_extra_geo_structuur(self):
        # extra rayon/regio
        with self.assert_max_queries(32):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_06_BAD_RAYON_REGIO)
        self.assertTrue("[ERROR] Onbekend rayon {'rayon_number': 0, 'name': 'Rayon 0'}" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekende regio {'region_number': 0, 'name': 'Regio 0', 'rayon_number': 1}" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_geen_data(self):
        # lege dataset
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_07_NO_CLUBS)
        self.assertTrue("[ERROR] Geen data voor top-level sleutel 'clubs'" in f1.getvalue())

    def test_vereniging_mutaties(self):
        # vereniging mutaties
        with self.assert_max_queries(93):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_03_BASE_DATA,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Nieuwe wedstrijdlocatie voor adres 'Oude pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1000] Grote Club gekoppeld aan wedstrijdlocatie 'Oude pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())

        with self.assert_max_queries(55):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_08_VER_MUTATIES,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Wijziging van regio van vereniging 1000: 111 --> 112" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van naam van vereniging 1000: "Grote Club" --> "Nieuwe Grote Club"' in f2.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 1001 niet wijzigen naar onbekende regio 199" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1002 hoort bij onbekende regio 199" in f1.getvalue())
        self.assertTrue("[INFO] Wijziging van secretaris voor vereniging 1001: geen --> 100001" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van plaats van vereniging 1000: "Stad" --> "Stadia"' in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van secretaris email voor vereniging 1000: "test@groteclub.archery" --> "andere@groteclub.archery"' in f2.getvalue())
        self.assertTrue("[INFO] Nieuwe wedstrijdlocatie voor adres 'Nieuwe pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1000] Nieuwe Grote Club ontkoppeld van wedstrijdlocatie met adres 'Oude pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1000] Nieuwe Grote Club gekoppeld aan wedstrijdlocatie 'Nieuwe pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1002 KvK nummer 'X15' moet 8 cijfers bevatten" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1042 KvK nummer '1234' moet 8 cijfers bevatten" in f2.getvalue())

    def test_lid_mutaties(self):
        # lid mutaties
        with self.assert_max_queries(93):
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

        with self.assert_max_queries(51):
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
        self.assertTrue("[INFO] Lid 100024: is_actief_lid nee --> ja" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: is_actief_lid: ja --> nee" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100024: para_classificatie: 'W1' --> ''" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: is_actief_lid ja --> nee (want blocked)" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: vereniging 1000 Grote Club --> 1001 HBS Dichtbij" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100098: adres_code '1111AA111' --> '1115AB5'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100098: geboorteplaats 'Papendal' --> 'Arnhem'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100098: telefoonnummer '+31234567890' --> 'phone_prio_1'" in f2.getvalue())

        # 100099 is geen lid meer, maar moet toch nog gebruik kunnen blijven maken van de diensten
        sporter = Sporter.objects.get(lid_nr=100098)
        self.assertNotEqual(sporter.bij_vereniging, None)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)
        self.assertEqual(sporter.adres_code, "1115AB5")
        self.assertEqual(sporter.geboorteplaats, 'Arnhem')
        self.assertEqual(sporter.telefoon, 'phone_prio_1')

    def test_haakjes(self):
        # sommige leden hebben de toevoeging " (Erelid NHB)" aan hun achternaam toegevoegd
        # andere leden hebben een toevoeging achter hun voornaam: "Tineke (Tini)" - niet over klagen
        # some ontbreekt er een haakje
        # import verwijderd dit
        with self.assert_max_queries(41):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_10_TOEVOEGING_NAAM,
                                                 OPTION_SIM)
        # print(f2.getvalue())
        self.assertTrue("[WARNING] Lid 100999: verwijder toevoeging achternaam: 'Dienbaar (Erelid NHB)' --> 'Dienbaar'" in f2.getvalue())
        self.assertTrue("Lid 100998" not in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100997: onbalans in haakjes in " in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100996: rare tekens in naam " in f2.getvalue())

    def test_datum_zonder_eeuw(self):
        # sommige leden hebben een geboortedatum zonder eeuw
        with self.assert_max_queries(37):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_11_BAD_DATE,
                                                 OPTION_SIM)

        # print(f1.getvalue(), f2.getvalue())
        self.assertTrue("[WARNING] Lid 100999 geboortedatum gecorrigeerd van 0030-05-05 naar 1930-05-05" in f1.getvalue())
        sporter = Sporter.objects.get(lid_nr=100999)
        self.assertEqual(sporter.geboorte_datum.year, 1930)

        self.assertTrue("[WARNING] Lid 100998 geboortedatum gecorrigeerd van 0010-05-05 naar 2010-05-05" in f1.getvalue())
        sporter = Sporter.objects.get(lid_nr=100998)
        self.assertEqual(sporter.geboorte_datum.year, 2010)
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide geboortedatum: 1810-05-05" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide datum lidmaatschap: 1815-06-06" in f1.getvalue())

    def test_skip_member(self):
        # sommige leden worden niet geïmporteerd
        # geen (valide) geboortedatum
        # geen (valid) datum van lidmaatschap
        with self.assert_max_queries(36):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_12_MEMBER_INCOMPLETE_1,
                                        OPTION_SIM)
        with self.assertRaises(ObjectDoesNotExist):
            Sporter.objects.get(lid_nr=101711)

    def test_del_vereniging(self):
        # test het verwijderen van een lege vereniging

        # maak een test vereniging die verwijderd kan worden
        ver = NhbVereniging()
        ver.naam = "Wegisweg Club"
        ver.ver_nr = "1998"
        ver.regio = NhbRegio.objects.get(pk=116)
        ver.save()

        with self.assert_max_queries(46):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_12_MEMBER_INCOMPLETE_1,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1998] Wegisweg Club wordt nu verwijderd" in f2.getvalue())

    def test_weer_actief(self):
        # mutatie van inactief lid naar actief lid

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 110000
        sporter.geslacht = "M"
        sporter.voornaam = "Zweven"
        sporter.achternaam = "de Tester"
        sporter.email = "zdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = None
        sporter.is_actief_lid = False
        sporter.save()

        with self.assert_max_queries(33):
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

        with self.assert_max_queries(34):
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

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_13_WIJZIG_GESLACHT_1,
                                                 OPTION_SIM)
        self.assertTrue("[INFO] Lid 100001 geslacht: V --> X" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 voorkeuren: wedstrijd geslacht instelbaar gemaakt" in f2.getvalue())

        # nu weer de andere kant op (X --> M)
        with self.assert_max_queries(61):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geslacht: X --> M" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 voorkeuren: wedstrijd geslacht vastgezet" in f2.getvalue())

    def test_maak_secretaris(self):
        # een lid secretaris maken
        with self.assert_max_queries(63):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        self.assertTrue('[WARNING] Vereniging 1000 heeft geen adres' in f2.getvalue())
        self.assertTrue("[INFO] Wijziging van secretaris voor vereniging 1000: geen --> 100001 Ramon de Tester" in f2.getvalue())
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 heeft nog geen account" in f2.getvalue())
        self.assertTrue("[WARNING] Meerdere secretarissen voor vereniging 2000 is niet ondersteund: 100024, 100001" in f2.getvalue())

        # lid = Sporter.objects.get(lid_nr="100001")
        ver = NhbVereniging.objects.get(ver_nr="1000")
        functie = Functie.objects.get(rol="SEC", nhb_ver=ver)
        self.assertEqual(functie.accounts.count(), 1)

        sporter = Sporter.objects.get(lid_nr="100024")
        ver = NhbVereniging.objects.get(ver_nr="2000")
        functie = Functie.objects.get(rol="SEC", nhb_ver=ver)
        self.assertEqual(functie.accounts.count(), 0)
        # 100024 is nog geen SEC omdat ze geen account heeft

        # maak het account van 100024 aan en probeer het nog een keer
        sporter.account = self.e2e_create_account(sporter.lid_nr, 'maakt.niet.uit@gratis.net', sporter.voornaam)
        sporter.save()

        with self.assert_max_queries(29):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        self.assertTrue('[WARNING] Vereniging 1000 heeft geen adres' in f2.getvalue())
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan SEC functie" in f2.getvalue())

        ver = NhbVereniging.objects.get(ver_nr="2000")
        functie = Functie.objects.get(rol="SEC", nhb_ver=ver)
        self.assertEqual(functie.accounts.count(), 1)

    def test_club_1377(self):
        # een paar speciale import gevallen

        with self.assert_max_queries(67):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_15_CLUB_1377,
                                        OPTION_SIM)

        # controleer de geen_wedstrijden vlag voor 1377 en normale clubs
        ver = NhbVereniging.objects.get(ver_nr=1000)
        self.assertFalse(ver.geen_wedstrijden)

        ver = NhbVereniging.objects.get(ver_nr=1377)
        self.assertTrue(ver.geen_wedstrijden)

        # verifieer verwijderen van "(geen deelname wedstrijden)" uit de naam
        self.assertEqual(ver.naam, "Persoonlijk")

        # controleer dat de mutatie achteraf werkt
        ver = NhbVereniging.objects.get(ver_nr=1000)
        ver.geen_wedstrijden = True
        ver.save()

        ver = NhbVereniging.objects.get(ver_nr=1377)
        ver.geen_wedstrijden = False
        ver.save()

        with self.assert_max_queries(25):
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
        with self.assert_max_queries(63):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_14_WIJZIG_GESLACHT_2,
                                        OPTION_SIM)

        # maak het account van 100024 aan, zodat deze secretaris kan worden
        # maak het account van 100024 aan en probeer het nog een keer
        sporter = Sporter.objects.get(lid_nr="100024")
        sporter.account = self.e2e_create_account(sporter.lid_nr, 'maakt.niet.uit@gratis.net', sporter.voornaam)
        sporter.save()

        # maak 100024 secretaris
        with self.assert_max_queries(29):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_14_WIJZIG_GESLACHT_2,
                                                 OPTION_SIM)
        self.assertTrue('[WARNING] Vereniging 1000 heeft geen adres' in f2.getvalue())
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan SEC functie" in f2.getvalue())

        # probeer 100024 te verwijderen
        with self.assert_max_queries(32):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_16_VERWIJDER_LID,
                                                 OPTION_SIM)
        self.assertTrue("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())

    def test_verwijder_recordhouder_fail(self):
        # maak 100024 aan
        with self.assert_max_queries(63):
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
        with self.assert_max_queries(24):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_16_VERWIJDER_LID,
                                                 OPTION_SIM)
        self.assertFalse("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())

    def test_verwijder_score_fail(self):
        # maak 100024 aan
        with self.assert_max_queries(63):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_14_WIJZIG_GESLACHT_2,
                                        OPTION_SIM)

        # maak een schutterboog aan
        boog_r = BoogType.objects.get(afkorting='R')
        sporter = Sporter.objects.get(lid_nr="100024")
        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=boog_r)
        sporterboog.save()
        score_indiv_ag_opslaan(sporterboog, 18, 5.678, None, "")

        # probeer 100024 te verwijderen
        with self.assert_max_queries(41):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_16_VERWIJDER_LID,
                                                 OPTION_SIM)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())
        self.assertTrue('[ERROR] Onverwachte fout bij het verwijderen van een lid' in f1.getvalue())

    def test_import_nhb_crm_dryrun(self):
        # dryrun
        with self.assert_max_queries(42):
            f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                                 TESTFILE_08_VER_MUTATIES,
                                                 OPTION_SIM,
                                                 OPTION_DRY_RUN)
        self.assertTrue("DRY RUN" in f2.getvalue())

        with self.assert_max_queries(69):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_03_BASE_DATA,
                                        OPTION_SIM)

        ver = NhbVereniging.objects.get(ver_nr=1000)
        ver.geen_wedstrijden = True
        ver.save()

        with self.assert_max_queries(31):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_08_VER_MUTATIES,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)
        with self.assert_max_queries(19):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_09_LID_MUTATIES,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)
        with self.assert_max_queries(36):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_14_WIJZIG_GESLACHT_2,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)

        # maak een test vereniging die verwijderd kan worden
        ver = NhbVereniging()
        ver.naam = "Wegisweg Club"
        ver.ver_nr = "1999"
        ver.regio = NhbRegio.objects.get(pk=116)
        ver.save()
        with self.assert_max_queries(19):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_12_MEMBER_INCOMPLETE_1,
                                        OPTION_SIM,
                                        OPTION_DRY_RUN)

    def test_incomplete_data(self):
        # test import met een incomplete entry van een nieuw lid
        with self.assert_max_queries(48):
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
        with self.assert_max_queries(93):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_03_BASE_DATA,
                                        OPTION_SIM)

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is not None)

        # lid 100001 heeft zich uitgeschreven tijdens het jaar
        with self.assert_max_queries(45):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_18_LID_UITGESCHREVEN,
                                        '--sim_now=2020-07-02')

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is not None)

        # lid 100001 is nog steeds uitgeschreven - geen verandering tot 15 januari
        with self.assert_max_queries(45):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_18_LID_UITGESCHREVEN,
                                        '--sim_now=2021-01-15')

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertTrue(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is not None)

        # lid 100001 is nog steeds uitgeschreven - verandering komt na 15 januari
        with self.assert_max_queries(24):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_18_LID_UITGESCHREVEN,
                                        OPTION_DRY_RUN,
                                        '--sim_now=2021-01-16')

        with self.assert_max_queries(34):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_18_LID_UITGESCHREVEN,
                                        '--sim_now=2021-01-16')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        sporter = Sporter.objects.get(lid_nr=100001)
        self.assertFalse(sporter.is_actief_lid)
        self.assertEqual(sporter.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(sporter.bij_vereniging is None)

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
        self.assertTrue("[ERROR] Onbekende regio {'region_number': 'a101', 'name': 'Regio 99', 'rayon_number': 1}" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekende regio {'region_number': '99', 'name': 'Regio 99', 'rayon_number': 'x'}" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief verenigingsnummer: 'y' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief regio nummer: 'z' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1001 hoort bij onbekende regio z" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief bondsnummer: x (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief verenigingsnummer: 'y' (geen getal)" in f1.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 'y' voor lid 100024 niet vinden" in f1.getvalue())
        self.assertTrue("[ERROR] Foutief bondsnummer: ggg (geen getal)" in f1.getvalue())
        self.assertTrue("[WARNING] Kan speelsterkte volgorde niet vaststellen voor" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1001 heeft BIC '1234' met foute length 4 (verwacht: 8 of 11) horende bij IBAN '1234'" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1001 heeft IBAN '1234' met foute length 4 (verwacht: 18)" in f1.getvalue())
        # self.assertTrue("[ERROR] Vereniging 1042 heeft BIC 'fout lengte' met foute length 12 (verwacht: 8 of 11) horende bij IBAN 'Wat een grap'" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1042 heeft IBAN 'Wat een grap' met foute length 12 (verwacht: 18)" in f1.getvalue())

    def test_speelsterkte(self):
        # controleer dat de import tegen niet-nummers kan
        with self.assert_max_queries(93):
            self.run_management_command(IMPORT_COMMAND,
                                        TESTFILE_03_BASE_DATA,
                                        OPTION_SIM)

        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_20_SPEELSTERKTE)
        self.assertTrue("[INFO] Lid 100001: nieuwe speelsterkte 1991-01-01, Recurve, Recurve 1100" in f2.getvalue())

    def test_iban_bic(self):
        f1, f2 = self.run_management_command(IMPORT_COMMAND,
                                             TESTFILE_21_IBAN_BIC)

        self.assertTrue("[WARNING] Vereniging 1001 heeft een IBAN zonder BIC: None, 'NL91ABNA0417164300'" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1042 heeft een BIC zonder IBAN: 'ABNANL2A', None" in f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1000 heeft een onbekende BIC code 'HUH2HUH2' horende bij IBAN 'NL91ABNA0417164300'" in f2.getvalue())
        self.assertTrue("ERROR] Vereniging 1043 heeft een foutieve IBAN: 'NL91ABNA0417164309'" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1044 heeft IBAN 'NL91ABNA0TEKORT' met foute length 15 (verwacht: 18)" in f1.getvalue())

    def test_crash(self):
        self.assertEqual(0, MailQueue.objects.count())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(SystemExit):
            f1, f2 = call_command(IMPORT_COMMAND,
                                  OPTION_DRY_RUN,
                                  TESTFILE_22_CRASH,  # triggers crash
                                  stderr=f1,
                                  stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Onverwachte fout tijdens import_nhb_crm: crash test" in f1.getvalue())

        self.assertEqual(1, MailQueue.objects.count())


# end of file
