# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from .models import (IndivRecord, BesteIndivRecords,
                     LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE)
from NhbStructuur.models import NhbLid
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestRecordsVerbeterbaar(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Views """

    def setUp(self):
        """ initialisatie van de test case """

        # NhbLib
        lid = NhbLid()
        lid.nhb_nr = 123456
        lid.voornaam = 'Janynke'
        lid.achternaam = 'Schutter'
        lid.email = 'janynke@test.nl'
        lid.geboorte_datum = parse_date('1970-03-03')
        lid.woon_straatnaam = 'Papendal'
        lid.geslacht = 'V'
        lid.sinds_datum = parse_date("1991-02-03") # Y-M-D
        #lid.bij_vereniging
        lid.save()
        self.lid1 = lid

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
        self.lid2 = lid

        # Record 42
        rec = IndivRecord()
        rec.volg_nr = 42
        rec.discipline = DISCIPLINE[0][0]   # OD
        rec.soort_record = 'Test record'
        rec.geslacht = GESLACHT[0][0]   # M
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[0][0]   # M
        rec.materiaalklasse = MATERIAALKLASSE[0][0]     # R
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
        rec.discipline = DISCIPLINE[1][0]   # 18
        rec.soort_record = 'Test record para'
        rec.geslacht = GESLACHT[1][0]   # Vrouw
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[1][0]   # Senior
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

        beste = BesteIndivRecords()
        beste.volgorde = 1
        beste.discipline = rec.discipline
        beste.soort_record = rec.soort_record
        beste.geslacht = rec.geslacht
        beste.leeftijdscategorie = rec.leeftijdscategorie
        beste.materiaalklasse = rec.materiaalklasse
        beste.para_klasse = rec.para_klasse
        beste.beste = rec
        beste.save()

        # Record 44
        rec = IndivRecord()
        rec.volg_nr = 44
        rec.discipline = DISCIPLINE[2][0]   # 25
        rec.soort_record = '25m'
        rec.geslacht = GESLACHT[1][0]   # Vrouw
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[3][0]   # Cadet
        rec.materiaalklasse = 'R'       # Recurve
        #rec.para_klasse =
        rec.nhb_lid = self.lid1
        rec.naam = 'Petra Schutter'
        rec.datum = parse_date('2017-08-27')
        rec.plaats = 'Nergens'
        rec.land = 'Niederland'
        rec.score = 249
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        # Record 45
        rec = IndivRecord()
        rec.volg_nr = 45
        rec.discipline = DISCIPLINE[2][0]   # 25
        rec.soort_record = '25m'
        rec.geslacht = GESLACHT[1][0]   # Vrouw
        rec.leeftijdscategorie = LEEFTIJDSCATEGORIE[3][0]   # Cadet
        rec.materiaalklasse = 'R'       # Recurve
        #rec.para_klasse =
        rec.nhb_lid = self.lid2
        rec.naam = 'Petra Schutter'
        rec.datum = parse_date('2017-08-30')
        rec.plaats = 'Narguns'
        rec.land = 'Niederland'
        rec.score = 250
        # rec.score_notitie =
        # rec.is_european_record =
        # rec.is_world_record =
        rec.save()

        beste = BesteIndivRecords()
        beste.volgorde = 1
        beste.discipline = rec.discipline
        beste.soort_record = rec.soort_record
        beste.geslacht = rec.geslacht
        beste.leeftijdscategorie = rec.leeftijdscategorie
        beste.materiaalklasse = rec.materiaalklasse
        beste.para_klasse = rec.para_klasse
        beste.beste = rec
        beste.save()
        self.beste = beste

        self.url_kies_disc = '/records/indiv/verbeterbaar/'
        self.url_verbeterbaar = '/records/indiv/verbeterbaar/%s/'     # disc

    def test_xtra(self):
        self.assertTrue(str(self.beste) != "")

    def test_kies_disc(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies_disc)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar_kies_disc.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        self.assertEqual(3, len(urls))      # indoor, 25m1pijl, outdoor

        self.e2e_assert_other_http_commands_not_supported(self.url_kies_disc)

    def test_verbeterbaar_od(self):
        url = self.url_verbeterbaar % "outdoor"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar_discipline.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(url)

    def test_verbeterbaar_18(self):
        url = self.url_verbeterbaar % "indoor"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar_discipline.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(url)

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        self.assertEqual(12, len(urls))
        self.assertTrue('/records/record-18-43/' in urls)

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_verbeterbaar_25(self):
        url = self.url_verbeterbaar % "25m1pijl"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('records/verbeterbaar_discipline.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(url)

        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        self.assertEqual(12, len(urls))
        self.assertTrue('/records/record-25-45/' in urls)

    def test_combies(self):
        url = self.url_verbeterbaar % 'outdoor'
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?boog=recurve')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(url + '?boog=alles&geslacht=man&leeftijdsklassse=senior')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(url + '?boog=recurve&geslacht=vrouw&leeftijdsklasse=junior')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

    def test_verbeterbaar_bad(self):
        url = self.url_verbeterbaar % "bad"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert_is_redirect(resp, self.url_kies_disc)

        url = self.url_verbeterbaar % "outdoor"
        with self.assert_max_queries(20):
            resp = self.client.get(url + '?boog=bad')
        self.assert_is_redirect(resp, self.url_kies_disc)

        with self.assert_max_queries(20):
            resp = self.client.get(url + '?geslacht=bad')
        self.assert_is_redirect(resp, self.url_kies_disc)

        with self.assert_max_queries(20):
            resp = self.client.get(url + '?leeftijdsklasse=bad')
        self.assert_is_redirect(resp, self.url_kies_disc)

# end of file
