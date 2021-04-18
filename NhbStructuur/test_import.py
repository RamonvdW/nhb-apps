# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Functie.models import Functie
from Overig.e2ehelpers import E2EHelpers
from Records.models import IndivRecord
from Schutter.models import SchutterBoog
from Score.models import score_indiv_ag_opslaan
from .models import NhbRegio, NhbVereniging, NhbLid
import datetime
import io


class TestNhbStructuurImport(E2EHelpers, TestCase):
    """ unit tests voor de NhbStructuur applicatie """

    def setUp(self):
        """ initialisatie van de test case """

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)
        lid.save()

    def test_file_not_found(self):
        # afhandelen niet bestaand bestand
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/notexisting.json',
                                    stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue().startswith('[ERROR] Bestand kan niet gelezen worden'))
        # self.assertEqual(f2.getvalue(), '')

    def test_bad_json(self):
        # afhandelen slechte/lege JSON file
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_01.json',
                                    stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue().startswith('[ERROR] Probleem met het JSON formaat in bestand'))
        # self.assertEqual(f2.getvalue(), '')

    def test_toplevel_structuur_afwezig(self):
        # top-level keys afwezig
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_02.json',
                                    stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Verplichte sleutel 'rayons' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'regions' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'clubs' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'members' niet aanwezig in de 'top-level' data" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_import(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(84):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
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

    def test_unicode_error(self):
        # UnicodeDecodeError
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_04.json',
                                    stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Bestand heeft unicode problemen ('rawunicodeescape' codec can't decode bytes in position 180-181: truncated" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_missing_keys(self):
        # missing/extra keys
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_05.json',
                                    stderr=f1, stdout=f2)
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
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(26):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_06.json',
                                    stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Onbekend rayon {'rayon_number': 0, 'name': 'Rayon 0'}" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekende regio {'region_number': 0, 'name': 'Regio 0', 'rayon_number': 1}" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_geen_data(self):
        # lege dataset
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_07.json',
                                    stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Geen data voor top-level sleutel 'clubs'" in f1.getvalue())
        # self.assertEqual(f2.getvalue(), '')

    def test_vereniging_mutaties(self):
        # vereniging mutaties
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(83):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Nieuwe wedstrijdlocatie voor adres 'Oude pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1000] Grote Club gekoppeld aan wedstrijdlocatie 'Oude pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(53):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_08.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Wijziging van regio voor vereniging 1000: 111 --> 112" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van naam voor vereniging 1000: "Grote Club" --> "Nieuwe Grote Club"' in f2.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 1001 niet wijzigen naar onbekende regio 199" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1002 hoort bij onbekende regio 199" in f1.getvalue())
        self.assertTrue("[INFO] Wijziging van secretaris voor vereniging 1001: geen --> 100001" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van plaats voor vereniging 1000: "Stad" --> "Stadia"' in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van secretaris email voor vereniging 1000: "test@groteclub.archery" --> "andere@groteclub.archery"' in f2.getvalue())
        self.assertTrue("[INFO] Nieuwe wedstrijdlocatie voor adres 'Nieuwe pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1000] Nieuwe Grote Club ontkoppeld van wedstrijdlocatie met adres 'Oude pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())
        self.assertTrue("[INFO] Vereniging [1000] Nieuwe Grote Club gekoppeld aan wedstrijdlocatie 'Nieuwe pijlweg 1, 1234 AB Doelstad'" in f2.getvalue())

    def test_lid_mutaties(self):
        # lid mutaties
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(83):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

        lid = NhbLid.objects.get(nhb_nr=100098)
        self.assertEqual(lid.bij_vereniging.ver_nr, 1000)
        self.assertTrue(lid.is_actief_lid)
        self.assertEqual(lid.lid_tot_einde_jaar, 2020)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(45):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_09.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue("[ERROR] Lid 100001 heeft geen valide geboortedatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100099 heeft geen valide geboortedatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100100 heeft geen valide e-mail (bad_email)" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100001 heeft onbekend geslacht: X (moet zijn: M of F)" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100009 heeft geen voornaam of initials" in f1.getvalue())
        self.assertTrue("[INFO] Lid 100024: is_actief_lid nee --> ja" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: is_actief_lid: ja --> nee" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100024: para_classificatie: 'W1' --> ''" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: is_actief_lid ja --> nee (want blocked)" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: vereniging 1000 Grote Club --> 1001 HBS Dichtbij" in f2.getvalue())

        # 100099 is geen lid meer, maar moet toch nog gebruik kunnen blijven maken van de diensten
        lid = NhbLid.objects.get(nhb_nr=100098)
        self.assertNotEqual(lid.bij_vereniging, None)
        self.assertTrue(lid.is_actief_lid)
        self.assertEqual(lid.lid_tot_einde_jaar, 2020)

    def test_haakjes(self):
        # sommige leden hebben de toevoeging " (Erelid NHB)" aan hun achternaam toegevoegd
        # andere leden hebben een toevoeging achter hun voornaam: "Tineke (Tini)" - niet over klagen
        # some ontbreekt er een haakje
        # import verwijderd dit
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(36):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_10.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        # print(f2.getvalue())
        self.assertTrue("[WARNING] Lid 100999: verwijder toevoeging achternaam: 'Dienbaar (Erelid NHB)' --> 'Dienbaar'" in f2.getvalue())
        self.assertTrue("Lid 100998" not in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100997: onbalans in haakjes in " in f2.getvalue())
        self.assertTrue("[WARNING] Lid 100996: rare tekens in naam " in f2.getvalue())

    def test_datum_zonder_eeuw(self):
        # sommige leden hebben een geboortedatum zonder eeuw
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(32):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_11.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

        # print(f1.getvalue(), f2.getvalue())
        self.assertTrue("[WARNING] Lid 100999 geboortedatum gecorrigeerd van 0030-05-05 naar 1930-05-05" in f1.getvalue())
        lid = NhbLid.objects.get(nhb_nr=100999)
        self.assertEqual(lid.geboorte_datum.year, 1930)

        self.assertTrue("[WARNING] Lid 100998 geboortedatum gecorrigeerd van 0010-05-05 naar 2010-05-05" in f1.getvalue())
        lid = NhbLid.objects.get(nhb_nr=100998)
        self.assertEqual(lid.geboorte_datum.year, 2010)
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide geboortedatum: 1810-05-05" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide datum lidmaatschap: 1815-06-06" in f1.getvalue())

    def test_skip_member(self):
        # sommige leden worden niet geïmporteerd
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(34):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_12.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        with self.assertRaises(NhbLid.DoesNotExist):
            NhbLid.objects.get(nhb_nr=101711)

    def test_del_vereniging(self):
        # test het verwijderen van een lege vereniging

        # maak een test vereniging die verwijderd kan worden
        ver = NhbVereniging()
        ver.naam = "Wegisweg Club"
        ver.ver_nr = "1999"
        ver.regio = NhbRegio.objects.get(pk=116)
        ver.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(45):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_12.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Vereniging [1999] Wegisweg Club wordt nu verwijderd" in f2.getvalue())

    def test_weer_actief(self):
        # mutatie van inactief lid naar actief lid

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 110000
        lid.geslacht = "M"
        lid.voornaam = "Zweven"
        lid.achternaam = "de Tester"
        lid.email = "zdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = None
        lid.is_actief_lid = False
        lid.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(28):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_13.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 110000: vereniging geen --> 1000 Grote Club" in f2.getvalue())

        lid = NhbLid.objects.get(pk=lid.pk)
        self.assertTrue(lid.bij_vereniging is not None)
        self.assertTrue(lid.is_actief_lid)

    def test_maak_secretaris(self):
        # een lid secretaris maken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(56):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Wijziging van secretaris voor vereniging 1000: geen --> 100001 Ramon de Tester" in f2.getvalue())
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 heeft nog geen account" in f2.getvalue())

        # lid = NhbLid.objects.get(nhb_nr="100001")
        ver = NhbVereniging.objects.get(ver_nr="1000")
        functie = Functie.objects.get(rol="SEC", nhb_ver=ver)
        self.assertEqual(functie.accounts.count(), 1)

        lid = NhbLid.objects.get(nhb_nr="100024")
        ver = NhbVereniging.objects.get(ver_nr="2000")
        functie = Functie.objects.get(rol="SEC", nhb_ver=ver)
        self.assertEqual(functie.accounts.count(), 0)
        # 100024 is nog geen SEC omdat ze geen account heeft

        # maak het account van 100024 aan en probeer het nog een keer
        lid.account = self.e2e_create_account(lid.nhb_nr, 'maakt.niet.uit@gratis.net', lid.voornaam)
        lid.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(22):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan SEC functie" in f2.getvalue())

        ver = NhbVereniging.objects.get(ver_nr="2000")
        functie = Functie.objects.get(rol="SEC", nhb_ver=ver)
        self.assertEqual(functie.accounts.count(), 1)

    def test_club_1377(self):
        # een paar speciale import gevallen

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(67):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_15.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

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

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(25):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_15.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Wijziging van 'geen wedstrijden' voor vereniging 1377: False --> True" in f2.getvalue())
        self.assertTrue("[INFO] Wijziging van 'geen wedstrijden' voor vereniging 1000: True --> False" in f2.getvalue())
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

    def test_verwijder_secretaris_fail(self):
        # verwijderen van de secretaris geeft een fout

        # maak 100024 aan
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(56):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

        # maak het account van 100024 aan, zodat deze secretaris kan worden
        # maak het account van 100024 aan en probeer het nog een keer
        lid = NhbLid.objects.get(nhb_nr="100024")
        lid.account = self.e2e_create_account(lid.nhb_nr, 'maakt.niet.uit@gratis.net', lid.voornaam)
        lid.save()

        # maak 100024 secretaris
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(29):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan SEC functie" in f2.getvalue())

        # probeer 100024 te verwijderen
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(32):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_16.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())

    def test_verwijder_recordhouder_fail(self):
        # maak 100024 aan
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(56):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

        # maak een record aan op naam van 100024
        lid = NhbLid.objects.get(nhb_nr="100024")
        IndivRecord(volg_nr=1,
                    nhb_lid=lid,
                    score=1,
                    datum="2018-01-01").save()

        # probeer 100024 te verwijderen
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_16.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        self.assertFalse("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())

    def test_verwijder_score_fail(self):
        # maak 100024 aan
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(56):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

        # maak een schutterboog aan
        boog_r = BoogType.objects.get(afkorting='R')
        lid = NhbLid.objects.get(nhb_nr="100024")
        schutterboog = SchutterBoog(nhblid=lid,
                                    boogtype=boog_r)
        schutterboog.save()
        score_indiv_ag_opslaan(schutterboog, 18, 5.678, None, "")

        # probeer 100024 te verwijderen
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(40):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_16.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())
        self.assertTrue('[ERROR] Onverwachte fout bij het verwijderen van een lid' in f1.getvalue())

    def test_import_nhb_crm_dryrun(self):
        # dryrun
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(37):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_08.json',
                                    '--sim_now=2020-07-01', '--dryrun', stderr=f1, stdout=f2)
        self.assertTrue("DRY RUN" in f2.getvalue())

        with self.assert_max_queries(60):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

        ver = NhbVereniging.objects.get(ver_nr=1000)
        ver.geen_wedstrijden = True
        ver.save()

        with self.assert_max_queries(26):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_08.json',
                                    '--sim_now=2020-07-01', '--dryrun', stderr=f1, stdout=f2)
        with self.assert_max_queries(15):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_09.json',
                                    '--sim_now=2020-07-01', '--dryrun', stderr=f1, stdout=f2)
        with self.assert_max_queries(32):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json',
                                    '--sim_now=2020-07-01', '--dryrun', stderr=f1, stdout=f2)

        # maak een test vereniging die verwijderd kan worden
        ver = NhbVereniging()
        ver.naam = "Wegisweg Club"
        ver.ver_nr = "1999"
        ver.regio = NhbRegio.objects.get(pk=116)
        ver.save()
        with self.assert_max_queries(15):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_12.json',
                                    '--sim_now=2020-07-01', '--dryrun', stderr=f1, stdout=f2)

    def test_incomplete_data(self):
        # test import met een incomplete entry van een nieuw lid
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(41):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_17.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Lid 100002 heeft geen achternaam" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100007 heeft geen valide geboortedatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100008 heeft geen valide lidmaatschapsdatum" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100009 heeft geen voornaam of initials" in f1.getvalue())

    def test_bad_sim_now(self):
        # puur voor de coverage
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(0):
            management.call_command('import_nhb_crm', 'x', '--sim_now=y-m-d', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] geen valide sim_now" in f1.getvalue())

    def test_uitschrijven(self):
        # lid schrijft zich uit bij een vereniging en mag tot einde jaar diensten gebruiken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(83):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json',
                                    '--sim_now=2020-07-01', stderr=f1, stdout=f2)

        lid = NhbLid.objects.get(nhb_nr=100001)
        self.assertTrue(lid.is_actief_lid)
        self.assertEqual(lid.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(lid.bij_vereniging is not None)

        # lid 100001 heeft zich uitgeschreven tijdens het jaar
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(26):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_18.json',
                                    '--sim_now=2020-07-02', stderr=f1, stdout=f2)

        lid = NhbLid.objects.get(nhb_nr=100001)
        self.assertTrue(lid.is_actief_lid)
        self.assertEqual(lid.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(lid.bij_vereniging is not None)

        # lid 100001 is nog steeds uitgeschreven - geen verandering tot 15 januari
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(41):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_18.json',
                                    '--sim_now=2021-01-15', stderr=f1, stdout=f2)

        lid = NhbLid.objects.get(nhb_nr=100001)
        self.assertTrue(lid.is_actief_lid)
        self.assertEqual(lid.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(lid.bij_vereniging is not None)

        # lid 100001 is nog steeds uitgeschreven - verandering komt na 15 januari
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_18.json',
                                    '--dryrun', '--sim_now=2021-01-16', stderr=f1, stdout=f2)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(26):
            management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_18.json',
                                    '--sim_now=2021-01-16', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        lid = NhbLid.objects.get(nhb_nr=100001)
        self.assertFalse(lid.is_actief_lid)
        self.assertEqual(lid.lid_tot_einde_jaar, 2020)      # komt van sim_now=2020-07-01
        self.assertTrue(lid.bij_vereniging is None)

# end of file
