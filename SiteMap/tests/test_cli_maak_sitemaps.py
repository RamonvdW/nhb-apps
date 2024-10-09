# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from SiteMap.models import SiteMapLastMod
from TestHelpers.e2ehelpers import E2EHelpers
import tempfile
import os


class TestSiteMapCliMaakSitemaps(E2EHelpers, TestCase):

    """ tests voor de SiteMap applicatie, management command maak_sitemaps """

    expected_sitemaps = 7 + 1       # +1 for index

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_alles(self):
        self.assertEqual(SiteMapLastMod.objects.count(), 0)

        with tempfile.TemporaryDirectory() as output_dir:
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('maak_sitemaps', output_dir)
            # print("f1: %s" % f1.getvalue())
            # print("f2: %s" % f2.getvalue())

            self.assertTrue('[ERROR]' not in f1.getvalue())
            self.assertTrue('[ERROR]' not in f2.getvalue())

            fnames = os.listdir(output_dir)
            self.assertEqual(len(fnames), self.expected_sitemaps)

        self.assertEqual(SiteMapLastMod.objects.count(), self.expected_sitemaps - 1)

        last_mod = SiteMapLastMod.objects.first()
        self.assertTrue(str(last_mod) != '')

        # nog een keer, dan zijn de last_mod records beschikbaar en de digest hetzelfde
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assert_max_queries(20):
                f1, f2 = self.run_management_command('maak_sitemaps', output_dir)

            self.assertTrue('[ERROR]' not in f1.getvalue())
            self.assertTrue('[ERROR]' not in f2.getvalue())

            fnames = os.listdir(output_dir)
            self.assertEqual(len(fnames), self.expected_sitemaps)

        self.assertEqual(SiteMapLastMod.objects.count(), self.expected_sitemaps - 1)

    def test_exception(self):
        fake_dir = '/tmp/does-not-exist/'
        f1, f2 = self.run_management_command('maak_sitemaps', fake_dir, report_exit_code=False)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertTrue('[ERROR]' in f1.getvalue())
        self.assertTrue('Traceback:' in f1.getvalue())

# end of file
