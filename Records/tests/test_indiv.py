# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from Records.definities import LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Records.models import IndivRecord
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
        sporter = Sporter(
                    lid_nr=123456,
                    voornaam='Jan',
                    achternaam='Schutter',
                    email='jan@test.nl',
                    geboorte_datum=parse_date('1970-03-03'),
                    adres_code='Papendal',
                    geslacht='M',
                    sinds_datum=parse_date("1991-02-03"))  # Y-M-D
        sporter.save()

        sporter = Sporter(
                    lid_nr=123457,
                    voornaam='Petra',
                    achternaam='Schutter',
                    email='petra@test.nl',
                    geboorte_datum=parse_date('1970-01-30'),
                    adres_code='Arnhem',
                    geslacht='V',
                    sinds_datum=parse_date("1991-02-05"))  # Y-M-D
        sporter.save()

        # Record 42
        rec = IndivRecord(
                    volg_nr=42,
                    discipline=DISCIPLINE[0][0],  # OD
                    soort_record='Test record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    naam='Top Schutter 2',
                    datum=parse_date('2016-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    score=1233,
                    max_score=5678)
        rec.save()

        # Record 43
        rec = IndivRecord(
                    volg_nr=43,
                    discipline=DISCIPLINE[1][0],   # 18
                    soort_record='Test record para',
                    geslacht=GESLACHT[1][0],   # V
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[1][0],   # S
                    materiaalklasse='R',       # Recurve
                    para_klasse='Open',
                    naam='Top Schutter 2',
                    datum=datetime.datetime.now(),
                    plaats='Ergens Anders',
                    land='Nederland',
                    score=1235)
        rec.save()

        # Record 44
        rec = IndivRecord(
                    volg_nr=44,
                    discipline=DISCIPLINE[2][0],   # 25
                    soort_record='25m',
                    geslacht=GESLACHT[1][0],   # V
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[3][0],   # C
                    materiaalklasse='R',       # Recurve
                    sporter=sporter,
                    naam='Petra Schutter',
                    datum=parse_date('2017-08-27'),
                    plaats='Nergens',
                    land='Nederland',
                    score=249)
        rec.save()

        # Record 45
        rec = IndivRecord(
                    volg_nr=45,
                    discipline=DISCIPLINE[0][0],   # OD
                    soort_record='Niet verbeterbaar record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    verbeterbaar=False,
                    naam='Top Schutter 2',
                    datum=parse_date('2011-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    score=1234,
                    max_score=1440)
        rec.save()

        # Record 46
        rec = IndivRecord(
                    volg_nr=46,
                    discipline=DISCIPLINE[0][0],   # OD
                    soort_record='Test record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    sporter=sporter,
                    naam='Top Schutter',
                    datum=parse_date('2017-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    score=1234,
                    max_score=5678,
                    x_count=56)
        rec.save()

        # Record 47
        rec = IndivRecord(
                    volg_nr=47,
                    discipline=DISCIPLINE[0][0],   # OD
                    soort_record='Test record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    sporter=sporter,
                    naam='Top Schutter',
                    datum=parse_date('2015-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    score=1232,
                    max_score=5678)
        rec.save()

        # Record 47
        rec = IndivRecord(
                    volg_nr=47,
                    discipline=DISCIPLINE[0][0],   # OD
                    soort_record='Ander soort record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    sporter=sporter,
                    naam='Top Schutter',
                    datum=parse_date('2014-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    score=999,
                    max_score=1000)
        rec.save()

        # Record 50
        rec = IndivRecord(
                    volg_nr=50,
                    discipline=DISCIPLINE[0][0],   # OD
                    soort_record='Ander soort record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[1][0],   # S
                    materiaalklasse=MATERIAALKLASSE[4][0],     # TR
                    sporter=sporter,
                    naam='Traditionele Schutter',
                    datum=parse_date('2022-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    score=999,
                    max_score=1000)
        rec.save()

    def test_all(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_indiv_all)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_filter_indiv.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        url = self.url_indiv % ('heren', 'outdoor', '50plus', 'recurve', 'ja', 'nvt', 46)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_filter_indiv.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # para dwingt disc!=25 en lcat=U af
        url = self.url_indiv % ('heren', '25m1pijl', '21plus', 'recurve', 'ja', 'open', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_filter_indiv.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # gewoon een goede para
        url = self.url_indiv % ('dames', 'indoor', 'gecombineerd', 'recurve', 'ja', 'open', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_filter_indiv.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # niet-para dwingt lcat!=U
        url = self.url_indiv % ('heren', 'outdoor', 'gecombineerd', 'recurve', 'ja', 'nvt', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_filter_indiv.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        url = self.url_indiv % ('heren', 'outdoor', '21plus', 'traditional', 'ja', 'nvt', 0)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_filter_indiv.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Traditionele Schutter')

        self.e2e_assert_other_http_commands_not_supported(self.url_indiv_all)

# end of file
