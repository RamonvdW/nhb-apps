# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.operations import Functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Webwinkel.models import WebwinkelProduct, WebwinkelFoto


class TestWebwinkelOverzicht(E2EHelpers, TestCase):

    """ tests voor de Webwinkel applicatie, module: Overzicht """

    url_webwinkel_overzicht = '/webwinkel/'
    url_webwinkel_product = '/webwinkel/product-%s/'     # product_pk

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

        foto = WebwinkelFoto()
        foto.save()

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=True,
                        omslag_foto=foto,
                        bestel_begrenzing='')
        product.save()
        self.product = product

        product2 = WebwinkelProduct(
                        omslag_titel='Test titel 2',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='doos,dozen',
                        bestel_begrenzing='1-20')
        product2.save()
        self.product2 = product2

        product3 = WebwinkelProduct(
                        omslag_titel='Test titel 3',
                        sectie='x',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=0)           # uitverkocht
        product3.save()
        self.product3 = product3

        foto2 = WebwinkelFoto(
                        locatie='test_1.jpg',
                        locatie_thumb='test_1_thumb.jpg')
        foto2.save()
        self.product3.fotos.add(foto2)

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_overzicht)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_product % self.product.pk)
        self.assert403(resp)

    def test_sporter(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/overzicht.dtl', 'plein/site_layout.dtl'))

        url = self.url_webwinkel_product % self.product.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/product.dtl', 'plein/site_layout.dtl'))

        url = self.url_webwinkel_product % self.product2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/product.dtl', 'plein/site_layout.dtl'))

        url = self.url_webwinkel_product % self.product3.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/product.dtl', 'plein/site_layout.dtl'))

        # corner cases
        url = self.url_webwinkel_product % "xxx"
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Product niet gevonden')

        self.product2.mag_tonen = False
        self.product2.save(update_fields=['mag_tonen'])
        url = self.url_webwinkel_product % self.product2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Product niet gevonden')

        url = self.url_webwinkel_product % self.product3.pk
        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_mww(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mww)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/overzicht.dtl', 'plein/site_layout.dtl'))

    def test_bestel(self):

        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        url = self.url_webwinkel_product % self.product.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': '1', 'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        url = self.url_webwinkel_product % self.product3.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': '1', 'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        url = self.url_webwinkel_product % self.product2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': '2', 'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        # corner cases
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})        # geen 'aantal'
        self.assert404(resp, 'Foutieve parameter')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': ''})
        self.assert404(resp, 'Foutieve parameter')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': 'xxx'})
        self.assert404(resp, 'Foutieve parameter')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': '999'})
        self.assert404(resp, 'Foutieve parameter (2)')

        url = self.url_webwinkel_product % self.product3.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': '0'})
        self.assert404(resp, 'Foutieve parameter (2)')

        url = self.url_webwinkel_product % self.product3.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': '5'})
        self.assert404(resp, 'Foutieve parameter (2)')

        url = self.url_webwinkel_product % "xxx"
        resp = self.client.post(url, {})
        self.assert404(resp, 'Product niet gevonden')


# end of file
