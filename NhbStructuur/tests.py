# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Account.models import Account
from .migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Functie.models import Functie
import datetime
from dateutil.relativedelta import relativedelta
import io


class TestNhbStructuur(TestCase):
    """ unit tests voor de NhbStructuur applicatie """

    def setUp(self):
        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
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
        lid.save()

        usermodel = get_user_model()
        usermodel.objects.create_user('100001', 'rdetester@gmail.not', 'wachtwoord')
        account = Account.objects.get(username='100001')
        account.nhblid = lid
        account.save()
        self.account_100001 = account

    def test_rayons(self):
        self.assertEqual(NhbRayon.objects.all().count(), 4)
        rayon = NhbRayon.objects.get(pk=3)
        self.assertEqual(rayon.naam, "Rayon 3")
        self.assertEqual(rayon.geografisch_gebied, "Oost Brabant en Noord Limburg")
        self.assertIsNotNone(str(rayon))

    def test_regios(self):
        self.assertEqual(NhbRegio.objects.all().count(), 17)
        regio = NhbRegio.objects.get(pk=111)
        self.assertEqual(regio.naam, "Regio 111")
        self.assertIsNotNone(str(regio))

    def test_lid(self):
        lid = NhbLid.objects.get(nhb_nr="100001")
        self.assertIsNotNone(lid)
        self.assertIsNotNone(str(lid))

        lid.clean_fields()      # run field validators
        lid.clean()             # run model validator

        # test: geboortejaar in de toekomst
        now = datetime.datetime.now()
        lid.geboorte_datum = now - relativedelta(years=1)   # avoid leap-year issue
        with self.assertRaises(ValidationError):
            lid.clean_fields()

        # test: geboortejaar te ver in het verleden
        lid.geboorte_datum = datetime.date(year=1890, month=1, day=1)
        with self.assertRaises(ValidationError):
            lid.clean_fields()

        # test: sinds_datum (2010) te dicht op geboortejaar
        lid.geboorte_datum = datetime.date(year=2009, month=1, day=1)
        with self.assertRaises(ValidationError):
            lid.clean()

        lid.sinds_datum = datetime.date(year=2100, month=11, day=12)
        with self.assertRaises(ValidationError):
            lid.clean_fields()

        self.assertEqual(lid.voornaam, "Ramon")
        self.assertEqual(lid.achternaam, "de Tester")
        self.assertEqual(lid.volledige_naam(), "Ramon de Tester")

    def test_vereniging(self):
        ver = NhbVereniging.objects.all()[0]
        self.assertIsNotNone(str(ver))
        ver.clean_fields()      # run validators
        ver.clean()             # run model validator

    def test_import_nhb_crm_00_file_not_found(self):
        # afhandelen niet bestaand bestand
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/notexisting.json', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue().startswith('[ERROR] Bestand kan niet gelezen worden'))
        self.assertEqual(f2.getvalue(), '')

    def test_import_nhb_crm_01_bad_json(self):
        # afhandelen slechte/lege JSON file
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_01.json', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue().startswith('[ERROR] Probleem met het JSON formaat in bestand'))
        self.assertEqual(f2.getvalue(), '')

    def test_import_nhb_crm_02_toplevel_structuur_afwezig(self):
        # top-level keys afwezig
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_02.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Verplichte sleutel 'rayons' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'regions' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'clubs' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'members' niet aanwezig in de 'top-level' data" in f1.getvalue())
        self.assertEqual(f2.getvalue(), '')

    def test_import_nhb_crm_03(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())
        self.assertTrue("[WARNING] Vereniging 1000 (Grote Club) heeft geen secretaris!" in f1.getvalue())
        self.assertTrue("[ERROR] Kan secretaris 1 van vereniging 1001 niet vinden" in f1.getvalue())
        self.assertTrue("[INFO] Wijziging naam rayon 4: 'Rayon 4' --> 'Rayon 99'" in f2.getvalue())
        self.assertTrue("[INFO] Wijziging naam regio 101: 'Regio 101' --> 'Regio 99'" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: naam Ramon de Tester --> Voornaam van der Achternaam" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 e-mail: 'rdetester@gmail.not' --> ''" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geslacht: M --> V" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001 geboortedatum: 1972-03-04 --> 2000-02-01" in f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: sinds_datum: 2010-11-12 --> 2000-01-01" in f2.getvalue())

    def test_import_nhb_crm_04_unicode_error(self):
        # UnicodeDecodeError
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_04.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Bestand heeft unicode problemen ('rawunicodeescape' codec can't decode bytes in position 180-181: truncated" in f1.getvalue())
        self.assertEqual(f2.getvalue(), '')

    def test_import_nhb_crm_05_missing_keys(self):
        # missing/extra keys
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_05.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'rayon' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'regio' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'club' data" in f1.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'member' data" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'rayon' data: ['name1']" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'regio' data: ['name2']" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'club' data: ['name3']" in f1.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'member' data: ['name4']" in f1.getvalue())
        #self.assertEqual(f2.getvalue(), '')

    def test_import_nhb_crm_06_extra_geo_structuur(self):
        # extra rayon/regio
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_06.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Onbekend rayon {'rayon_number': 0, 'name': 'Rayon 0'}" in f1.getvalue())
        self.assertTrue("[ERROR] Onbekende regio {'region_number': 0, 'name': 'Regio 0', 'rayon_number': 1}" in f1.getvalue())
        #self.assertEqual(f2.getvalue(), '')

    def test_import_nhb_crm_07_geen_data(self):
        # lege dataset
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_07.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Geen data voor top-level sleutel 'clubs'" in f1.getvalue())
        self.assertEqual(f2.getvalue(), '')

    def test_import_nhb_crm_08_vereniging_mutaties(self):
        # vereniging mutaties
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json', stderr=f1, stdout=f2)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_08.json', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())
        self.assertTrue("[INFO] Wijziging van regio voor vereniging 1000: 111 --> 112" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van naam voor vereniging 1000: "Grote Club" --> "Nieuwe Grote Club"' in f2.getvalue())
        self.assertTrue("[ERROR] Kan vereniging 1001 niet wijzigen naar onbekende regio 199" in f1.getvalue())
        self.assertTrue("[ERROR] Vereniging 1002 hoort bij onbekende regio 199" in f1.getvalue())
        self.assertTrue("[INFO] Wijziging van secretaris voor vereniging 1001: geen --> 100001" in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van plaats voor vereniging 1000: "Stad" --> "Stadia"' in f2.getvalue())
        self.assertTrue('[INFO] Wijziging van contact email voor vereniging 1000: "test@groteclub.archery" --> "andere@groteclub.archery"' in f2.getvalue())

    def test_import_nhb_crm_09_lid_mutaties(self):
        # lid mutaties
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json', stderr=f1, stdout=f2)
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_09.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Lid 100001 heeft geen valide geboortedatum", f1.getvalue())
        self.assertTrue("[ERROR] Lid 100001 heeft onbekend geslacht: X (moet zijn: M of F)", f1.getvalue())
        self.assertTrue("[WARNING] Lid 100009 heeft geen voornaam of initials" in f1.getvalue())
        self.assertTrue("[INFO] Lid 100009 wordt overgeslagen (geen valide geboortedatum, maar toch blocked)" in f2.getvalue())
        self.assertTrue("[ERROR] Lid 100009 heeft geen valide lidmaatschapsdatum", f1.getvalue())
        self.assertTrue("[ERROR] Lid 100009 heeft geen valide email (geen)", f1.getvalue())
        self.assertTrue("[INFO] Lid 100024: is_actief_lid nee --> ja", f2.getvalue())
        self.assertTrue("[INFO] Lid 100001: is_actief_lid: ja --> nee", f2.getvalue())
        self.assertTrue("[INFO] Lid 100024: para_classificatie: 'W1' --> ''", f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: is_actief_lid ja --> nee (want blocked)", f2.getvalue())
        self.assertTrue("[INFO] Lid 100025: vereniging 1000 Grote Club --> 1001 HBS Dichtbij", f2.getvalue())

    def test_import_crm_10_erelid(self):
        # sommige leden hebben de toevoegen " (Erelid NHB)" aan hun achternaam toegevoegd
        # import verwijderd dit
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_10.json', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Lid 100999: verwijder toevoeging erelid: 'Dienbaar (Erelid NHB)' --> 'Dienbaar'" in f2.getvalue())

    def test_import_crm_11_datum_zonder_eeuw(self):
        # sommige leden hebben een geboortedatum zonder eeuw
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_11.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Lid 100999 heeft geen valide geboortedatum: 0030-05-05" in f1.getvalue())
        lid = NhbLid.objects.get(nhb_nr=100999)
        self.assertEqual(lid.geboorte_datum.year, 1930)
        self.assertTrue("[ERROR] Lid 100998 heeft geen valide geboortedatum: 0010-05-05" in f1.getvalue())
        lid = NhbLid.objects.get(nhb_nr=100998)
        self.assertEqual(lid.geboorte_datum.year, 2010)
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide geboortedatum: 1810-05-05" in f1.getvalue())
        self.assertTrue("[ERROR] Lid 100997 heeft geen valide lidmaatschapdatum: 1815-06-06" in f1.getvalue())

    def test_import_crm_12_skip_member(self):
        # sommige leden worden niet geimporteerd
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_12.json', stderr=f1, stdout=f2)
        with self.assertRaises(NhbLid.DoesNotExist):
            lid = NhbLid.objects.get(nhb_nr=101711)

    def test_import_crm_12_del_vereniging(self):
        # test het verwijderen van een lege vereniging

        # maak een test vereniging die verwijderd kan worden
        ver = NhbVereniging()
        ver.naam = "Wegisweg Club"
        ver.nhb_nr = "1999"
        ver.regio = NhbRegio.objects.get(pk=116)
        ver.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_12.json', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Vereniging 1999 Wegisweg Club wordt nu verwijderd" in f2.getvalue())

    def test_import_crm_13_inactief(self):
        # inactief maken nadat al geen lid meer van een vereniging

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
        lid.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_13.json', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Lid 110000: vereniging geen --> 1000 Grote Club" in f2.getvalue())

    def test_import_crm_14_maak_cwz(self):
        # secretaris-lid cwz maken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Wijziging van secretaris voor vereniging 1000: geen --> 100001 Ramon de Tester" in f2.getvalue())
        self.assertTrue("[WARNING] Secretaris 100024 van vereniging 2000 heeft nog geen account" in f2.getvalue())

        lid = NhbLid.objects.get(nhb_nr="100001")
        ver = NhbVereniging.objects.get(nhb_nr="1000")
        functie = Functie.objects.get(rol="CWZ", nhb_ver=ver)
        self.assertEqual(len(functie.account_set.all()), 1)

        lid = NhbLid.objects.get(nhb_nr="100024")
        ver = NhbVereniging.objects.get(nhb_nr="2000")
        functie = Functie.objects.get(rol="CWZ", nhb_ver=ver)
        self.assertEqual(len(functie.account_set.all()), 0)
        # 100024 is nog geen CWZ omdat ze geen account heeft

        # maak het account van 100024 aan en probeer het nog een keer
        usermodel = get_user_model()
        usermodel.objects.create_user('100024', 'maakt.niet.uit@gratis.net', 'wachtwoord')
        account = Account.objects.get(username='100024')
        account.nhblid = lid
        account.save()

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan CWZ functie" in f2.getvalue())

        lid = NhbLid.objects.get(nhb_nr="100024")
        ver = NhbVereniging.objects.get(nhb_nr="2000")
        functie = Functie.objects.get(rol="CWZ", nhb_ver=ver)
        self.assertEqual(len(functie.account_set.all()), 1)

    def test_import_crm_15(self):
        # een paar speciale import gevallen

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_15.json', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())

        # verifieer verwijderen van "(geen deelname wedstrijden)" uit de naam
        ver = NhbVereniging.objects.get(nhb_nr=1377)
        self.assertEqual(ver.naam, "Persoonlijk")

    def test_import_crm_16_verwijder_secretaris_fail(self):
        # verwijderen van de secretaris geeft een fout

        # maak 100024 aan
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json', stderr=f1, stdout=f2)
        lid = NhbLid.objects.get(nhb_nr="100024")

        # maak het account van 100024 aan, zodat deze secretaris kan worden
        usermodel = get_user_model()
        usermodel.objects.create_user('100024', 'maakt.niet.uit@gratis.net', 'wachtwoord')
        account = Account.objects.get(username='100024')
        account.nhblid = lid
        account.save()

        # maak 100024 secretaris
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json', stderr=f1, stdout=f2)
        self.assertEqual(f1.getvalue(), '')
        self.assertTrue("[INFO] Secretaris 100024 van vereniging 2000 is gekoppeld aan CWZ functie" in f2.getvalue())

        # probeer 100024 te verwijderen
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_16.json', stderr=f1, stdout=f2)

        # verwijderen van leden staat op dit moment uit - zie import commando
        #self.assertTrue("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())
        #self.assertTrue("[ERROR] Onverwachte fout bij het verwijderen van een lid: " in f1.getvalue())
        self.assertFalse("[INFO] Lid 100024 Voornaam van der Achternaam [V, 2000] wordt nu verwijderd" in f2.getvalue())

    def test_import_nhb_crm_dryrun(self):
        # dryrun
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_08.json', '--dryrun', stderr=f1, stdout=f2)
        self.assertTrue("DRY RUN" in f2.getvalue())

        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_03.json', stderr=f1, stdout=f2)
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_08.json', '--dryrun', stderr=f1, stdout=f2)
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_09.json', '--dryrun', stderr=f1, stdout=f2)
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_14.json', '--dryrun', stderr=f1, stdout=f2)

        # maak een test vereniging die verwijderd kan worden
        ver = NhbVereniging()
        ver.naam = "Wegisweg Club"
        ver.nhb_nr = "1999"
        ver.regio = NhbRegio.objects.get(pk=116)
        ver.save()
        management.call_command('import_nhb_crm', './NhbStructuur/management/testfiles/testfile_12.json', '--dryrun', stderr=f1, stdout=f2)

    def test_bereken_wedstrijdleeftijd(self):
        lid = NhbLid.objects.get(nhb_nr=100001)     # geboren 1972; bereikt leeftijd 40 in 2012
        self.assertEqual(lid.bereken_wedstrijdleeftijd(2012), 40)

# end of file
