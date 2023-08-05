# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from Logboek.apps import post_migration_callback
from Sporter.models import Sporter
from Logboek.models import LogboekRegel, schrijf_in_logboek
from Logboek.views import RESULTS_PER_PAGE
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestLogboek(E2EHelpers, TestCase):

    """ tests voor de Logboek applicatie """

    test_after = ('Functie',)

    url_logboek = '/logboek/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_same = self.e2e_create_account('same', 'same@test.com', 'same')

        sporter = Sporter()
        sporter.lid_nr = 100042
        sporter.geslacht = "M"
        sporter.voornaam = "Beh"
        sporter.achternaam = "eerder"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.account = self.account_normaal
        sporter.email = sporter.account.email
        sporter.save()

        LogboekRegel.objects.all().delete()

        schrijf_in_logboek(self.account_normaal, 'Logboek unittest', 'test setUp')
        schrijf_in_logboek(None, 'Logboek unittest', 'zonder account')
        schrijf_in_logboek(None, 'Records', 'import gelukt')
        schrijf_in_logboek(None, 'Rollen', 'Jantje is de baas')
        schrijf_in_logboek(None, 'NhbStructuur', 'weer een nieuw lid')
        schrijf_in_logboek(None, 'Betalingen', 'Betalen maar')
        schrijf_in_logboek(None, 'Uitrol', 'Rollen met die hap')
        schrijf_in_logboek(self.account_normaal, 'OTP controle', 'alweer verkeerd')
        schrijf_in_logboek(self.account_same, 'Testafdeling', 'Afdeling gesloten')
        schrijf_in_logboek(self.account_same, 'Competitie', 'Klassengrenzen vastgesteld')
        schrijf_in_logboek(self.account_same, 'Accommodaties', 'Weer een clubhuis')
        schrijf_in_logboek(self.account_same, 'Clusters', 'Groepeer ze maar')
        schrijf_in_logboek(None, 'Iets anders', 'Valt onder Rest')
        schrijf_in_logboek(None, 'oude_site_overnemen (command line)', 'Valt onder Import')

    def test_anon(self):
        # do een get van het logboek zonder ingelogd te zijn
        # resulteert in een redirect naar het plein
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek)
        self.assert403(resp)

    def test_str(self):
        # gebruik de str functie op de Logboek class
        log = LogboekRegel.objects.first()
        self.assertTrue(str(log) != "")

    def test_users_forbidden(self):
        # do een get van het logboek met een gebruiker die daar geen rechten toe heeft
        # resulteert rauwe Forbidden
        self.e2e_login_and_pass_otp(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek)
        self.assert403(resp)

    def test_user_allowed(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.assertTrue(self.account_admin.is_staff)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # alles
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # rest
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'rest/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/rest.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'test setUp')
        self.assertContains(resp, 'IT beheerder')

        # records import
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'records/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/records.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'import gelukt')

        # accounts
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'accounts/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/accounts.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'alweer verkeerd')

        # rollen
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'rollen/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/rollen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Jantje is de baas')

        # nhbstructuur / crm import
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'crm-import/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/nhbstructuur.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'weer een nieuw lid')

        # competitie
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'competitie/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/competitie.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Klassengrenzen vastgesteld')

        # accommodaties
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'accommodaties/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/accommodaties.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Weer een clubhuis')

        # clusters
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'clusters/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/clusters.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Groepeer ze maar')

        # betalingen
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'betalingen/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/betalingen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Betalen maar')

        # uitrol
        with self.assert_max_queries(4):
            resp = self.client.get(self.url_logboek + 'uitrol/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/uitrol.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Rollen met die hap')

    def test_pagination(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.assertTrue(self.account_admin.is_staff)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # pagina 1 is altijd op te vragen
        # check that pagination niet aan staat (niet nodig, te weinig regels)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + 'crm-import/?page=1')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/nhbstructuur.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'weer een nieuw lid')
        self.assertNotContains(resp, 'chevron_')      # icoon van pagination pijltje

        # test illegale pagina nummers
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + 'crm-import/?page=999999')
        self.assert404(resp, 'Ongeldige pagina (999999): Die pagina bevat geen resultaten')     # django vertaling
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + 'crm-import/?page=test')
        self.assert404(resp, 'Pagina is niet')                                                  # django vertaling
        self.assert404(resp, 'en kan ook niet naar een geheel getal worden geconverteerd')      # django vertaling

        # voeg wat extra regels toe aan het logboek
        # zorg voor 10+ pagina's
        for regel in range(11 * RESULTS_PER_PAGE):
            schrijf_in_logboek(self.account_same, 'NhbStructuur', 'CRM import nummer %s' % regel)
        # for

        # haal pagina 1 op en check dat de pagination nu getoond wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + 'crm-import/?page=1')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/nhbstructuur.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'chevron_')      # icoon van pagination pijltje

        # haal pagina 2 op voor alternatieve coverage ('previous' wordt actief)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + 'crm-import/?page=2')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # haal pagina 10 op voor alternatieve coverage (de pagina nummers schuiven)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + 'crm-import/?page=10')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # haal de hoogste pagina op voor alternatieve coverage (geen 'next')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + 'crm-import/?page=12')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

    def test_log_versie(self):
        # trigger de init code die in het logboek schrijft
        post_migration_callback(None)

        # controleer dat er 1 regel met het versienummer toegevoegd is in het logboek
        qset = LogboekRegel.objects.filter(gebruikte_functie='Uitrol', activiteit__contains=settings.SITE_VERSIE)
        self.assertEqual(len(qset), 1)

    def test_other_http(self):
        # als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        self.e2e_assert_other_http_commands_not_supported(self.url_logboek)
        self.e2e_assert_other_http_commands_not_supported(self.url_logboek + 'crm-import/')
        self.e2e_assert_other_http_commands_not_supported(self.url_logboek + 'rollen/')
        self.e2e_assert_other_http_commands_not_supported(self.url_logboek + 'accounts/')
        self.e2e_assert_other_http_commands_not_supported(self.url_logboek + 'records/')

    def test_same(self):
        obj = LogboekRegel.objects.filter(actie_door_account=self.account_same)[0]
        self.assertEqual(obj.bepaal_door(), 'same')

        obj = LogboekRegel.objects.filter(actie_door_account=self.account_normaal)[0]
        self.assertEqual(obj.bepaal_door(), 'normaal (Normaal)')

    def test_zoek(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        # alles
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_logboek + '?zoekterm=Ramon%20de%20Tester')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)


# end of file
