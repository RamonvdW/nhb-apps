# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import Functie
from Geo.models import Regio
from Instaptoets.models import Vraag, Instaptoets
from Opleiding import admin
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN, OPLEIDING_STATUS_GEANNULEERD
from Opleiding.models import OpleidingDiploma, Opleiding
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestOpleidingOverzicht(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit Overzicht """

    test_after = ('Account', 'Functie')

    url_overzicht = '/opleiding/'
    url_details = '/opleiding/details/%s/'      # opleiding_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.not', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

        # maak een test vereniging
        self.ver = Vereniging(
                        ver_nr=1000,
                        naam="Grote Club",
                        regio=Regio.objects.get(regio_nr=112))
        self.ver.save()

        self.functie_hwl = Functie(
                                beschrijving='HWL ver 1000',
                                rol='HWL',
                                bevestigde_email='hwl@khsn.not',
                                vereniging=self.ver)
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_normaal)

        self.functie_sec = Functie(
                                beschrijving='SEC ver 1000',
                                rol='SEC',
                                bevestigde_email='sec@khsn.not',
                                vereniging=self.ver)
        self.functie_sec.save()
        self.functie_sec.accounts.add(self.account_normaal)

        now = timezone.now()
        sporter = Sporter(
                    lid_nr=100001,
                    voornaam='Thea',
                    achternaam='de Tester',
                    unaccented_naam='Thea de Tester',
                    email='normaal@test.not',
                    geboorte_datum="1970-11-15",
                    geslacht='V',
                    sinds_datum='2000-01-01',
                    lid_tot_einde_jaar=now.year,
                    account=self.account_normaal)
        sporter.save()
        self.sporter = sporter

        # maak een basiscursus aan zodat het kaartje Basiscursus getoond wordt op het overzicht
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_begin="2024-11-01",
                        periode_einde="2024-12-01",
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True,
                        ingangseisen='test')
        opleiding.save()
        self.opleiding = opleiding
        self.opleiding.refresh_from_db()

        diploma = OpleidingDiploma(
                        sporter=sporter,
                        code='123',
                        beschrijving='Test diploma')
        diploma.save()
        self.diploma = diploma

        # geannuleerde opleiding
        opleiding = Opleiding(
                        titel="Test 2",
                        is_basiscursus=False,
                        periode_begin="2024-02-01",
                        periode_einde="2024-03-01",
                        beschrijving="Test niet meer",
                        status=OPLEIDING_STATUS_GEANNULEERD)
        opleiding.save()
        self.opleiding_geannuleerd = opleiding

        # niet-basiscursus
        Opleiding(
                titel="Test 3",
                is_basiscursus=False,
                periode_begin="2024-02-01",
                periode_einde="2024-03-01",
                beschrijving="Test nog steeds",
                status=OPLEIDING_STATUS_INSCHRIJVEN).save()

        # maak de instaptoets beschikbaar
        Vraag().save()

        # instaptoets in progress
        toets = Instaptoets(
                    sporter=sporter,
                    aantal_vragen=10,
                    aantal_antwoorden=5)
        toets.save()

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht.dtl', 'design/site_layout.dtl'))

        url = self.url_details % self.opleiding.pk

        # geeft hint inloggen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/details.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'Om in te schrijven op deze opleiding moet je een account aanmaken en inloggen')

        self.assertTrue(str(self.diploma) != '')
        self.assertTrue(str(self.opleiding) != '')

        opleiding = self.opleiding
        opleiding.periode_begin = datetime.date(year=2024, month=10, day=1)
        opleiding.periode_einde = datetime.date(year=2024, month=10, day=1)
        self.assertTrue(opleiding.periode_str() == 'oktober 2024')

        opleiding.periode_begin = datetime.date(year=2024, month=10, day=1)
        opleiding.periode_einde = datetime.date(year=2024, month=11, day=1)
        self.assertTrue(opleiding.periode_str() == 'oktober tot november 2024')

        opleiding.periode_begin = datetime.date(year=2024, month=11, day=1)
        opleiding.periode_einde = datetime.date(year=2025, month=1, day=1)
        self.assertTrue(opleiding.periode_str() == 'november 2024 tot januari 2025')

    def test_sporter(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht.dtl', 'design/site_layout.dtl'))

        url = self.url_details % self.opleiding_geannuleerd.pk

        # kan (nog) niet aanmelden
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/details.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'deze opleiding is GEANNULEERD')

        # instaptoets gehaald --> kan aanmelden
        now = timezone.now()
        toets = Instaptoets(
                    sporter=self.sporter,
                    afgerond=now,
                    aantal_vragen=1,
                    aantal_antwoorden=1,
                    is_afgerond=True,
                    aantal_goed=1,
                    geslaagd=True)
        toets.save()

        url = self.url_details % self.opleiding.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/details.dtl', 'design/site_layout.dtl'))

        resp = self.client.get(self.url_details % 999999)
        self.assert404(resp, 'Slechte parameter')

    def test_gast(self):
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht.dtl', 'design/site_layout.dtl'))

        url = self.url_details % self.opleiding.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/details.dtl', 'design/site_layout.dtl'))

    def test_beheerders(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        url = self.url_details % self.opleiding_geannuleerd.pk

        # MO
        self.e2e_wissel_naar_functie(self.functie_mo)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/details.dtl', 'design/site_layout.dtl'))

        # SEC
        self.e2e_wissel_naar_functie(self.functie_sec)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/details.dtl', 'design/site_layout.dtl'))

        # HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/details.dtl', 'design/site_layout.dtl'))

    def test_admin(self):
        # FUTURE: migreer naar Beheer/tests
        # GastRegistratieFaseFilter
        worker = (admin.HeeftAccountFilter(None,
                                           {'heeft_account': 'Nee'},
                                           OpleidingDiploma,
                                           admin.OpleidingDiplomaAdmin))
        _ = worker.queryset(None, OpleidingDiploma.objects.all())

        worker = (admin.HeeftAccountFilter(None,
                                           {'heeft_account': 'Ja'},
                                           OpleidingDiploma,
                                           admin.OpleidingDiplomaAdmin))
        _ = worker.queryset(None, OpleidingDiploma.objects.all())

# end of file
