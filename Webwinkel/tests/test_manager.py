# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelFoto


class TestWebwinkelOverzicht(E2EHelpers, TestCase):

    """ tests voor de Webwinkel applicatie, module: Overzicht """

    url_manager = '/webwinkel/manager/'
    url_voorraad = '/webwinkel/manager/voorraad/'

    def setUp(self):
        """ initialisatie van de test case """

        self.lid_nr = 123456

        self.account_email = 'winkel@test.not'
        self.account_normaal = self.e2e_create_account(self.lid_nr, self.account_email, 'Mgr', accepteer_vhpg=True)

        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        sporter1 = Sporter(
                    lid_nr=self.lid_nr,
                    geslacht='M',
                    voornaam='Mgr',
                    achternaam='Winkel',
                    geboorte_datum='1977-07-07',
                    sinds_datum='2020-07-07',
                    adres_code='1234AB56',
                    account=self.account_normaal,
                    bij_vereniging=self.ver1,
                    postadres_1='Sporter straatnaam 1',
                    postadres_2='Sporter woonplaats',
                    postadres_3='Sporter land')
        sporter1.save()
        self.sporter1 = sporter1

        self.functie_mww = Functie.objects.get(rol='MWW')
        self.functie_mww.accounts.add(self.account_normaal)
        self.functie_mww.bevestigde_email = 'webshop@test.not'
        self.functie_mww.save(update_fields=['bevestigde_email'])

        foto = WebwinkelFoto()
        foto.save()

        foto2 = WebwinkelFoto(
                        locatie='test_1.jpg',
                        locatie_thumb='test_1_thumb.jpg')
        foto2.save()
        self.foto2 = foto2

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        volgorde=1,
                        onbeperkte_voorraad=True,
                        omslag_foto=foto,
                        bestel_begrenzing='',
                        prijs_euro="1.23")
        product.save()
        self.product = product

        product2 = WebwinkelProduct(
                        omslag_titel='Test titel 2',
                        volgorde=2,
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='doos,dozen',
                        bestel_begrenzing='1-20',
                        prijs_euro="42.00")
        product2.save()
        self.product2 = product2

        product3 = WebwinkelProduct(
                        omslag_titel='Test titel 3',
                        volgorde=3,
                        sectie='x',
                        eenheid='meervoud',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=0)           # uitverkocht
        product3.save()
        self.product3 = product3
        self.product3.fotos.add(foto2)

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_manager)
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_voorraad)
        self.assert_is_redirect_login(resp)

        self.e2e_login_and_pass_otp(self.account_normaal)

        resp = self.client.get(self.url_manager)
        self.assert403(resp)

        resp = self.client.get(self.url_voorraad)
        self.assert403(resp)

    def test_mww(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mww)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/manager.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorraad)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/voorraad.dtl', 'design/site_layout.dtl'))

# end of file
