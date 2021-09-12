# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Wedstrijden.models import WedstrijdLocatie
from .models import KalenderWedstrijd
from TestHelpers.e2ehelpers import E2EHelpers


class TestKalender(E2EHelpers, TestCase):
    """ unit tests voor de Kalender applicatie """

    url_kalender = '/kalender/'
    url_kalender_manager = '/kalender/manager/'
    url_kalender_vereniging = '/kalender/vereniging/'
    url_kalender_wijzig_wedstrijd = '/kalender/%s/wijzig/'  # wedstrijd_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        lid = NhbLid(
                    nhb_nr=100000,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    account=self.account_admin)
        lid.save()

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

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.get(self.url_kalender_manager)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_vereniging)
        self.assert403(resp)

        resp = self.client.get(self.url_kalender_wijzig_wedstrijd % 0)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender)

    def test_gebruiker(self):
        self.client.logout()

        # haal de url op van de eerste pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender)
        url = resp.url

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_kalender)
        self.assert_is_redirect(resp, self.url_kalender_manager)

        resp = self.client.get(self.url_kalender_vereniging)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.nhbver1)
        resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        # wissel terug naar BB
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender_manager, post=False)

    def test_hwl(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_kalender)
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        resp = self.client.get(self.url_kalender_manager)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender_vereniging, post=False)

        # gebruik de post interface zonder verzoek
        self.assertEqual(0, KalenderWedstrijd.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_vereniging)
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(0, KalenderWedstrijd.objects.count())

        # wedstrijd aanmaken zonder dat de vereniging een externe locatie heeft
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(0, KalenderWedstrijd.objects.count())

        # maak een wedstrijd aan
        self._maak_externe_locatie(self.nhbver1)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_vereniging, {'nieuwe_wedstrijd': 'ja'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

        self.assertEqual(1, KalenderWedstrijd.objects.count())

        # haal de wedstrijd op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

# end of file
