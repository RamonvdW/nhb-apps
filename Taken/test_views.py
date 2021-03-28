# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from NhbStructuur.models import NhbLid
from Overig.e2ehelpers import E2EHelpers
from .models import Taak
import datetime


class TestTakenViews(E2EHelpers, TestCase):
    """ unit tests voor de Taken applicatie """

    test_after = ('Functie',)

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_same = self.e2e_create_account('same', 'same@test.com', 'same')

        lid = NhbLid()
        lid.nhb_nr = 100042
        lid.geslacht = "M"
        lid.voornaam = "Beh"
        lid.achternaam = "eerder"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.account = self.account_normaal
        lid.email = lid.account.email
        lid.save()

        # maak een taak aan
        taak = Taak(toegekend_aan=self.account_admin,
                    deadline='2020-01-01',
                    beschrijving='Testje',
                    handleiding_pagina='Hoofdpagina')
        taak.save()
        self.taak1 = taak

        # maak een afgeronde taak aan
        taak = Taak(is_afgerond=True,
                    toegekend_aan=self.account_normaal,
                    deadline='2020-01-01',
                    beschrijving='Afgerond testje')
        taak.save()
        self.taak2 = taak

        self.url_overzicht = '/taken/overzicht/'
        self.url_details = '/taken/details/%s/'     # taak_pk

    def test_anon(self):
        # do een get van het taken overzicht zonder ingelogd te zijn
        # resulteert in een redirect naar het plein
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details % 0)
        self.assert403(resp)

    def test_allowed(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/overzicht.dtl', 'plein/site_layout.dtl'))

        url = self.url_details % self.taak1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/details.dtl', 'plein/site_layout.dtl'))

        # nogmaals, zonder handleiding
        self.taak1.handleiding_pagina = ""
        self.taak1.save()
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

    def test_bad(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        # niet bestaande taak
        url = self.url_details % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)

        # taak van een ander
        url = self.url_details % self.taak2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)


# end of file
