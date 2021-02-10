# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from Overig.e2ehelpers import E2EHelpers
import io
import os


class TestCompetitieCliOudeSiteMaakJson(E2EHelpers, TestCase):
    """ unittests voor de Competitie applicatie, management command oude_site_maak_json """

    def setUp(self):
        """ initialisatie van de test case """

        self.dir_top = './Competitie/management/testfiles'
        self.dir_testfiles1 = './Competitie/management/testfiles/20200929_220000'
        self.dir_testfiles2 = './Competitie/management/testfiles/20200929_235958'

        self.ref_file = os.path.join(self.dir_top, 'expected_oude_site.json')

    def test_een(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('oude_site_maak_json', self.dir_testfiles1, stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue("[ERROR] Kan einde tabel onverwacht niet vinden" in f2.getvalue())
        self.assertTrue("[ERROR] Kan einde regel onverwacht niet vinden" in f2.getvalue())
        self.assertTrue("[ERROR] Kan einde wedstrijdklasse niet vinden: " in f2.getvalue())
        self.assertTrue("[INFO] Schrijf '%s/oude_site.json'" % self.dir_testfiles1[2:] in f2.getvalue())

        ref_data = open(self.ref_file, 'r').read()
        new_data = open(os.path.join(self.dir_testfiles1, 'oude_site.json'), 'r').read()
        self.assertEqual(ref_data, new_data)

    def test_all(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('oude_site_maak_json', self.dir_top, '--all', stderr=f1, stdout=f2)
        self.assertTrue("[INFO] Schrijf '%s/oude_site.json'" % self.dir_testfiles1[2:] in f2.getvalue())
        self.assertTrue("[INFO] Schrijf '%s/zelfde_site.json'" % self.dir_testfiles2[2:] in f2.getvalue())

# end of file
