# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import ORGANISATIE_WA, ORGANISATIE_NHB, ORGANISATIE_IFAA
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter
from Wedstrijden.models import WedstrijdLocatie
from .models import KalenderWedstrijd, WEDSTRIJD_DISCIPLINE_3D
from TestHelpers.e2ehelpers import E2EHelpers


class TestKalenderVereniging(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie, module vereniging """

    url_kalender_vereniging = '/kalender/vereniging/'
    url_kalender_maak_nieuw = '/kalender/vereniging/kies-type/'

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

    def test_maak_wedstrijd(self):
        # anon mag niet
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assert_is_redirect_not_plein(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maak_nieuw)
        self.assert_is_redirect_not_plein(resp)

        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        self.assertEqual(0, KalenderWedstrijd.objects.count())

        # haal het overzicht op, zonder externe locatie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender_vereniging)

        # probeer een wedstrijd aan te maken zonder wedstrijdlocatie
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(0, KalenderWedstrijd.objects.count())

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender_maak_nieuw, post=True)

        # maak een wedstrijdlocatie van deze vereniging aan
        self._maak_externe_locatie(self.nhbver1)

        # haal het overzicht opnieuw op (geen wedstrijden)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        # haal de keuze pagina op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maak_nieuw)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/nieuwe-wedstrijd-kies-type.dtl', 'plein/site_layout.dtl'))

        # maak een nieuwe wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.get(organisatie=ORGANISATIE_WA)
        self.assertEqual(wedstrijd.boogtypen.count(), 5)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 40)

        # maak een nieuwe wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'huh'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(1, KalenderWedstrijd.objects.count())

        # maak nog een wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'nhb'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(2, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.get(organisatie=ORGANISATIE_NHB)
        self.assertEqual(wedstrijd.boogtypen.count(), 5)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 60)        # gender-neutrale klassen zijn niet gekozen

        # maak nog een wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_maak_nieuw, {'keuze': 'ifaa'})
        self.assert_is_redirect(resp, self.url_kalender_vereniging)
        self.assertEqual(3, KalenderWedstrijd.objects.count())
        wedstrijd = KalenderWedstrijd.objects.get(organisatie=ORGANISATIE_IFAA)
        self.assertEqual(wedstrijd.boogtypen.count(), 12)
        self.assertEqual(wedstrijd.discipline, WEDSTRIJD_DISCIPLINE_3D)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 144)

        # haal het overzicht opnieuw op (met de 2 wedstrijden)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_vereniging)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

# end of file
