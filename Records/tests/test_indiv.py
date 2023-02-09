# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from Records.models import IndivRecord, LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestRecordsIndiv(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Views """

    url_indiv_all = '/records/indiv/'
    url_indiv = '/records/indiv/%s/%s/%s/%s/%s/%s/%s/'  # gesl, disc, lcat, makl, verb, para, nummer

    def setUp(self):
        """ initialisatie van de test case """

        # leden
        sporter = Sporter()
        sporter.lid_nr = 123456
        sporter.voornaam = 'Jan'
        sporter.achternaam = 'Schutter'
        sporter.email = 'jan@test.nl'
        sporter.geboorte_datum = parse_date('1970-03-03')
        sporter.woon_straatnaam = 'Papendal'
        sporter.geslacht = 'M'
        sporter.sinds_datum = parse_date("1991-02-03")  # Y-M-D
        sporter.save()

        sporter = Sporter()
        sporter.lid_nr = 123457
        sporter.voornaam = 'Petra'
        sporter.achternaam = 'Schutter'
        sporter.email = 'petra@test.nl'
        sporter.geboorte_datum = parse_date('1970-01-30')
        sporter.woon_straatnaam = 'Arnhem'
        sporter.geslacht = 'V'
        sporter.sinds_datum = parse_date("1991-02-05")  # Y-M-D
        sporter.save()

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
        rec.sporter = sporter
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
        rec.sporter = sporter
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
        rec.sporter = sporter
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
        rec.sporter = sporter
        rec.naam = 'Top Schutter'
        rec.datum = parse_date('2014-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 999
        rec.max_score = 1000
        rec.save()

        # Record 50
        rec = IndivRecord()
        rec.volg_nr = 50
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Ander soort record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[1][0]   # S
        rec.materiaalklasse = MATERIAALKLASSE[4][0]     # TR
        rec.sporter = sporter
        rec.naam = 'Traditionele Schutter'
        rec.datum = parse_date('2022-08-27')
        rec.plaats = 'Papendal'
        rec.land = 'Nederland'
        rec.score = 999
        rec.max_score = 1000
        rec.save()

        # Record 51
        rec = IndivRecord()
        rec.volg_nr = 50
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Ander soort record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[1][0]   # S
        rec.materiaalklasse = MATERIAALKLASSE[5][0]     # IB
        rec.sporter = sporter
        rec.naam = 'Instinctieve Schutter'
        rec.datum = parse_date('2020-08-27')
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

        url = self.url_indiv % ('mannen', 'outdoor', 'senioren', 'traditional', 'ja', 'nvt', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Traditionele Schutter')

        url = self.url_indiv % ('mannen', 'outdoor', 'senioren', 'instinctive-bow', 'ja', 'nvt', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_indiv.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Instinctieve Schutter')

        self.e2e_assert_other_http_commands_not_supported(self.url_indiv_all)

# end of file
