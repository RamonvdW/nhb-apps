# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils.dateparse import parse_date
from Records.definities import LEEFTIJDSCATEGORIE, GESLACHT, MATERIAALKLASSE, DISCIPLINE
from Records.models import IndivRecord, AnderRecord
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestRecordsView(E2EHelpers, TestCase):
    """ unittests voor de Records applicatie, Views """

    url_overzicht = '/records/'
    url_specifiek = '/records/record-%s-%s/'  # discipline (18/25/OD), volg_nr
    url_zoek = '/records/zoek/'
    url_lijst_er = '/records/lijst-er/'
    url_lijst_wr = '/records/lijst-wr/'

    def setUp(self):
        """ initialisatie van de test case """

        # NhbLib
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
                    discipline=DISCIPLINE[2][0],   # 25,
                    soort_record='25m',
                    geslacht=GESLACHT[1][0],   # V
                    leeftijdscategorie=LEEFTIJDSCATEGORIE[3][0],  # C
                    materiaalklasse='R',       # Recurve
                    sporter=sporter,
                    naam='Petra Schutter',
                    datum=parse_date('2017-08-27'),
                    plaats='Nergens',
                    land='Niederland',
                    score=249)
        rec.save()

        # Record 50
        rec = IndivRecord(
                    volg_nr=50,
                    discipline='OD',
                    soort_record='70m (72p)',
                    geslacht='V',
                    leeftijdscategorie='S',
                    materiaalklasse='R',       # Recurve
                    sporter=sporter,
                    naam='Petra Schutter',
                    datum=parse_date('2020-02-02'),
                    plaats='Bullseye',
                    land='Nederland',
                    score=350,
                    is_european_record=True)
        rec.save()

        # Record 51
        rec = IndivRecord(
                    volg_nr=51,
                    discipline='OD',
                    soort_record='70m (72p)',
                    geslacht='V',
                    leeftijdscategorie='S',
                    materiaalklasse='R',       # Recurve
                    sporter=sporter,
                    naam='Petra Schutter',
                    datum=parse_date('2020-03-03'),
                    plaats='Bullseye',
                    land='Nederland',
                    score=355,
                    is_european_record=True,
                    is_world_record=True)
        rec.save()

        # Record 60
        rec = IndivRecord(
                    volg_nr=60,
                    discipline='OD',
                    soort_record='50m (72p)',
                    geslacht='V',
                    leeftijdscategorie='U',    # para
                    para_klasse='Open',
                    materiaalklasse='R',       # Recurve
                    sporter=sporter,
                    naam='Para Schutter',
                    datum=parse_date('2020-03-03'),
                    plaats='Bullseye',
                    land='Nederland',
                    score=350,
                    is_european_record=False,
                    is_world_record=False)
        rec.save()
        self.rec = rec

    def test_create(self):
        rec = IndivRecord.objects.first()
        rec.clean_fields()      # run field validators
        rec.clean()             # run model validator
        self.assertIsNotNone(str(rec))      # use the __str__ method (only used by admin interface)

    def test_view_overzicht(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_overzicht.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_view_specifiek(self):
        url = self.url_specifiek % ('OD', 42)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_specifiek.dtl', 'design/site_layout.dtl'))
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
        self.assert_template_used(resp, ('records/records_specifiek.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, '1235')
        self.assertContains(resp, 'Ergens Anders')
        self.assertContains(resp, 'Nederland')
        self.assertContains(resp, 'Top Schutter 2')
        self.assertContains(resp, 'Para klasse')
        self.assertContains(resp, 'Open')

    def test_view_specifiek_missing(self):
        url = self.url_specifiek % ('OD', 0)            # niet bestaand record nummer
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Record niet gevonden')

    def test_view_zoek(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_zoek.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # te lange zoekterm
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'x' * 51})
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        self.e2e_assert_other_http_commands_not_supported(self.url_zoek)

    def test_view_zoek_lid_nr(self):
        resp = self.client.get(self.url_zoek, {'zoekterm': '123456'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # onbekend lid_nr
        resp = self.client.get(self.url_zoek, {'zoekterm': '999999'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        # onbekende zoekterm
        # let op de zoekterm: mag niet matchen met soort_record, naam, plaats of land
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'jaja'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assertContains(resp, "Geen records gevonden")

    def test_view_zoek_plaats(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'Papendal'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_zoek.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, "Resultaten")
        self.assertContains(resp, "1 record")
        self.assert_html_ok(resp)

    def test_view_zoek_plaats_case_insensitive(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'PENdal'})       # noqa
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assertContains(resp, "Resultaten")
        self.assertContains(resp, "1 record")

    def test_special(self):
        self.rec.is_european_record = True
        self.rec.is_world_record = True
        self.rec.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_er)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_special_er.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_wr)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_special_wr.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_lijst_er)
        self.e2e_assert_other_http_commands_not_supported(self.url_lijst_wr)

    def test_zoek_para(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_zoek, {'zoekterm': 'Para Schutter'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_zoek.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Para Schutter')
        self.assertContains(resp, 'Open')

    def test_eervol(self):
        # eervolle vermelding
        ander = AnderRecord(
                    titel='Guinness Book',
                    sv_icon='record ander',
                    tekst='test',
                    url='https://www.handboogsport.nl')
        ander.save()

        self.assertTrue(str(ander) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('records/records_overzicht.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

# end of file
