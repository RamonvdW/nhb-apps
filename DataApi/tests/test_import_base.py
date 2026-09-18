# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from DataApi.import_base import ImportCrmBase
from TestHelpers.e2ehelpers import E2EHelpers
import io


class TestDataApiImportBase(E2EHelpers, TestCase):

    """ tests voor de DataApi applicatie, base class ImportCrmBase """

    def setUp(self):
        pass

    def test_import_base(self):
        out = io.StringIO()
        base = ImportCrmBase(out, True, 'hallo')
        self.assertTrue(base.dryrun)
        self.assertEqual(base.afmelddatum, 'hallo')
        base.out_warning('test')
        self.assertTrue('[WARNING] test' in out.getvalue())

        out = io.StringIO()
        base = ImportCrmBase(out, False, '')
        self.assertFalse(base.dryrun)
        base.out_error('test)')
        self.assertTrue('[ERROR] test' in out.getvalue())

        out = io.StringIO()
        base = ImportCrmBase(out, False, '')
        base.out_info('test')
        self.assertTrue('[INFO] test' in out.getvalue())

        out = io.StringIO()
        base = ImportCrmBase(out, False, '')
        base.out_debug('test')
        self.assertTrue('[DEBUG] test' in out.getvalue())

        out = io.StringIO()
        base = ImportCrmBase(out, False, '')
        self.assertFalse(base.exit_error)
        res = base.check_keys(['foo', 'bar'], ('foo',), ('bar', 'niet nodig'), 'test')
        self.assertFalse(res)        # geen error
        self.assertFalse(base.exit_error)

        out = io.StringIO()
        base = ImportCrmBase(out, False, '')
        res = base.check_keys(['foo', 'bar', 'extra'], ('foo', 'nodig'), ('bar', 'niet nodig'), 'test')
        # print('out: %s' % out.getvalue())
        self.assertTrue(res)        # error
        self.assertTrue(base.exit_error)
        self.assertTrue("[ERROR] [FATAL] Verplichte sleutel 'nodig' niet aanwezig in de 'test' data" in out.getvalue())
        self.assertTrue("[WARNING] Extra sleutel aanwezig in de 'test' data: ['extra']" in out.getvalue())

    def test_huisnummer(self):
        out = io.StringIO()
        base = ImportCrmBase(out, False, '')
        nr = base.extract_huisnummer('Eerste straat 1')
        self.assertEqual(nr, 1)

        nr = base.extract_huisnummer('Tweede straat 2bis')
        self.assertEqual(nr, 2)

        nr = base.extract_huisnummer('Derde straat 3 A')
        self.assertEqual(nr, 3)

        nr = base.extract_huisnummer('3e straat 4')
        self.assertEqual(nr, 4)

        nr = base.extract_huisnummer('Pijlweg')
        self.assertEqual(nr, 0)

        nr = base.extract_huisnummer('')
        self.assertEqual(nr, 0)


# end of file
