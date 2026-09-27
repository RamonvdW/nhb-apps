# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.models import DataApiVereniging
from DataApi.operations import ImportHistCrmLidmaatschappen
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer


class TestDataApiImportHistCrmLms(E2EHelpers, TestCase):

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

        out = OutputBuffer()
        v = ImportHistCrmLidmaatschappen(out, True, '')
        self.assertEqual(v.count_gestopt, 0)
        self.assertEqual(v.count_actief, 0)
        self.assertEqual(v.count_ver_null, 0)

        data = [
            {   # geen lid
                'club_number': None,
                'member_number': 100001,
                'member_from': None,
                'member_from_club': None,
                'member_until_club': None,
                'gender': 'F',                  # wordt omgezet in V
                'birthday': '2001-03-20',
                'postal_code': '1111AA',
                'iso_abbr': 'NL',
                'date_of_death': None,
            },
            {
                'club_number': 1,
                'member_number': 100002,
                'member_from': None,
                'member_from_club': None,
                'member_until_club': None,
                'gender': 'M',
                'birthday': '1950-11-30',
                'postal_code': '3409',
                'iso_abbr': 'BE',
                'date_of_death': None,
            },
            {
                'club_number': 1,
                'member_number': 100003,
                'member_from': None,
                'member_from_club': None,
                'member_until_club': None,
                'gender': 'M',
                'birthday': '1950-11-30',
                'postal_code': '3409',
                'iso_abbr': None,               # wordt automatisch NL
                'date_of_death': None,
            },
            {
                'club_number': 1,
                'member_number': 100004,
                'member_from': None,
                'member_from_club': '2020-02-02',
                'member_until_club': '9999-12-31',      # geen einddatum
                'gender': 'M',
                'birthday': '1950-11-30',
                'postal_code': None,                    # geen postcode mag
                'iso_abbr': None,
                'date_of_death': None,
            },
            {
                'club_number': 1,
                'member_number': 100005,
                'member_from': None,
                'member_from_club': '2040-02-02',       # start in de toekomst
                'member_until_club': '2099-01-01',      # einddatum in de toekomst
                'gender': 'M',
                'birthday': '1950-11-30',
                'postal_code': None,
                'iso_abbr': None,
                'date_of_death': None,
            },
        ]

        # intentie, want dry-run
        v.importeer(data)
        print('\nout: %s' % out.getvalue())

    def test_bad(self):
        out = OutputBuffer()
        v = ImportHistCrmLidmaatschappen(out, True, '')

        data = [
            {
                'club_number': 'x',             # geen getal
                'member_number': 'x',           # geen getal
                'birthday': 'ymd',
                'member_from': None,
                'member_from_club': None,
                'member_until_club': None,
                'gender': 'X',
                'postal_code': '1111AA',
                'iso_abbr': 'NL',
                'date_of_death': None,
            },
            {
                'club_number': None,                # geen lid
                'member_number': 100001,            # moet goed zijn
                'birthday': 'ymd',                  # geen datum
                'member_from': None,
                'member_from_club': None,
                'member_until_club': None,
                'gender': 'X',
                'postal_code': '1111AA',
                'iso_abbr': 'NL',
                'date_of_death': None,
            },
            {
                'club_number': 'x',                 # geen getal
                'member_number': 100002,            # moet goed zijn
                'birthday': '2005-01-01',           # moet goed zijn
                'member_from': None,
                'member_from_club': None,
                'member_until_club': None,
                'gender': 'Y',                      # bad gender
                'postal_code': '1111',              # bad postcode
                'iso_abbr': 'NL',
                'date_of_death': None,
            },
            {
                'club_number': 'x',                 # geen getal
                'birthday': '2000-01-01',           # moet goed zijn
                'gender': 'M',                      # moet goed zijn
                'member_number': 100003,
                'member_from': None,
                'member_from_club': '1801',         # bad date
                'member_until_club': None,
                'iso_abbr': 'NL',
                'postal_code': '1111',              # bad NL postcode
                'date_of_death': None,
            },
            {
                'club_number': 'x',                 # geen getal
                'member_number': 100004,
                'birthday': '2000-01-01',           # moet goed zijn
                'gender': 'M',                      # moet goed zijn
                'iso_abbr': 'NL',
                'postal_code': '1111ZZ',            # moet goed zijn
                'member_from_club': '2010-06-07',   # moet goed zijn
                'member_from': None,
                'member_until_club': None,
                'date_of_death': None,
            },
            {
                'club_number': None,                # geen getal
                'member_number': 100005,
                'birthday': '20yymmdd',             # bad birthday
                'gender': 'M',
                'iso_abbr': 'NL',
                'postal_code': '1111ZZ',
                'member_from_club': None,
                'member_from': None,
                'member_until_club': None,
                'date_of_death': None,
            },
            {
                'club_number': 1,                   # moet goed zijn
                'member_number': 100006,            # moet goed zijn
                'birthday': '2000-01-01',           # moet goed zijn
                'gender': 'M',                      # moet goed zijn
                'iso_abbr': 'NL',                   # moet goed zijn
                'postal_code': '1111ZZ',            # moet goed zijn
                'member_from_club': None,           # kies member_from
                'member_from': '2010-14-02',        # bad month
                'member_until_club': None,
                'date_of_death': None,
            },
            {
                'club_number': 1,                   # moet goed zijn
                'member_number': 100007,            # moet goed zijn
                'birthday': '2000-01-01',           # moet goed zijn
                'gender': 'M',                      # moet goed zijn
                'iso_abbr': 'NL',                   # moet goed zijn
                'postal_code': '1111ZZ',            # moet goed zijn
                'member_from': None,                # kies member_from_club
                'member_from_club': '2010-14-02',   # bad month
                'member_until_club': None,
                'date_of_death': None,
            },
            {
                'club_number': 1,                   # moet goed zijn
                'member_number': 100008,            # moet goed zijn
                'birthday': '2000-01-01',           # moet goed zijn
                'gender': 'M',                      # moet goed zijn
                'iso_abbr': 'NL',                   # moet goed zijn
                'postal_code': '1111ZZ',            # moet goed zijn
                'member_from': None,                # kies member_from_club
                'member_from_club': '2010-12-02',   # moet goed zijn
                'member_until_club': 'ymd',         # bad date
                'date_of_death': None,
            },
        ]

        v.importeer(data)
        print('\nout: %s' % out.getvalue())

        self.assertTrue("[ERROR] Foutief bondsnummer: x (geen getal)" in out.getvalue())
        self.assertTrue("[ERROR] Lid 100001 heeft geen valide geboortedatum: 'ymd'" in out.getvalue())
        self.assertTrue("[ERROR] Lid 100002 heeft onbekend geslacht: Y" in out.getvalue())
        self.assertTrue("[WARNING] Lid 100003 uit plaats ?, land NL heeft postcode '1111'" in out.getvalue())
        self.assertTrue("[ERROR] Lid 100003 heeft geen valide datum member_from[_club]: '1801'" in out.getvalue())
        self.assertTrue("[ERROR] Lid 100005 heeft geen valide geboortedatum: '20yymmdd'" in out.getvalue())
        self.assertTrue("[ERROR] Lid 100006 heeft geen valide member_from[_club]: '2010-14-02'" in out.getvalue())
        self.assertTrue("[ERROR] Lid 100007 heeft geen valide member_from[_club]: '2010-14-02'" in out.getvalue())
        self.assertTrue("[ERROR] Lid 100008 heeft geen valide datum member_until[_club]: 'ymd" in out.getvalue())

# end of file
