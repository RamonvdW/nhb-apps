# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestTakenViews(E2EHelpers, TestCase):

    """ tests voor de applicatie Taken """

    test_after = ('Functie', 'Taken.tests.test_taken')

    url_overzicht = '/taken/'
    url_details = '/taken/details/%s/'  # taak_pk

    emailadres = 'taak@nhb.not'
    emailadres2 = 'taak2@nhb.not'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """

        self.functie_sup = Functie.objects.get(rol='SUP')
        self.functie_sup.bevestigde_email = self.emailadres
        self.functie_sup.laatste_email_over_taken = None
        self.functie_sup.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

        self.functie_mwz = Functie.objects.get(rol='MWZ')
        self.functie_mwz.bevestigde_email = self.emailadres2
        self.functie_mwz.laatste_email_over_taken = None
        self.functie_mwz.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

        # maak een taak aan
        taak = Taak(toegekend_aan_functie=self.functie_sup,
                    deadline='2020-01-01',
                    beschrijving='Testje taak1 met meerdere\nregels\ntest')
        taak.save()
        self.taak1 = taak

        # maak een afgeronde taak aan
        taak = Taak(is_afgerond=True,
                    toegekend_aan_functie=self.functie_mwz,
                    deadline='2020-01-01',
                    beschrijving='Afgerond testje taak2')
        taak.save()
        self.taak2 = taak

    def test_anon(self):
        # do een get van het takenoverzicht zonder ingelogd te zijn
        # dit leidt tot een redirect naar het plein
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details % 0)
        self.assert403(resp)

    def test_allowed(self):
        self.functie_sup.accounts.add(self.testdata.account_admin)
        self.functie_mwz.accounts.add(self.testdata.account_admin)

        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/overzicht.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, 'Testje taak1')
        self.assertContains(resp, 'testje taak2')

        url = self.url_details % self.taak1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/details.dtl', 'plein/site_layout.dtl'))

        # doe de post om de taak af te ronden
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_overzicht)

        # nogmaals, voor uitbreiding logboek
        self.taak1 = Taak.objects.get(pk=self.taak1.pk)     # refresh from database
        self.taak1.is_afgerond = False
        self.taak1.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_overzicht)

        # nogmaals afronden (is al afgerond)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_overzicht)

        # details, nu afgerond
        url = self.url_details % self.taak1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/details.dtl', 'plein/site_layout.dtl'))

        # overzicht met afgeronde taak
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/overzicht.dtl', 'plein/site_layout.dtl'))

        self.assertTrue(str(self.taak1) != '')
        self.assertTrue(str(self.taak2) != '')

    def test_bad(self):
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        # niet bestaande taak
        url = self.url_details % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Geen valide taak')
        resp = self.client.post(url)
        self.assert404(resp, 'Geen valide taak')

        # taak van een ander
        url = self.url_details % self.taak2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)


# end of file
