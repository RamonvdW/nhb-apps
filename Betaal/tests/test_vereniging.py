# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Betaal.models import BetaalInstellingenVereniging
from Functie.operations import maak_functie
from NhbStructuur.models import NhbVereniging, NhbRegio
from TestHelpers.e2ehelpers import E2EHelpers


class TestBetaalMutaties(E2EHelpers, TestCase):

    """ tests voor de Betaal-applicatie, interactie achtergrond taak met CPSP """

    url_ver_instellingen = '/bestel/betaal/vereniging/instellingen/'

    def setUp(self):
        self.account = self.e2e_create_account_admin()

        self.regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_111
        ver.save()
        self.nhbver = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

    def test_instellen(self):
        # anon
        resp = self.client.get(self.url_ver_instellingen)
        self.assert_is_redirect(resp, '/account/login/')

        # login in en wissel naar HWL
        self.e2e_login_and_pass_otp(self.account)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # nu mag de pagina wel gebruikt worden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ver_instellingen)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('betaal/vereniging-instellingen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wijzigen in lege sleutel mag
        # (=verwijder sleutel, maar ook op Opslaan drukken zonder iets ingevuld te hebben)
        resp = self.client.post(self.url_ver_instellingen)
        self.assert_is_redirect(resp, '/wedstrijden/vereniging/')

        resp = self.client.post(self.url_ver_instellingen, {'apikey': 'blabla fout'})
        self.assert404(resp, 'Niet geaccepteerd')

        resp = self.client.post(self.url_ver_instellingen, {'apikey': 'test_12345'})
        self.assert_is_redirect(resp, '/wedstrijden/vereniging/')

        # ophalen met instellingen opgeslagen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ver_instellingen)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('betaal/vereniging-instellingen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # zet de "akkoord via NHB" optie
        instellingen = BetaalInstellingenVereniging.objects.all()[0]
        self.assertEqual(instellingen.mollie_api_key, 'test_12345')
        instellingen.akkoord_via_nhb = True
        instellingen.save()

        # ophalen met instellingen opgeslagen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ver_instellingen)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('betaal/vereniging-instellingen.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Ja, betalingen aan jullie lopen via de NHB rekening')

# end of file
