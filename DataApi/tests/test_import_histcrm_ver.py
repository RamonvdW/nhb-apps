# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.models import DataApiVereniging
from DataApi.operations import ImportHistCrmVerenigingen
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer


class TestDataApiImportHistCrmVer(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, operations class ImportHistCrmVerenigingen """

    def setUp(self):
        pass

    def test_afmelden(self):
        DataApiVereniging.objects.create(
                ver_nr=1,
                naam='Grote club',
                aanmeld_datum='',
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        DataApiVereniging.objects.create(
                ver_nr=2,
                naam='Club is weg',
                aanmeld_datum='1900-01-01',
                afmeld_datum='2000-01-01',
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        DataApiVereniging.objects.create(
                ver_nr=3,
                naam='Club gaat weg',
                aanmeld_datum='',
                afmeld_datum='',        # onbekend, dan geen probleem om af te melden
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        DataApiVereniging.objects.create(
                ver_nr=4,
                naam='Club komt nog',
                aanmeld_datum='2100-01-01',
                afmeld_datum='',
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        out = OutputBuffer()
        v = ImportHistCrmVerenigingen(out, True, '')
        self.assertEqual(v.count_gestopt, 1)
        self.assertEqual(v.count_actief, 3)

        ver = v.vind_vereniging(0)
        self.assertIsNone(ver)

        ver = v.vind_vereniging(1)
        self.assertIsNotNone(ver)
        assert isinstance(ver, DataApiVereniging)
        self.assertEqual(ver.ver_nr, 1)
        self.assertEqual(ver.naam, 'Grote club')

        # ver 1 wordt aangepast
        # ver 2 is al weg
        # ver 3 is afwezig en wordt afgemeld
        data = [
            {
                'club_number': '1',
                'prefix': '',
                'name': 'Grote club',
                'address': '',
                'postal_code': '',
                'location_name': '',
                'iso_abbr': 'NL',
                'latitude': '',
                'longitude': '',
            },
        ]

        # intentie, want dry-run
        v.importeer(data)
        # print('\nout: %s' % out.getvalue())
        self.assertTrue("[INFO] Vereniging [3] Club gaat weg ( .. ) wordt afgemeld" in out.getvalue())

        # nu echt afmelden
        out = OutputBuffer()
        v = ImportHistCrmVerenigingen(out, False, 'doeidag')
        v.importeer(data)

        ver = DataApiVereniging.objects.get(ver_nr=3)
        self.assertEqual(ver.afmeld_datum, 'doeidag')

    def test_mutaties(self):
        DataApiVereniging.objects.create(
                ver_nr=1,
                naam='Grote club',
                aanmeld_datum='',
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        DataApiVereniging.objects.create(
                ver_nr=2,
                naam='Kleine club',
                aanmeld_datum='',
                afmeld_datum='ja',      # vereniging wordt weer actief gemaakt
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        out = OutputBuffer()
        v = ImportHistCrmVerenigingen(out, True, '')
        self.assertEqual(v.count_gestopt, 1)
        self.assertEqual(v.count_actief, 1)

        data = [
            {
                'club_number': '1',
                'prefix': 'De',
                'name': 'Grote Club',
                'address': 'Pijlstraat 7\n1111AA Boogstad',
                'postal_code': '1111AA',
                'location_name': 'Boogstad',
                'coc_number': '12345678',
                'iso_abbr': 'NL',
                'latitude': '12',
                'longitude': '34',
            },
            {
                'club_number': '2',
                'prefix': '',
                'name': 'Kleine Club',
                'address': '',
                'postal_code': '',
                'location_name': '',
                'iso_abbr': '',
                'latitude': '',
                'longitude': '',
            },
            {
                'club_number': '3',
                'prefix': '',
                'name': 'Nieuwe Club',
                'address': '',
                'postal_code': '',
                'location_name': '',
                'iso_abbr': '',
                'latitude': '',
                'longitude': '',
            },
        ]

        # intentie, want dry-run
        v.importeer(data)
        # print('\nout: %s' % out.getvalue())
        self.assertTrue("[INFO] Vereniging 2 wordt weer actief gemaakt" in out.getvalue())

        # nu echt importeren
        out = OutputBuffer()
        v = ImportHistCrmVerenigingen(out, False, '')
        v.importeer(data)

        ver = DataApiVereniging.objects.get(ver_nr=1)
        self.assertEqual(ver.naam, 'De Grote Club')
        self.assertEqual(ver.straatnaam, 'Pijlstraat')
        self.assertEqual(ver.huisnummer, 7)
        self.assertEqual(ver.postcode, '1111AA')
        self.assertEqual(ver.plaats, 'Boogstad')
        self.assertEqual(ver.lat, '12')
        self.assertEqual(ver.lon, '34')

        ver = DataApiVereniging.objects.get(ver_nr=2)
        self.assertEqual(ver.afmeld_datum, '')

    def test_bad(self):
        DataApiVereniging.objects.create(
                ver_nr=1,
                naam='Grote club',
                aanmeld_datum='',
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        DataApiVereniging.objects.create(
                ver_nr=2,
                naam='Kleine club',
                aanmeld_datum='',
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        DataApiVereniging.objects.create(
                ver_nr=3,
                naam='Andere club',
                aanmeld_datum='',
                straatnaam='',
                huisnummer=0,
                postcode='',
                plaats='',
                lat='',
                lon='')

        out = OutputBuffer()
        v = ImportHistCrmVerenigingen(out, True, '')

        data = [
            {
                'club_number': 'krak',
                'prefix': '',
                'name': '',
                'address': '',
                'postal_code': '',
                'location_name': '',
                'iso_abbr': '',
                'latitude': '',
                'longitude': '',
            },
            {
                'club_number': '1',
                'prefix': '',
                'name': 'Grote club',
                'address': 'Maar 1 regel',
                'coc_number': 'bad',
                'postal_code': '',
                'location_name': '',
                'iso_abbr': '',
                'latitude': '',
                'longitude': '',
            },
            {
                'club_number': '2',
                'prefix': '',
                'name': 'Kleine club',
                'address': '7e Doelpakstraat 7\nX',    # twee keer "huisnummer"
                'postal_code': '',
                'location_name': '',
                'iso_abbr': '',
                'latitude': '',
                'longitude': '',
            },
            {
                'club_number': '3',
                'prefix': '',
                'name': 'Andere club',
                'address': 'Doelpakstraat\nX',         # geen huisnummer
                'postal_code': '',
                'location_name': '',
                'iso_abbr': '',
                'latitude': '',
                'longitude': '',
            },
        ]

        v.importeer(data)
        # print('\nout: %s' % out.getvalue())
        self.assertTrue("[ERROR] Geen valide verenigingsnummer: 'krak'" in out.getvalue())
        self.assertTrue("[ERROR] Vereniging 1 adres bestaat niet uit 2 regels:" in out.getvalue())
        self.assertTrue("[WARNING] Vereniging 1 KvK nummer 'bad' moet 8 cijfers bevatten" in out.getvalue())
        self.assertTrue("[DEBUG] Uitdaging: meerdere matches huisnr 7 in 7e Doelpakstraat 7" in out.getvalue())
        self.assertTrue("[ERROR] Kan huisnummer 0 niet vinden in adres 'Doelpakstraat'" in out.getvalue())

        # keys check
        data = [
            {
                'club_number': '1',
            },
        ]
        out = OutputBuffer()
        v = ImportHistCrmVerenigingen(out, True, '')
        v.importeer(data)
        # print('\nout: %s' % out.getvalue())
        self.assertTrue("[ERROR] Verplichte sleutel 'name' niet aanwezig in de 'club{vereniging}' data")

        # trigger de crash optie
        data = [
            {
                'club_number': 'crash',
                'prefix': '',
                'name': '',
                'address': '',
                'postal_code': '',
                'location_name': '',
                'iso_abbr': '',
                'latitude': '',
                'longitude': '',
            },
        ]
        out = OutputBuffer()
        v = ImportHistCrmVerenigingen(out, True, '')

        with self.assertRaises(Exception) as exc:
            v.importeer(data)
        # print('exc.msg=%s' % repr(exc.exception))
        self.assertEqual(exc.exception.args[0], 'crash test')

# end of file
