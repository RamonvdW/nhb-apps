# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Instaptoets.models import Vraag, Instaptoets
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleiding.models import Opleiding, OpleidingMoment
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from datetime import timedelta


class TestOpleidingBasiscursus(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit Basiscursus """

    test_after = ('Account', 'Functie')

    url_basiscursus = '/opleiding/basiscursus/'
    url_inschrijven_basiscursus = '/opleiding/inschrijven/basiscursus/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.not', 'Normaal')

        ver = Vereniging(
                        ver_nr=1000,
                        naam='Grote club',
                        plaats='Schietstad',
                        regio=Regio.objects.get(regio_nr=116))
        ver.save()

        sporter = Sporter(
                    lid_nr=100000,
                    voornaam='Nor',
                    achternaam='Maal',
                    geboorte_datum='1988-08-08',
                    sinds_datum='2024-02-02',
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
                        kosten_euro=10.00)
        opleiding.save()

        # moment zonder locatie
        moment = OpleidingMoment(
                        datum="2024-11-11",
                        locatie=None)
        moment.save()
        opleiding.momenten.add(moment)

        # moment met locatie met plaats
        locatie = EvenementLocatie(
                        naam='test',
                        vereniging=ver,
                        plaats='Boogstad')
        locatie.save()

        moment = OpleidingMoment(
                        datum="2024-11-12",
                        locatie=locatie)
        moment.save()
        opleiding.momenten.add(moment)

        # moment met locatie zonder plaats
        locatie = EvenementLocatie(
                        naam='test locatie',
                        vereniging=ver,
                        plaats='')
        locatie.save()

        moment = OpleidingMoment(
                        datum="2024-11-13",
                        locatie=locatie)
        moment.save()
        opleiding.momenten.add(moment)

    def test_anon(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

    def test_gast(self):
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        self.e2e_login(self.account_normaal)

        # corner case: geen opleidingen
        Opleiding.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_inschrijven_basiscursus not in urls)

    def test_sporter(self):
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

        # maak de instaptoets beschikbaar
        Vraag().save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

        # instaptoets gehaald
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

        # inschrijven is mogelijk
        # toets opnieuw doen is ook mogelijk (alleen op de test server)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'kan alleen op de test server')

        # inschrijven is mogelijk
        # toets opnieuw doen is niet mogelijk (op de live server)
        with override_settings(IS_TEST_SERVER=False):
            resp = self.client.get(self.url_basiscursus)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))
            self.assertNotContains(resp, 'kan alleen op de test server')

        # instaptoets verlopen
        toets.afgerond = timezone.now() - timedelta(days=400)
        toets.save(update_fields=['afgerond'])

        # corner case: geen momenten
        OpleidingMoment.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/basiscursus.dtl', 'plein/site_layout.dtl'))

# end of file
