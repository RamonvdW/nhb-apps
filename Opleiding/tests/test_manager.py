# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import Functie
from Instaptoets.models import Vraag, Instaptoets
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN, OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF
from Opleiding.models import Opleiding, OpleidingInschrijving
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers


class TestOpleidingManager(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit voor de MO """

    test_after = ('Account', 'Functie')

    url_manager = '/opleiding/manager/'
    url_niet_ingeschreven = '/opleiding/manager/niet-ingeschreven/'

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

        now = timezone.now()
        sporter = Sporter(
                    lid_nr=100001,
                    voornaam='Thea',
                    achternaam='de Tester',
                    unaccented_naam='Thea de Tester',
                    email='normaal@test.nhb',
                    geboorte_datum="1970-11-15",
                    geboorteplaats='Pijlstad',
                    geslacht='V',
                    sinds_datum='2000-01-01',
                    telefoon='+123456789',
                    lid_tot_einde_jaar=now.year,
                    account=self.account_normaal)
        sporter.save()
        self.sporter = sporter

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

    def test_niet_ingeschreven(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        # iemand heeft de instaptoets gehaald, maar is niet ingeschreven
        toets = Instaptoets(
                    is_afgerond=True,
                    geslaagd=True,
                    sporter=self.sporter)
        toets.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_niet_ingeschreven)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/niet-ingeschreven.dtl', 'plein/site_layout.dtl'))

        # nog een keer, maar nu is de sporter wel ingeschreven
        OpleidingInschrijving(
                opleiding=self.opleiding,
                sporter=self.sporter,
                status=OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                nummer=1).save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_niet_ingeschreven)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/niet-ingeschreven.dtl', 'plein/site_layout.dtl'))


# end of file
