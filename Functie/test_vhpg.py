# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import HanterenPersoonsgegevens
from Functie.models import  account_needs_vhpg
from Functie.view_vhpg import account_vhpg_is_geaccepteerd
from Overig.e2ehelpers import E2EHelpers


class TestFunctieVHPG(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie; module VHPG """

    test_after = ('Functie.test_2fa', 'Functie.wisselvanrol')

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin(accepteer_vhpg=False)
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.url_acceptatie = '/functie/vhpg-acceptatie/'
        self.url_afspraken = '/functie/vhpg-afspraken/'
        self.url_overzicht = '/functie/vhpg-overzicht/'

    def test_anon(self):
        self.e2e_logout()

        # probeer diverse functies zonder ingelogd te zijn
        resp = self.client.get(self.url_overzicht)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_afspraken)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_acceptatie)
        self.assert_is_redirect(resp, '/plein/')

        # doe een post zonder ingelogd te zijn
        resp = self.client.post(self.url_acceptatie, {})
        self.assert_is_redirect(resp, '/plein/')

    def test_niet_nodig(self):
        self.e2e_login(self.account_normaal)
        resp = self.client.get(self.url_acceptatie)
        self.assert_is_redirect(resp, '/plein/')

    def test_admin(self):
        self.e2e_login(self.account_admin)
        resp = self.client.get(self.url_acceptatie, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/vhpg-acceptatie.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'verplicht')

        self.assertEqual(HanterenPersoonsgegevens.objects.count(), 0)
        needs_vhpg, _ = account_needs_vhpg(self.account_admin)
        self.assertTrue(needs_vhpg)

        # voer de post uit zonder checkbox (dit gebeurt ook als de checkbox niet gezet wordt)
        resp = self.client.post(self.url_acceptatie, {}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/vhpg-acceptatie.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'verplicht')

        self.assertEqual(HanterenPersoonsgegevens.objects.count(), 0)

        # voer de post uit met checkbox wel gezet (waarde maakt niet uit)
        resp = self.client.post(self.url_acceptatie, {'accepteert': 'whatever'}, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(HanterenPersoonsgegevens.objects.count(), 1)
        needs_vhpg, _ = account_needs_vhpg(self.account_admin)
        self.assertFalse(needs_vhpg)

        obj = HanterenPersoonsgegevens.objects.all()[0]
        self.assertTrue(str(obj) != "")

        self.e2e_assert_other_http_commands_not_supported(self.url_acceptatie, post=False)

    def test_overzicht(self):
        account_vhpg_is_geaccepteerd(self.account_admin)

        self.e2e_login_and_pass_otp(self.account_admin)

        # is niet BB
        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to plein)

        # wissel naar BB rol
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/vhpg-overzicht.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_afspraken(self):
        self.e2e_login(self.account_admin)

        resp = self.client.get(self.url_afspraken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/vhpg-afspraken.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_afspraken)


# end of file
