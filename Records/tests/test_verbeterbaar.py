# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from Records.definities import LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Records.models import IndivRecord, BesteIndivRecords
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestRecordsVerbeterbaar(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Views """

    url_kies_disc = '/records/indiv/verbeterbaar/'
    url_verbeterbaar = '/records/indiv/verbeterbaar/%s/%s/%s/%s/'     # disc, makl, lcat, gesl

    def setUp(self):
        """ initialisatie van de test case """

        # leden
        sporter = Sporter(
                    lid_nr=123456,
                    voornaam='Janynke',
                    achternaam='Schutter',
                    email='janynke@test.nl',
                    geboorte_datum=parse_date('1970-03-03'),
                    adres_code='Papendal',
                    geslacht='V',
                    sinds_datum=parse_date("1991-02-03"))  # Y-M-D
        sporter.save()
        self.sporter_123456 = sporter

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
        self.sporter_123457 = sporter

        # Record 42
        rec = IndivRecord(
                    volg_nr=42,
                    discipline=DISCIPLINE[0][0],   # OD
                    soort_record='Test record',
                    geslacht=GESLACHT[0][0],   # M
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[0][0],   # M
                    materiaalklasse=MATERIAALKLASSE[0][0],     # R
                    # materiaalklasse_overig
                    sporter=sporter,
                    naam='Top Schutter',
                    datum=parse_date('2017-08-27'),
                    plaats='Papendal',
                    land='Nederland',
                    # score_notitie
                    # is_european_record
                    # is_world_record
                    score=1234,
                    max_score=5678,
                    x_count=56)
        rec.save()

        # Record 43
        rec = IndivRecord(
                    volg_nr=43,
                    discipline=DISCIPLINE[1][0],   # 18
                    soort_record='Test record para',
                    geslacht=GESLACHT[1][0],   # Vrouw
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[1][0],   # Senior
                    materiaalklasse='R',       # Recurve
                    para_klasse='Open',
                    # sporter
                    naam='Top Schutter 2',
                    datum=datetime.datetime.now(),
                    plaats='Ergens Anders',
                    land='Nederland',
                    # score_notitie
                    # is_european_record
                    # is_world_record
                    score=1235)
        rec.save()

        beste = BesteIndivRecords(
                    volgorde=1,
                    discipline=rec.discipline,
                    soort_record=rec.soort_record,
                    geslacht=rec.geslacht,
                    leeftijdscategorie=rec.leeftijdscategorie,
                    materiaalklasse=rec.materiaalklasse,
                    para_klasse=rec.para_klasse,
                    beste=rec)
        beste.save()

        # Record 44
        rec = IndivRecord(
                    volg_nr=44,
                    discipline=DISCIPLINE[2][0],   # 25
                    soort_record='25m',
                    geslacht=GESLACHT[1][0],   # Vrouw
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[3][0],   # Cadet
                    materiaalklasse='R',       # Recurve
                    # para_klasse
                    sporter=self.sporter_123456,
                    naam='Petra Schutter',
                    datum=parse_date('2017-08-27'),
                    plaats='Nergens',
                    land='Niederland',
                    # score_notitie
                    # is_european_record
                    # is_world_record
                    score=249)
        rec.save()

        # Record 45
        rec = IndivRecord(
                    volg_nr=45,
                    discipline=DISCIPLINE[2][0],   # 25
                    soort_record='25m',
                    geslacht=GESLACHT[1][0],   # Vrouw
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[3][0],   # Cadet
                    materiaalklasse='R',      # Recurve
                    # para_klasse
                    sporter=self.sporter_123457,
                    naam='Petra Schutter',
                    datum=parse_date('2017-08-30'),
                    plaats='Narguns',
                    land='Niederland',
                    # score_notitie
                    # is_european_record
                    # is_world_record
                    score=250)
        rec.save()

        beste = BesteIndivRecords(
                    volgorde=1,
                    discipline=rec.discipline,
                    soort_record=rec.soort_record,
                    geslacht=rec.geslacht,
                    leeftijdscategorie=rec.leeftijdscategorie,
                    materiaalklasse=rec.materiaalklasse,
                    para_klasse=rec.para_klasse,
                    beste=rec)
        beste.save()
        self.beste = beste

    def test_xtra(self):
        self.assertTrue(str(self.beste) != "")

    def test_kies_disc(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies_disc)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar_kies_disc.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        self.assertEqual(3, len(urls))      # indoor, 25m1pijl, outdoor

        self.e2e_assert_other_http_commands_not_supported(self.url_kies_disc)

    def test_basics(self):
        url = self.url_verbeterbaar % ("outdoor", 'alle', 'alle', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar.dtl', 'design/site_layout.dtl'))

        url = self.url_verbeterbaar % ("indoor", 'alle', 'alle', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar.dtl', 'design/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(url)

        urls = self.extract_all_urls(resp)
        self.assertTrue('/records/record-18-43/' in urls)

        url = self.url_verbeterbaar % ("25m1pijl", 'alle', 'alle', 'alle')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar.dtl', 'design/site_layout.dtl'))

        urls = self.extract_all_urls(resp)
        self.assertTrue('/records/record-25-45/' in urls)

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_filters(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ('outdoor', 'recurve', 'alle', 'alle'))
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ('outdoor', 'alle', '21plus', 'heren'))
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ('outdoor', 'recurve', 'onder21', 'dames'))
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ('indoor', 'alle', 'gecombineerd', 'alle'))
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

    def test_bad(self):
        # slechte disc
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ("bad", 'alle', 'alle', 'alle'))
        self.assert404(resp, '?')

        # slechte makl
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ("outdoor", 'bad', 'alle', 'alle'))
        self.assert404(resp, '?')

        # slechte lcat
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ("indoor", 'alle', 'bad', 'alle'))
        self.assert404(resp, '?')

        # slecht gesl
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_verbeterbaar % ("25m1pijl", 'alle', 'alle', 'bad'))
        self.assert404(resp, '?')

# end of file
