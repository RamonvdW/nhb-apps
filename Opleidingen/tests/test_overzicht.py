# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Opleidingen import admin
from Opleidingen.models import OpleidingDiploma
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers


class TestFunctieOverzicht(E2EHelpers, TestCase):

    """ tests voor de Opleidingen applicatie, functionaliteit Overzicht """

    test_after = ('Account', 'Functie')

    url_overzicht = '/opleidingen/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/overzicht.dtl', 'plein/site_layout.dtl'))

        sporter = Sporter(lid_nr=1)
        deelnemer = OpleidingDiploma(sporter=sporter, code='1234', beschrijving='test')
        self.assertTrue(str(deelnemer) != '')

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

    def test_mo(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleidingen/overzicht.dtl', 'plein/site_layout.dtl'))

# end of file
