# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Instaptoets.models import Vraag, Instaptoets
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from datetime import timedelta


class TestOpleidingBasiscursus(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit Basiscursus """

    test_after = ('Account', 'Functie')

    url_basiscursus = '/opleiding/basiscursus/'
    url_inschrijven_basiscursus = '/opleiding/inschrijven/basiscursus/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')

        sporter = Sporter(
                    lid_nr=100000,
                    voornaam='Nor',
                    achternaam='Maal',
                    geboorte_datum='1988-08-08',
                    sinds_datum='2024-02-02',
                    account=self.account_normaal)
        sporter.save()
        self.sporter = sporter

    def test_anon(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

    def test_gast(self):
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_inschrijven_basiscursus not in urls)

    def test_sporter(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

        # maak de instaptoets beschikbaar
        Vraag().save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

        # instaptoets gehaald
        now = timezone.now()
        toets = Instaptoets(
                    sporter=self.sporter,
                    afgerond=now,
                    aantal_vragen=1,
                    aantal_antwoorden=1,
                    is_afgerond=True,
                    aantal_goed=1,
                    geslaagd=True)
        toets.save()

        # inschrijven is mogelijk
        # toets opnieuw doen is ook mogelijk (alleen op de test server)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'kan alleen op de test server')

        # inschrijven is mogelijk
        # toets opnieuw doen is niet mogelijk (op de live server)
        with override_settings(IS_TEST_SERVER=False):
            resp = self.client.get(self.url_basiscursus)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))
            self.assertNotContains(resp, 'kan alleen op de test server')

        # instaptoets verlopen
        toets.afgerond = timezone.now() - timedelta(days=400)
        toets.save(update_fields=['afgerond'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

# end of file
