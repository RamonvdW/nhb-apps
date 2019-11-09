# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from .models import IndivRecord
from NhbStructuur.models import NhbLid
from Plein.tests import assert_html_ok, assert_other_http_commands_not_supported, assert_template_used
import datetime


class RecordsTest(TestCase):
    """ unittests voor de Records applicatie """

    def setUp(self):
        """ initializatie van de test case """

        # NhbLib
        lid = NhbLid()
        lid.nhb_nr = 123456
        lid.voornaam = 'Top'
        lid.achternaam = 'Schutter'
        lid.email = 'user@test.nl'
        lid.geboorte_datum = parse_date('1970-03-03')
        lid.woon_straatnaam = 'Papendal'
        lid.geslacht = 'M'
        lid.sinds_datum = parse_date("1991-02-03") # Y-M-D
        #lid.bij_vereniging
        lid.save()

        # Record 42
        rec = IndivRecord()
        rec.volg_nr = 42
        rec.discipline = IndivRecord.DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Test record'
        rec.geslacht = IndivRecord.GESLACHT[0][0]
        rec.leeftijdscategorie = IndivRecord.LEEFTIJDSCATEGORIE[0][0]
        rec.materiaalklasse = IndivRecord.MATERIAALKLASSE[0][0]
        # rec.materiaalklasse_overig =
        rec.nhb_lid = lid
        rec.naam = 'Top Schutter'
        rec.datum = datetime.datetime.now()
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 1234
        # rec.score_notitie =
        # rec.is_national_record =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        # Record 43
        rec = IndivRecord()
        rec.volg_nr = 43
        rec.discipline = IndivRecord.DISCIPLINE[1][0]
        rec.soort_record = 'Test record overig'
        rec.geslacht = IndivRecord.GESLACHT[1][0]
        rec.leeftijdscategorie = IndivRecord.LEEFTIJDSCATEGORIE[1][0]   # 18
        rec.materiaalklasse = 'O'       # overig
        rec.materiaalklasse_overig = 'Overige Test'
        # rec.nhb_lid =
        rec.naam = 'Top Schutter 2'
        rec.datum = datetime.datetime.now()
        rec.plaats = 'Ergens Anders'
        rec.land = 'Nederland'
        rec.score = 1235
        # rec.score_notitie =
        # rec.is_national_record =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        # TODO: add record with reference to nhb_lid

    def test_create(self):
        rec = IndivRecord.objects.all()[0]
        rec.clean_fields()      # run field validators
        rec.clean()             # run model validator
        self.assertIsNotNone(str(rec))      # use the __str__ method (only used by admin interface)

    def test_view_overzicht(self):
        rsp = self.client.get('/records/')
        self.assertEqual(rsp.status_code, 200)
        assert_html_ok(self, rsp)
        assert_other_http_commands_not_supported(self, '/records/')

    def test_view_specifiek(self):
        rsp = self.client.get('/records/record-OD-42/')    # OD=Outdoor, 42=volg_nr
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        assert_other_http_commands_not_supported(self, '/records/record-OD-42/')
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_specifiek_overig(self):
        rsp = self.client.get('/records/record-18-43/')    # 18=Indoor, 43=volg_nr
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_specifiek_missing(self):
        rsp = self.client.get('/records/record-OD-0/')    # niet bestaand record nummer
        self.assertEqual(rsp.status_code, 404)

    def test_view_zoom_0args(self):
        rsp = self.client.get('/records/indiv/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_1args(self):
        rsp = self.client.get('/records/indiv/mannen/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_2args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_3args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/masters/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('records/records_indiv_zoom1234.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_4args(self):
        rsp = self.client.get('/records/indiv/mannen/outdoor/masters/recurve/')
        self.assertEqual(rsp.status_code, 200)
        assert_template_used(self, rsp, ('records/records_indiv_zoom5.dtl', 'plein/site_layout.dtl'))
        assert_html_ok(self, rsp)
        # TODO: check extra zaken via template context (rsp.context)

    def test_view_zoom_1args_neg(self):
        rsp = self.client.get('/records/indiv/neg/')
        self.assertEqual(rsp.status_code, 404)

    def test_view_zoek(self):
        rsp = self.client.get('/records/zoek/')
        self.assertEqual(rsp.status_code, 200)
        assert_other_http_commands_not_supported(self, '/records/zoek/')

    def test_view_zoek_nhb_nr(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': '123456'})
        self.assertEqual(rsp.status_code, 200)

    def test_view_zoek_unknown_nhb_nr(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': '999999'})
        self.assertEqual(rsp.status_code, 200)

    def test_view_zoek_not_nhb_nr(self):
        # let op de zoekterm: mag niet matchen met soort_record, naam, plaats of land
        rsp = self.client.get('/records/zoek/', {'zoekterm': 'jaja'})
        self.assertEqual(rsp.status_code, 200)

    def test_view_zoek_plaats(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': 'Papendal'})
        self.assertEqual(rsp.status_code, 200)

    def test_view_zoek_plaats_case_insensitive(self):
        rsp = self.client.get('/records/zoek/', {'zoekterm': 'paPENdal'})
        self.assertEqual(rsp.status_code, 200)

# end of file
