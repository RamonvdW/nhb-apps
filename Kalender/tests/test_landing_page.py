# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import WedstrijdLocatie, Wedstrijd
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestKalender(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie. module Manager """

    url_kalender = '/kalender/'
    url_kalender_manager = '/wedstrijden/manager/'
    url_kalender_vereniging = '/wedstrijden/vereniging/'
    url_kalender_maand = '/kalender/maand/##'          # startswith

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        # maak een test vereniging
        self.ver1 = NhbVereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.ver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.ver1)

        datum = timezone.now() + datetime.timedelta(days=30)
        wedstrijd = Wedstrijd(
                        titel='Test 1',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()
        self.wedstrijd = wedstrijd

        # inschrijving gesloten
        datum = timezone.now() + datetime.timedelta(days=4)
        wedstrijd = Wedstrijd(
                        titel='Test 2',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()

    def test_openbaar(self):
        self.client.logout()

        # redirect naar openbare overzicht
        resp = self.client.get(self.url_kalender)
        self.assert_is_redirect(resp, self.url_kalender_maand)

    def test_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_kalender)
        self.assert_is_redirect(resp, self.url_kalender_manager)

        self.e2e_assert_other_http_commands_not_supported(self.url_kalender)

    def test_hwl(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_kalender)
        self.assert_is_redirect(resp, self.url_kalender_vereniging)

# end of file
