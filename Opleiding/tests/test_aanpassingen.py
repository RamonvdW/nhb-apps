# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from Functie.models import Functie
from Geo.models import Regio
from Instaptoets.models import Vraag, Instaptoets
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleiding.models import Opleiding, OpleidingInschrijving
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestOpleidingAanpassingen(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit Aanpassingen """

    test_after = ('Account', 'Functie', 'Opleiding.tests.test_basiscursus')

    url_aanpassingen = '/opleiding/manager/aanpassingen/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

        ver_bond = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam='Bondsbureau',
                        plaats='Schietstad',
                        regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

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

        # maak de basiscursus aan
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_begin="2024-11-01",
                        periode_einde="2024-12-01",
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True,
                        kosten_euro=10.00)
        opleiding.save()
        self.opleiding = opleiding

        # maak de instaptoets beschikbaar
        Vraag().save()

        # instaptoets is gehaald
        now = timezone.now() - datetime.timedelta(days=10)
        toets = Instaptoets(
                    afgerond=now,
                    sporter=sporter,
                    aantal_vragen=10,
                    aantal_antwoorden=10,
                    is_afgerond=True,
                    aantal_goed=9,
                    geslaagd=True)
        toets.save()
        self.toets = toets

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanpassingen)
        self.assert_is_redirect_login(resp)

    def test_beheerder(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)
        self.e2e_check_rol('MO')

        # geen inschrijvingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanpassingen)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanpassingen.dtl', 'plein/site_layout.dtl'))

        # maak een inschrijving aan
        OpleidingInschrijving(
                opleiding=self.opleiding,
                sporter=self.sporter,
                aanpassing_geboorteplaats='Bad Vizier').save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanpassingen)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanpassingen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Bad Vizier')

        # nadat het CRM ge-update is moet deze aanpassing niet meer getoond worden
        self.sporter.geboorteplaats = 'Bad Vizier'
        self.sporter.save(update_fields=['geboorteplaats'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanpassingen)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanpassingen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Bad Vizier')

        # corner case
        self.e2e_wisselnaarrol_sporter()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanpassingen)
        self.assert403(resp, 'Geen toegang')


# end of file
