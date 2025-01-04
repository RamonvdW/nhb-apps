# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Instaptoets.models import Vraag, Instaptoets
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from datetime import timedelta


class TestOpleidingenBasiscursus(E2EHelpers, TestCase):

    """ tests voor de Opleidingen applicatie, functionaliteit Basiscursus """

    test_after = ('Account', 'Functie')

    url_basiscursus = '/opleidingen/basiscursus/'

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
        resp = self.client.get(self.url_basiscursus)
        self.assert_is_redirect(resp, '/account/login/')

    def test_gast(self):
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assert403(resp)

    def test_sporter(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/basiscursus.dtl', 'plein/site_layout.dtl'))

        # maak de instaptoets beschikbaar
        Vraag().save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/basiscursus.dtl', 'plein/site_layout.dtl'))

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

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/basiscursus.dtl', 'plein/site_layout.dtl'))

        # instaptoets verlopen
        toets.afgerond = timezone.now() - timedelta(days=400)
        toets.save(update_fields=['afgerond'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/basiscursus.dtl', 'plein/site_layout.dtl'))

# end of file
