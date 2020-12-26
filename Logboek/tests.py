# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from Logboek.apps import post_migration_callback
from NhbStructuur.models import NhbLid
from Overig.e2ehelpers import E2EHelpers
from .models import LogboekRegel, schrijf_in_logboek
from .views import RESULTS_PER_PAGE
import datetime


class TestLogboek(E2EHelpers, TestCase):
    """ unit tests voor de Logboek applicatie """

    test_after = ('Functie',)

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_same = self.e2e_create_account('same', 'same@test.com', 'same')

        lid = NhbLid()
        lid.nhb_nr = 100042
        lid.geslacht = "M"
        lid.voornaam = "Beh"
        lid.achternaam = "eerder"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.account = self.account_normaal
        lid.email = lid.account.email
        lid.save()

        LogboekRegel.objects.all().delete()

        schrijf_in_logboek(self.account_normaal, 'Logboek unittest', 'test setUp')
        schrijf_in_logboek(None, 'Logboek unittest', 'zonder account')
        schrijf_in_logboek(None, 'Records', 'import gelukt')
        schrijf_in_logboek(None, 'Rollen', 'Jantje is de baas')
        schrijf_in_logboek(None, 'NhbStructuur', 'weer een nieuw lid')
        schrijf_in_logboek(None, 'Uitrol', 'Rollen met die hap')
        schrijf_in_logboek(self.account_normaal, 'OTP controle', 'alweer verkeerd')
        schrijf_in_logboek(self.account_same, 'Testafdeling', 'Afdeling gesloten')
        schrijf_in_logboek(self.account_same, 'Competitie', 'Klassegrenzen vastgesteld')
        schrijf_in_logboek(self.account_same, 'Accommodaties', 'Weer een clubhuis')
        schrijf_in_logboek(self.account_same, 'Clusters', 'Groepeer ze maar')
        schrijf_in_logboek(None, 'Iets anders', 'Valt onder Rest')
        schrijf_in_logboek(None, 'oude_site_overnemen (command line)', 'Valt onder Import')

        self.logboek_url = '/logboek/'

    def test_anon(self):
        # do een get van het logboek zonder ingelogd te zijn
        # resulteert in een redirect naar het plein
        self.e2e_logout()
        resp = self.client.get(self.logboek_url)
        self.assert_is_redirect(resp, '/plein/')

    def test_str(self):
        # gebruik de str functie op de Logboek class
        log = LogboekRegel.objects.all()[0]
        msg = str(log)
        self.assertTrue("Logboek unittest" in msg and "normaal" in msg)

    def test_users_forbidden(self):
        # do een get van het logboek met een gebruiker die daar geen rechten toe heeft
        # resulteert rauwe Forbidden
        self.e2e_login_and_pass_otp(self.account_normaal)
        resp = self.client.get(self.logboek_url)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect (naar het plein)

    def test_user_allowed(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.assertTrue(self.account_admin.is_staff)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # alles
        resp = self.client.get(self.logboek_url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # rest
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'rest/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/rest.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'test setUp')
        self.assertContains(resp, 'IT beheerder')

        # records import
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'records/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/records.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'import gelukt')

        # accounts
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'accounts/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/accounts.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'alweer verkeerd')

        # rollen
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'rollen/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/rollen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Jantje is de baas')

        # nhbstructuur / crm import
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'crm-import/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/nhbstructuur.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'weer een nieuw lid')

        # competitie
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'competitie/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/competitie.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Klassegrenzen vastgesteld')

        # accommodaties
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'accommodaties/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/accommodaties.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Weer een clubhuis')

        # clusters
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'clusters/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/clusters.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Groepeer ze maar')

        # uitrol
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'uitrol/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/uitrol.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Rollen met die hap')

        # import
        with self.assertNumQueries(4):
            resp = self.client.get(self.logboek_url + 'import-oude-site/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/import_oude_site.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Valt onder Import')

    def test_pagination(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.assertTrue(self.account_admin.is_staff)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # pagina 1 is altijd op te vragen
        # check that pagination niet aan staat (niet nodig, te weinig regels)
        resp = self.client.get(self.logboek_url + 'crm-import/?page=1')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/nhbstructuur.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'weer een nieuw lid')
        self.assertNotContains(resp, 'chevron_')      # icoon van pagination pijltje

        # test illegale pagina nummers
        resp = self.client.get(self.logboek_url + 'crm-import/?page=999999')
        self.assertEqual(resp.status_code, 404)  # 404 = Not found
        resp = self.client.get(self.logboek_url + 'crm-import/?page=test')
        self.assertEqual(resp.status_code, 404)  # 404 = Not found

        # voeg wat extra regels toe aan het logboek
        # zorg voor 10+ pagina's
        for regel in range(11 * RESULTS_PER_PAGE):
            schrijf_in_logboek(self.account_same, 'NhbStructuur', 'CRM import nummer %s' % regel)
        # for

        # haal pagina 1 op en check dat de pagination nu getoond wordt
        resp = self.client.get(self.logboek_url + 'crm-import/?page=1')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('logboek/nhbstructuur.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'chevron_')      # icoon van pagination pijltje

        # haal pagina 2 op voor alternatieve coverage ('previous' wordt actief)
        resp = self.client.get(self.logboek_url + 'crm-import/?page=2')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # haal pagina 10 op voor alternatieve coverage (de pagina nummers schuiven)
        resp = self.client.get(self.logboek_url + 'crm-import/?page=10')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # haal de hoogste pagina op voor alternatieve coverage (geen 'next')
        resp = self.client.get(self.logboek_url + 'crm-import/?page=12')
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
        self.e2e_assert_other_http_commands_not_supported(self.logboek_url)
        self.e2e_assert_other_http_commands_not_supported(self.logboek_url + 'crm-import/')
        self.e2e_assert_other_http_commands_not_supported(self.logboek_url + 'rollen/')
        self.e2e_assert_other_http_commands_not_supported(self.logboek_url + 'accounts/')
        self.e2e_assert_other_http_commands_not_supported(self.logboek_url + 'records/')

    def test_same(self):
        obj = LogboekRegel.objects.filter(actie_door_account=self.account_same)[0]
        self.assertEqual(obj.bepaal_door(), 'same')

        obj = LogboekRegel.objects.filter(actie_door_account=self.account_normaal)[0]
        self.assertEqual(obj.bepaal_door(), 'normaal (Normaal)')

    def test_zoek(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        # alles
        resp = self.client.get(self.logboek_url + '?zoekterm=Ramon%20de%20Tester')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)


# end of file
