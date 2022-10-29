# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.operations import Functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers


class TestWebwinkelPrototype(E2EHelpers, TestCase):

    """ tests voor de Webwinkel applicatie, module ... """

    url_webwinkel_prototype = '/webwinkel/prototype/'

    def setUp(self):
        """ initialisatie van de test case """

        self.lid_nr = 123456

        self.account_normaal = self.e2e_create_account(self.lid_nr, 'winkel@nhb.not', 'Mgr', accepteer_vhpg=True)

        self.nhbver1 = NhbVereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.nhbver1.save()

        sporter1 = Sporter(
                    lid_nr=self.lid_nr,
                    geslacht='M',
                    voornaam='Mgr',
                    achternaam='Winkel',
                    geboorte_datum='1977-07-07',
                    sinds_datum='2020-07-07',
                    adres_code='1234AB56',
                    account=self.account_normaal,
                    bij_vereniging=self.nhbver1)
        sporter1.save()
        self.sporter1 = sporter1

        self.functie_mww = Functie.objects.get(rol='MWW')
        self.functie_mww.accounts.add(self.account_normaal)

    def test_anon(self):
        self.client.logout()
        resp = self.client.get(self.url_webwinkel_prototype)
        self.assert403(resp)

    def test_niet_mww(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        resp = self.client.get(self.url_webwinkel_prototype)
        self.assert403(resp)

    def test_mww(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mww)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_prototype)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/prototype.dtl', 'plein/site_layout.dtl'))

# end of file
