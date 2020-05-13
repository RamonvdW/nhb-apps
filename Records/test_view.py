# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from .models import IndivRecord
from NhbStructuur.models import NhbLid
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestRecordsView(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Views """

    def setUp(self):
        """ initialisatie van de test case """

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
        self.assert_html_ok(rsp)
        self.e2e_assert_other_http_commands_not_supported('/records/')

    def test_view_specifiek(self):
        rsp = self.client.get('/records/record-OD-42/')    # OD=Outdoor, 42=volg_nr
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assert_template_used(rsp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(rsp)
        self.e2e_assert_other_http_commands_not_supported('/records/record-OD-42/')
        self.assertContains(rsp, '1234 (56X)')
        self.assertContains(rsp, 'Papendal')
        self.assertContains(rsp, 'Nederland')
        self.assertContains(rsp, 'Top Schutter')

    def test_view_specifiek_overig(self):
        rsp = self.client.get('/records/record-18-43/')    # 18=Indoor, 43=volg_nr
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assert_template_used(rsp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(rsp)
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
        self.assert_template_used(rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_1args(self):
        rsp = self.client.get('/records/indiv/mannen/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assert_template_used(rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_2args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assert_template_used(rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_3args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/masters/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assert_template_used(rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_4args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/masters/recurve/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.assert_template_used(rsp, ('records/records_indiv_zoom5.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_1args_neg(self):
        rsp = self.client.get('/records/indiv/neg/')
        self.assertEqual(rsp.status_code, 404)  # 404 = Not found

    def test_view_zoek(self):
        rsp = self.client.get('/records/zoek/')
        self.assertEqual(rsp.status_code, 200)  # 200 = OK
        self.e2e_assert_other_http_commands_not_supported('/records/zoek/')

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

# end of file
