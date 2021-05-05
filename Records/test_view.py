# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from .models import IndivRecord, LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
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
        lid.sinds_datum = parse_date("1991-02-03")  # Y-M-D
        lid.save()

        lid = NhbLid()
        lid.nhb_nr = 123457
        lid.voornaam = 'Petra'
        lid.achternaam = 'Schutter'
        lid.email = 'petra@test.nl'
        lid.geboorte_datum = parse_date('1970-01-30')
        lid.woon_straatnaam = 'Arnhem'
        lid.geslacht = 'V'
        lid.sinds_datum = parse_date("1991-02-05")  # Y-M-D
        lid.save()

        # Record 42
        rec = IndivRecord()
        rec.volg_nr = 42
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Test record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = MATERIAALKLASSE[0][0]     # R
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
        rec.discipline = DISCIPLINE[1][0]   # 18
        rec.soort_record = 'Test record para'
        rec.geslacht = GESLACHT[1][0]   # V
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[1][0]   # S
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
        rec.discipline = DISCIPLINE[2][0]   # 25
        rec.soort_record = '25m'
        rec.geslacht = GESLACHT[1][0]   # V
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[3][0]   # C
        rec.materiaalklasse = 'R'       # Recurve
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

        # Record 50
        rec = IndivRecord()
        rec.volg_nr = 50
        rec.discipline = 'OD'
        rec.soort_record = '70m (72p)'
        rec.geslacht = 'V'
        rec.leeftijdscategorie = 'S'
        rec.materiaalklasse = 'R'       # Recurve
        rec.nhb_lid = lid
        rec.naam = 'Petra Schutter'
        rec.datum = parse_date('2020-02-02')
        rec.plaats = 'Bullseye'
        rec.land = 'Nederland'
        rec.score = 350
        # rec.score_notitie =
        rec.is_european_record = True
        # rec.is_world_record =
        rec.save()

        # Record 51
        rec = IndivRecord()
        rec.volg_nr = 51
        rec.discipline = 'OD'
        rec.soort_record = '70m (72p)'
        rec.geslacht = 'V'
        rec.leeftijdscategorie = 'S'
        rec.materiaalklasse = 'R'       # Recurve
        rec.nhb_lid = lid
        rec.naam = 'Petra Schutter'
        rec.datum = parse_date('2020-03-03')
        rec.plaats = 'Bullseye'
        rec.land = 'Nederland'
        rec.score = 355
        # rec.score_notitie =
        rec.is_european_record = True
        rec.is_world_record = True
        rec.save()

        self.rec = rec

        self.url_overzicht = '/records/'
        self.url_specifiek = '/records/record-%s-%s/'   # discipline (18/25/OD), volg_nr
        self.url_zoek = '/records/zoek/'
        self.url_lijst_er = '/records/lijst-er/'
        self.url_lijst_wr = '/records/lijst-wr/'

    def test_create(self):
        rec = IndivRecord.objects.all()[0]
        rec.clean_fields()      # run field validators
        rec.clean()             # run model validator
        self.assertIsNotNone(str(rec))      # use the __str__ method (only used by admin interface)

    def test_view_overzicht(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_overzicht.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_view_specifiek(self):
        url = self.url_specifiek % ('OD', 42)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, '1234 (56X)')
        self.assertContains(resp, 'Papendal')
        self.assertContains(resp, 'Nederland')
        self.assertContains(resp, 'Top Schutter')

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_view_specifiek_overig(self):
        url = self.url_specifiek % ('18', 43)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_specifiek.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, '1235')
        self.assertContains(resp, 'Ergens Anders')
        self.assertContains(resp, 'Nederland')
        self.assertContains(resp, 'Top Schutter 2')
        self.assertContains(resp, 'Para klasse:')
        self.assertContains(resp, 'Open')

    def test_view_specifiek_missing(self):
        url = self.url_specifiek % ('OD', 0)            # niet bestaand record nummer
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)  # 404 = Not found

    def test_view_zoek(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_zoek.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # te lange zoekterm
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'x' * 51})
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.e2e_assert_other_http_commands_not_supported(self.url_zoek)

    def test_view_zoek_nhb_nr(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': '123456'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK

    def test_view_zoek_unknown_nhb_nr(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': '999999'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK

    def test_view_zoek_not_nhb_nr(self):
        # let op de zoekterm: mag niet matchen met soort_record, naam, plaats of land
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'jaja'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assertContains(resp, "Niets gevonden")

    def test_view_zoek_plaats(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'Papendal'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_zoek.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Gevonden records (1)")
        self.assert_html_ok(resp)

    def test_view_zoek_plaats_case_insensitive(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'PENdal'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assertContains(resp, "Gevonden records (1)")

    def test_special(self):
        self.rec.is_european_record = True
        self.rec.is_world_record = True
        self.rec.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_er)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_special_er.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_wr)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_special_wr.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_lijst_er)
        self.e2e_assert_other_http_commands_not_supported(self.url_lijst_wr)

# end of file
