# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from BasisTypen.definities import SCHEIDS_VERENIGING
from Bestelling.definities import BESTELLING_REGEL_CODE_WEBWINKEL
from Bestelling.models import BestellingMandje, BestellingRegel
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from Sporter.models import Sporter
from Registreer.models import GastRegistratie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestPlein(E2EHelpers, TestCase):

    """ tests voor de Plein-applicatie """

    test_after = ('Functie',)

    url_root = '/'
    url_plein = '/plein/'
    url_privacy = '/plein/privacy/'
    url_handleidingen = '/plein/handleidingen/'
    url_niet_ondersteund = '/plein/niet-ondersteund/'
    url_speciale_pagina = '/plein/test-speciale-pagina/%s/'     # code
    url_mandje = '/bestel/mandje/'
    url_registreer_meer_vragen = '/account/registreer/gast/meer-vragen/'
    url_scheids = '/scheidsrechter/'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_100001 = self.e2e_create_account('100001', '100001@test.com', 'Ramon')

        self.functie_bko = maak_functie('BKO Test', 'BKO')

        self.functie_rko = maak_functie('RKO Test', 'RKO')
        self.functie_rko.rayon = Rayon.objects.get(rayon_nr=3)
        self.functie_rko.save()

        self.functie_rcl = maak_functie('RCL Test', 'RCL')
        self.functie_rcl.regio = Regio.objects.get(regio_nr=111)
        self.functie_rcl.save()

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        self.functie_sec = maak_functie('Secretaris vereniging 1000', 'SEC')
        self.functie_sec.vereniging = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie('Hoofdwedstrijdleider 1000', 'HWL')
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie('Wedstrijdleider 1000', 'WL')
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_100001,
                    email=self.account_100001.email)
        sporter.save()
        self.sporter_100001 = sporter

        # maak een lid aan voor de admin
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="M",
                    voornaam="Ad",
                    achternaam="Min",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.testdata.account_admin,
                    email=self.testdata.account_admin.email)
        sporter.save()

        self.functie_mo = maak_functie('Manager Opleidingen', 'MO')
        self.functie_mwz = maak_functie('Manager Wedstrijdzaken', 'MWZ')
        self.functie_mww = maak_functie('Manager Webwinkel', 'MWW')
        self.functie_sup = maak_functie('Support', 'SUP')
        self.functie_cs = maak_functie('Commissie Scheidsrechters', 'CS')

    def test_plein_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_handleidingen)
        self.assert_is_redirect(resp, '/account/login/')

        # check dat de het scheidsrechters kaartje er niet bij zit
        urls = self.extract_all_urls(resp)
        self.assertNotIn(self.url_scheids, urls)

    def test_plein_normaal(self):
        self.e2e_login(self.account_normaal)        # account, maar geen Sporter

        with override_settings(USE_SUBSET_FONT_FILES=False):      # extra coverage for site_layout_fonts.dtl
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_plein)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assertNotContains(resp, '/admin/')
            self.assertNotContains(resp, 'Wissel van rol')
            self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))
            self.assert_html_ok(resp)

        # check dat de het scheidsrechters kaartje er niet bij zit
        urls = self.extract_all_urls(resp)
        self.assertNotIn(self.url_scheids, urls)

    def test_plein_sporter(self):
        # leg iets in het mandje
        mandje, _ = BestellingMandje.objects.get_or_create(account=self.account_100001)
        regel = BestellingRegel(
                        korte_beschrijving='plein',
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()
        mandje.regels.add(regel)

        self.e2e_login(self.account_100001)

        # plein bekijken = mandje opnieuw evalueren
        with override_settings(DEBUG=True):      # extra coverage for site_layout.dtl: menu_toon_schermgrootte
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_plein)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))
            self.assert_html_ok(resp)

        # check dat de mandje-knop erbij zit
        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_mandje in urls)

        # check dat de het scheidsrechters kaartje er niet bij zit
        urls = self.extract_all_urls(resp)
        self.assertNotIn(self.url_scheids, urls)

    def test_plein_scheids(self):
        # sporter met scheidsrechter opleiding
        self.sporter_100001.scheids = SCHEIDS_VERENIGING
        self.sporter_100001.save(update_fields=['scheids'])

        self.account_100001.scheids = self.sporter_100001.scheids
        self.account_100001.save(update_fields=['scheids'])

        self.e2e_login(self.account_100001)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp)
        self.assertIn(self.url_scheids, urls)

    def test_plein_admin(self):
        self.functie_mo.accounts.add(self.testdata.account_admin)

        # voordat de 2FA control gedaan is, geen admin scherm link in het dropdown menu
        self.e2e_login(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wissel van rol')
        urls = [url for url in self.extract_all_urls(resp) if "admin" in url or "beheer" in url]
        self.assertEqual(0, len(urls))

        # simuleer 2FA, waarna het admin scherm in het dropdown menu komt
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Wissel van rol')
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp) if "beheer" in url]
        self.assertEqual(1, len(urls))      # is globaal beschikbaar bij is_staff

        # wissel naar elk van de functies

        # bb
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Manager MH')

        # bko
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'BKO')

        # rko
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.e2e_check_rol('RKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'RKO')

        # rcl
        self.e2e_wissel_naar_functie(self.functie_rcl)
        self.e2e_check_rol('RCL')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'RCL')

        # sec
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Hoofdwedstrijdleider 1000')

        # wl
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wedstrijdleider 1000')

        # mo
        self.e2e_wissel_naar_functie(self.functie_mo)
        self.e2e_check_rol('MO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Manager Opleidingen')

        # mwz
        self.e2e_wissel_naar_functie(self.functie_mwz)
        self.e2e_check_rol('MWZ')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Manager Wedstrijdzaken')

        # mww
        self.e2e_wissel_naar_functie(self.functie_mww)
        self.e2e_check_rol('MWW')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Manager Webwinkel')

        # cs
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Commissie Scheidsrechters')

        # support
        self.e2e_wissel_naar_functie(self.functie_sup)
        self.e2e_check_rol('support')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Support')

        # geen
        self.e2e_wisselnaarrol_gebruiker()
        self.e2e_check_rol('geen')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

    def test_sec(self):
        # login als secretaris
        account_sec = self.account_100001
        self.functie_sec.accounts.add(account_sec)
        self.e2e_account_accepteert_vhpg(account_sec)
        self.e2e_login_and_pass_otp(account_sec)

        # sec
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Secretaris vereniging 1000')
        self.assert_template_used(resp, ('plein/plein-beheerder.dtl', 'plein/site_layout.dtl'))

        # sporter
        self.e2e_wisselnaarrol_sporter()
        self.e2e_check_rol('sporter')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))

    def test_handleidingen(self):
        self.e2e_login(self.testdata.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_handleidingen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/handleidingen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_handleidingen)

    def test_registreer(self):
        # test doorsturen vast een onvolledig gast-account

        lid_nr = 800001
        account = self.e2e_create_account(str(lid_nr), 'ext@test.com', 'Ext van de Ern')
        account.is_gast = True
        account.save(update_fields=['is_gast'])
        gast = GastRegistratie(
                    lid_nr=lid_nr,
                    voornaam='Ext',
                    achternaam='van de Ern',
                    email_is_bevestigd=True,
                    email=account.bevestigde_email,
                    account=account)
        gast.save()

        self.e2e_login_no_check(account)

        # haal 'het plein' op en controleer dat deze doorstuurt naar de 'meer vragen' pagina
        resp = self.client.get(self.url_plein)
        self.assert_is_redirect(resp, self.url_registreer_meer_vragen)


# end of file
