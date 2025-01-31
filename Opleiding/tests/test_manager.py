# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Instaptoets.models import Vraag
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleiding.models import Opleiding
from TestHelpers.e2ehelpers import E2EHelpers


class TestOpleidingManager(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit voor de MO """

    test_after = ('Account', 'Functie')

    url_manager = '/opleiding/manager/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

        # maak een basiscursus aan zodat het kaartje Basiscursus getoond wordt op het overzicht
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_begin="2024-11-01",
                        periode_einde="2024-12-01",
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True)
        opleiding.save()
        self.opleiding = opleiding
        self.opleiding.refresh_from_db()

        # maak de instaptoets beschikbaar
        Vraag().save()

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_manager)
        self.assert403(resp, 'Geen toegang')

    def test_lijst(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        # lege lijst
        Opleiding.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht-manager.dtl', 'plein/site_layout.dtl'))


# end of file
