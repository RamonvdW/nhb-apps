# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import Functie
from Instaptoets.models import Vraag, Instaptoets
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN, OPLEIDING_STATUS_GEANNULEERD
from Opleiding.models import Opleiding, OpleidingInschrijving
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import json


class TestOpleidingInschrijven(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit Inschrijven """

    test_after = ('Account', 'Functie')

    url_inschrijven_basiscursus = '/opleiding/inschrijven/basiscursus/'
    url_toevoegen_aan_mandje = '/opleiding/inschrijven/toevoegen-mandje/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

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

        # maak een basiscursus aan zodat het kaartje Basiscursus getoond wordt op het overzicht
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_jaartal=2024,
                        periode_kwartaal=4,
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True)
        opleiding.save()
        self.opleiding = opleiding

        # geannuleerde opleiding
        opleiding = Opleiding(
                        titel="Test 2",
                        is_basiscursus=True,
                        periode_jaartal=2024,
                        periode_kwartaal=3,
                        beschrijving="Test niet meer",
                        status=OPLEIDING_STATUS_GEANNULEERD)
        opleiding.save()
        self.opleiding_geannuleerd = opleiding

        # niet-basiscursus
        Opleiding(
                titel="Test 3",
                is_basiscursus=False,
                periode_jaartal=2024,
                periode_kwartaal=3,
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
        self.toets = toets
        self.toets_niet_afgerond_datetime = toets.afgerond

    def _zet_instaptoets_gehaald(self):
        now = timezone.now() - datetime.timedelta(days=10)
        Instaptoets.objects.filter(pk=self.toets.pk).update(
                afgerond=now,
                aantal_antwoorden=10,
                is_afgerond=True,
                aantal_goed=9,
                geslaagd=True)

    def _zet_instaptoets_gezakt(self):
        Instaptoets.objects.filter(pk=self.toets.pk).update(
                afgerond=self.toets_niet_afgerond_datetime,
                aantal_antwoorden=10,
                is_afgerond=True,
                aantal_goed=5,
                geslaagd=False)

    def _zet_instaptoets_niet_af(self):
        Instaptoets.objects.filter(pk=self.toets.pk).update(
                afgerond=self.toets_niet_afgerond_datetime,
                aantal_antwoorden=5,
                is_afgerond=False,
                aantal_goed=0,
                geslaagd=False)

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus)
        self.assert404(resp, 'Inlog nodig')

        # geen toets
        Opleiding.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assert404(resp, 'Basiscursus niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje)
        self.assert_is_redirect_login(resp)

    def test_gast(self):
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus)
        self.assert404(resp, 'Inlog nodig')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje)
        self.assert403(resp)

    def test_toets_niet_gestart(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self.toets.delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_toets_niet_af(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_niet_af()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_toets_gezakt(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gezakt()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_toets_gehaald(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [self.url_toevoegen_aan_mandje])

    def test_wijzigen_doorgeven(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # geen JSON
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus)       # geen data
        self.assert404(resp, 'Geen valide verzoek')
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # foute keys
        data = {'niet nodig': 'onverwacht'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # nieuwe gegevens
        data = {'email': 'voor.opleiding@khsn.not',
                'plaats': 'Boogstad',
                'telefoon': '12345'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.aanpassing_email, 'voor.opleiding@khsn.not')
        self.assertEqual(inschrijving.aanpassing_telefoon, '12345')
        self.assertEqual(inschrijving.aanpassing_geboorteplaats, 'Boogstad')

        # geen wijzigingen --> geen toevoegingen aan logboekje
        data = {'email': 'voor.opleiding@khsn.not',
                'plaats': 'Boogstad',
                'telefoon': '12345'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        # get toont ingevoerde gegevens
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))

        # gelijk aan bekende gegevens
        data = {'email': self.sporter.email,
                'plaats': self.sporter.geboorteplaats,
                'telefoon': self.sporter.telefoon}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.aanpassing_email, '')
        self.assertEqual(inschrijving.aanpassing_telefoon, '')
        self.assertEqual(inschrijving.aanpassing_geboorteplaats, '')

        self.assertTrue(inschrijving.korte_beschrijving() != '')
        self.assertTrue(str(inschrijving) != '')

        # corner case: geen basiscursus
        OpleidingInschrijving.objects.all().delete()
        Opleiding.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)

    def test_mandje(self):
        # leg de inschrijving voor de opleiding in het mandje
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # zonder opleiding_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje)
        self.assert404(resp, 'Slecht verzoek')

        # bad opleiding_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': '##'})
        self.assert404(resp, 'Slecht verzoek')

        # niet bestaande opleiding_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': 999999})
        self.assert404(resp, 'Slecht verzoek (2)')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))


# end of file
