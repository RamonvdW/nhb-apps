# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.definities import ORGANISATIE_WA, ORGANISATIE_KHSN, ORGANISATIE_IFAA
from Functie.operations import maak_functie
from Locatie.models import Locatie
from NhbStructuur.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_DISCIPLINE_3D
from Wedstrijden.models import Wedstrijd


class TestWedstrijdenVereniging(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module vereniging """

    url_wedstrijden_vereniging = '/wedstrijden/vereniging/'
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'

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
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        self.ver2 = Vereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver2.save()

    @staticmethod
    def _maak_externe_locatie(ver):
        # voeg een locatie toe
        locatie = Locatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(ver)

        return locatie

    def test_maak_wedstrijd(self):
        # anon mag niet
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_vereniging)
        self.assert_is_redirect_not_plein(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_maak_nieuw)
        self.assert_is_redirect_not_plein(resp)

        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        self.assertEqual(0, Wedstrijd.objects.count())

        # haal het overzicht op, zonder externe locatie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_vereniging)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden_vereniging)

        # probeer een wedstrijd aan te maken zonder locatie
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        self.assertEqual(0, Wedstrijd.objects.count())

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden_maak_nieuw, post=True)

        # maak een locatie van deze vereniging aan
        self._maak_externe_locatie(self.ver1)

        # haal het overzicht opnieuw op (geen wedstrijden)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_vereniging)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        # haal de keuze pagina op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_maak_nieuw)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/nieuwe-wedstrijd-kies-type.dtl', 'plein/site_layout.dtl'))

        # maak een nieuwe wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.get(organisatie=ORGANISATIE_WA)
        self.assertEqual(wedstrijd.boogtypen.count(), 5)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 40)

        # maak een nieuwe wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'huh'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        self.assertEqual(1, Wedstrijd.objects.count())

        # maak nog een wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        self.assertEqual(2, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.get(organisatie=ORGANISATIE_KHSN)
        self.assertEqual(wedstrijd.boogtypen.count(), 5)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 70)        # gender-neutrale klassen zijn niet gekozen

        # maak nog een wedstrijd aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'ifaa'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        self.assertEqual(3, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.get(organisatie=ORGANISATIE_IFAA)
        self.assertEqual(wedstrijd.boogtypen.count(), 12)
        self.assertEqual(wedstrijd.discipline, WEDSTRIJD_DISCIPLINE_3D)
        self.assertEqual(wedstrijd.wedstrijdklassen.count(), 144)

        # haal het overzicht opnieuw op (met de 2 wedstrijden)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_vereniging)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

# end of file
