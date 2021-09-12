# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from .models import IndivRecord, LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from NhbStructuur.models import NhbLid
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestRecordsIndiv(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Views """

    url_indiv_all = '/records/indiv/'
    url_indiv = '/records/indiv/%s/%s/%s/%s/%s/%s/%s/'  # gesl, disc, lcat, makl, verb, para, nummer

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
        rec.naam = 'Top Schutter 2'
        rec.datum = parse_date('2016-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 1233
        rec.max_score = 5678
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
        rec.naam = 'Top Schutter 2'
        rec.datum = datetime.datetime.now()
        rec.plaats = 'Ergens Anders'
        rec.land = 'Nederland'
        rec.score = 1235
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
        rec.land = 'Nederland'
        rec.score = 249
        rec.save()

        # Record 45
        rec = IndivRecord()
        rec.volg_nr = 45
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Niet verbeterbaar record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = MATERIAALKLASSE[0][0]     # R
        rec.verbeterbaar = False
        rec.naam = 'Top Schutter 2'
        rec.datum = parse_date('2011-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 1234
        rec.max_score = 1440
        rec.save()

        # Record 46
        rec = IndivRecord()
        rec.volg_nr = 46
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
        rec.save()

        # Record 47
        rec = IndivRecord()
        rec.volg_nr = 47
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Test record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = MATERIAALKLASSE[0][0]     # R
        rec.nhb_lid = lid
        rec.naam = 'Top Schutter'
        rec.datum = parse_date('2015-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 1232
        rec.max_score = 5678
        rec.save()

        # Record 47
        rec = IndivRecord()
        rec.volg_nr = 47
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Ander soort record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = MATERIAALKLASSE[0][0]     # R
        rec.nhb_lid = lid
        rec.naam = 'Top Schutter'
        rec.datum = parse_date('2014-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 999
        rec.max_score = 1000
        rec.save()

    def test_all(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_indiv_all)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_indiv_all)

        url = self.url_indiv % ('mannen', 'outdoor', 'masters', 'recurve', 'ja', 'nvt', 46)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # para dwingt disc!=25 en lcat=U af
        url = self.url_indiv % ('mannen', '25m1pijl', 'senioren', 'recurve', 'ja', 'open', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # gewoon een goede para
        url = self.url_indiv % ('vrouwen', 'indoor', 'gecombineerd', 'recurve', 'ja', 'open', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # niet-para dwingt lcat!=U
        url = self.url_indiv % ('mannen', 'outdoor', 'gecombineerd', 'recurve', 'ja', 'nvt', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)


# end of file
