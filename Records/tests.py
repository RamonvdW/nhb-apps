# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.utils.dateparse import parse_date
from .models import IndivRecord
from NhbStructuur.models import NhbLid
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
import datetime
import io

class TestRecords(TestCase):
    """ unittests voor de Records applicatie """

    def setUp(self):
        """ initializatie van de test case """

        # NhbLib
        lid = NhbLid()
        lid.nhb_nr = 123456
        lid.voornaam = 'Jan'
        lid.achternaam = 'Schutter'
        lid.email = 'jan@test.nl'
        lid.geboorte_datum = parse_date('1970-03-03')
        lid.woon_straatnaam = 'Papendal'
        lid.geslacht = 'M'
        lid.sinds_datum = parse_date("1991-02-03") # Y-M-D
        #lid.bij_vereniging
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 123457
        lid.voornaam = 'Petra'
        lid.achternaam = 'Schutter'
        lid.email = 'petra@test.nl'
        lid.geboorte_datum = parse_date('1970-01-30')
        lid.woon_straatnaam = 'Arnhem'
        lid.geslacht = 'V'
        lid.sinds_datum = parse_date("1991-02-05") # Y-M-D
        #lid.bij_vereniging
        lid.save()

        # Record 42
        rec = IndivRecord()
        rec.volg_nr = 42
        rec.discipline = IndivRecord.DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Test record'
        rec.geslacht = IndivRecord.GESLACHT[0][0]   # M
        rec.leeftijdscategorie = IndivRecord.LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = IndivRecord.MATERIAALKLASSE[0][0]     # R
        # rec.materiaalklasse_overig =
        rec.nhb_lid = lid
        rec.naam = 'Top Schutter'
        rec.datum = parse_date('2017-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 1234
        rec.max_score = 5678
        rec.x_count = 56
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        # Record 43
        rec = IndivRecord()
        rec.volg_nr = 43
        rec.discipline = IndivRecord.DISCIPLINE[1][0]   # 18
        rec.soort_record = 'Test record para'
        rec.geslacht = IndivRecord.GESLACHT[1][0]   # V
        rec.leeftijdscategorie = IndivRecord.LEEFTIJDSCATEGORIE[1][0]   # S
        rec.materiaalklasse = 'R'       # Recurve
        rec.para_klasse = 'Open'
        # rec.nhb_lid =
        rec.naam = 'Top Schutter 2'
        rec.datum = datetime.datetime.now()
        rec.plaats = 'Ergens Anders'
        rec.land = 'Nederland'
        rec.score = 1235
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        # Record 44
        rec = IndivRecord()
        rec.volg_nr = 44
        rec.discipline = IndivRecord.DISCIPLINE[2][0]   # 25
        rec.soort_record = '25m'
        rec.geslacht = IndivRecord.GESLACHT[1][0]   # V
        rec.leeftijdscategorie = IndivRecord.LEEFTIJDSCATEGORIE[3][0]   # C
        rec.materiaalklasse = 'R'       # Recurve
        #rec.para_klasse =
        rec.nhb_lid = lid
        rec.naam = 'Petra Schutter'
        rec.datum = parse_date('2017-08-27')
        rec.plaats = 'Nergens'
        rec.land = 'Niederland'
        rec.score = 249
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

    def test_create(self):
        rec = IndivRecord.objects.all()[0]
        rec.clean_fields()      # run field validators
        rec.clean()             # run model validator
        self.assertIsNotNone(str(rec))      # use the __str__ method (only used by admin interface)

    def test_view_overzicht(self):
        rsp = self.client.get('/records/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_html_ok(self, rsp)
        assert_other_http_commands_not_supported(self, '/records/')

    def test_view_specifiek(self):
        rsp = self.client.get('/records/record-OD-42/')    # OD=Outdoor, 42=volg_nr
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        assert_other_http_commands_not_supported(self, '/records/record-OD-42/')
        self.assertContains(rsp, '1234 (56X)')
        self.assertContains(rsp, 'Papendal')
        self.assertContains(rsp, 'Nederland')
        self.assertContains(rsp, 'Top Schutter')

    def test_view_specifiek_overig(self):
        rsp = self.client.get('/records/record-18-43/')    # 18=Indoor, 43=volg_nr
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        self.assertContains(rsp, '1235')
        self.assertContains(rsp, 'Ergens Anders')
        self.assertContains(rsp, 'Nederland')
        self.assertContains(rsp, 'Top Schutter 2')
        self.assertContains(rsp, 'Para klasse:')
        self.assertContains(rsp, 'Open')

    def test_view_specifiek_missing(self):
        rsp = self.client.get('/records/record-OD-0/')    # niet bestaand record nummer
        self.assertEqual(rsp.status_code, 404)  # 404 = Not found

    def test_view_zoom_0args(self):
        rsp = self.client.get('/records/indiv/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_1args(self):
        rsp = self.client.get('/records/indiv/mannen/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_2args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_3args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/masters/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_4args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/masters/recurve/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_template_used(self, rsp, ('records/records_indiv_zoom5.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_1args_neg(self):
        rsp = self.client.get('/records/indiv/neg/')
        self.assertEqual(rsp.status_code, 404)  # 404 = Not found

    def test_view_zoek(self):
        rsp = self.client.get('/records/zoek/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        assert_other_http_commands_not_supported(self, '/records/zoek/')

    def test_view_zoek_nhb_nr(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': '123456'})
        self.assertEqual(rsp.status_code, 200)  # 200 = OK

    def test_view_zoek_unknown_nhb_nr(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': '999999'})
        self.assertEqual(rsp.status_code, 200)  # 200 = OK

    def test_view_zoek_not_nhb_nr(self):
        # let op de zoekterm: mag niet matchen met soort_record, naam, plaats of land
        rsp = self.client.get('/records/zoek/', {'zoekterm': 'jaja'})
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assertContains(rsp, "Niets gevonden")

    def test_view_zoek_plaats(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': 'Papendal'})
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assertContains(rsp, "Gevonden records (1)")

    def test_view_zoek_plaats_case_insensitive(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': 'PENdal'})
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assertContains(rsp, "Gevonden records (1)")

    def test_import_records(self):
        # afhandelen niet bestaand bestand
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './notexisting.json', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue().startswith('[ERROR] Kan bestand ./notexisting.json niet lezen ('))
        self.assertEqual(f2.getvalue(), '')

    def test_import_records_01(self):
        # kapot bestand
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_01.json', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue().startswith("[ERROR] Probleem met het JSON formaat in bestand './Records/management/testfiles/testfile_01.json'"))
        self.assertEqual(f2.getvalue(), '')

    def test_import_records_02(self):
        # onverwacht tabblad
        # verkeerde headers
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_02.json', '--dryrun', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Niet ondersteunde tabblad naam: Onbekende blad naam' in f1.getvalue())
        self.assertTrue('[ERROR] Kolom headers kloppen niet voor range Data team' in f1.getvalue())
        self.assertTrue('Samenvatting: ' in f2.getvalue())
        self.assertTrue('\nDRY RUN\n' in f2.getvalue())
        self.assertTrue('\nDone\n' in f2.getvalue())

    def test_import_records_03(self):
        # bestand met alleen headers, geen data
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_03.json', stderr=f1, stdout=f2)
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue('\nDone\n' in f2.getvalue())

    def test_import_records_04(self):
        # incompleet bestand
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_04.json', stderr=f1, stdout=f2)
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertTrue('[INFO] Record OD-1 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record OD-2 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 18-1 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 18-2 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 25-1 toegevoegd' in f2.getvalue())
        self.assertTrue('[INFO] Record 25-2 toegevoegd' in f2.getvalue())
        self.assertTrue('; 1 ongewijzigd;' in f2.getvalue())    # 25-44

    def test_import_records_05(self):
        # all kinds of errors
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_05.json', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Foute index (geen nummer): 'XA' in" in f1.getvalue())
        self.assertTrue("Fout geslacht: 'XB' + Foute leeftijdscategorie': 'XC' + Foute materiaalklasse: 'XD' + Foute discipline: 'XE' op blad 'OD' + Fout in soort_record: 'XF' is niet bekend + Fout in para klasse: 'XG' is niet bekend + Fout in pijlen: 'XI' is geen nummer + Fout NHB nummer: 'XJ' + Fout in score 'XK' + Fout in X-count 'XL' is geen getal + Foute tekst in Ook ER: 'XM' + Foute tekst in Ook WR: 'XN' in " in f1.getvalue())
        obj = IndivRecord.objects.get(discipline='18', volg_nr=2)
        self.assertEqual(obj.leeftijdscategorie, 'U')

    def test_import_records_06(self):
        # all kinds of changes
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_06.json', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())
        self.assertTrue("Wijzigingen voor record OD-42:" in f2.getvalue())
        self.assertTrue("geslacht: 'M' --> 'V'" in f2.getvalue())
        self.assertTrue("leeftijdscategorie: 'M' --> 'C'" in f2.getvalue())
        self.assertTrue("materiaalklasse: 'R' --> 'C'" in f2.getvalue())
        self.assertTrue("soort_record: 'Test record' --> '60m'" in f2.getvalue())
        self.assertTrue("para_klasse: '' --> 'W1'" in f2.getvalue())
        self.assertTrue("max_score: 5678 --> 1200" in f2.getvalue())
        self.assertTrue("nhb_lid: 123457 Petra Schutter [V, 1970] --> 123456 Jan Schutter [M, 1970]" in f2.getvalue())
        self.assertTrue("naam: 'Top Schutter' --> 'Jan Schutter'" in f2.getvalue())
        self.assertTrue("datum: 2017-08-27 --> 1901-01-01" in f2.getvalue())
        self.assertTrue("plaats: 'Papendal' --> 'Elbonia'" in f2.getvalue())
        self.assertTrue("land: 'Nederland' --> 'Mudland'" in f2.getvalue())
        self.assertTrue("score: 1234 --> 1432" in f2.getvalue())
        self.assertTrue("x_count: 56 --> 21" in f2.getvalue())
        self.assertTrue("is_european_record: False --> True" in f2.getvalue())
        self.assertTrue("is_world_record: False --> True" in f2.getvalue())
        self.assertTrue("score_notitie: '' --> 'Geen notitie'" in f2.getvalue())

        self.assertTrue("Wijzigingen voor record 25-44:" in f2.getvalue())
        self.assertTrue("score_notitie: '' --> 'gedeeld'" in f2.getvalue())

    def test_import_records_07(self):
        # onbekend NHB nummer
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_07.json', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())
        self.assertTrue("NHB nummer niet bekend: '999999' " in f1.getvalue())

    def test_import_records_08(self):
        # foute datums
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_records', './Records/management/testfiles/testfile_08.json', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '6-30-2017' in ['2'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-6-17' in ['3'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-617' in ['4'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30/6/2017' in ['5'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-6-1917' in ['6'," in f1.getvalue())
        self.assertTrue("[ERROR] Fout in datum: '30-6-2099' in ['7'," in f1.getvalue())

# end of file
