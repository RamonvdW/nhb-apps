# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter
from Wedstrijden.models import WedstrijdLocatie
from .models import KalenderWedstrijd
from TestHelpers.e2ehelpers import E2EHelpers


class TestKalenderMaand(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie """

    url_kalender = '/kalender/'
    url_kalender_maand = '/kalender/pagina-%s-%s/'  # jaar, maand
    url_kalender_vereniging = '/kalender/vereniging/'
    url_kalender_info = '/kalender/%s/info/'  # wedstrijd_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        sporter = Sporter(
                    lid_nr=100000,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    account=self.account_admin)
        sporter.save()

        # maak een test vereniging
        self.nhbver1 = NhbVereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.nhbver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.nhb_ver = self.nhbver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        self.nhbver2 = NhbVereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.nhbver2.save()

    @staticmethod
    def _maak_externe_locatie(ver):
        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(ver)

        return locatie

    def test_basic(self):
        # maand als getal
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 1))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))

        # illegale maand getallen
        resp = self.client.get(self.url_kalender_maand % (2020, 0))
        self.assert404(resp)
        resp = self.client.get(self.url_kalender_maand % (2020, 0))
        self.assert404(resp)

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'mrt'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'maart'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # illegale maand tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'xxx'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # illegaal jaar
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 'maart'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # wrap-around in december voor 'next'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 12))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # wrap-around in januari voor 'prev'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (2020, 1))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_wedstrijd(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]

        # accepteer de wedstrijd zodat deze getoond wordt
        wedstrijd.status = 'A'
        wedstrijd.save()

        self.client.logout()

        # haal de maand pagina op met een wedstrijd erop
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender)
        self.assertEqual(resp.status_code, 302)     # redirect naar juiste maand-pagina
        url = resp.url

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # annuleer de wedstrijd
        wedstrijd.status = 'X'
        wedstrijd.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_info(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.all()[0]

        # haal de info pagina van de wedstrijd op
        url = self.url_kalender_info % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_info % 999999)
        self.assert404(resp)

        self.e2e_assert_other_http_commands_not_supported(url)

# end of file
