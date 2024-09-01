# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Bestelling.definities import BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_AFGEROND
from Bestelling.models import Bestelling
from Functie.models import Functie
from Geo.models import Regio
from Mailer.models import MailQueue
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelFoto, WebwinkelKeuze


class TestWebwinkelOverzicht(E2EHelpers, TestCase):

    """ tests voor de Webwinkel applicatie, module: Overzicht """

    url_webwinkel_overzicht = '/webwinkel/'
    url_webwinkel_manager = '/webwinkel/manager/'
    url_webwinkel_product = '/webwinkel/product-%s/'     # product_pk

    url_mandje_bestellen = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_overboeking_ontvangen = '/bestel/vereniging/overboeking-ontvangen/'

    url_meer_vragen = '/account/registreer/gast/meer-vragen/'

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

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/overzicht.dtl', 'plein/site_layout.dtl'))

        # controleer dat het mandje niet getoond wordt
        urls = self.extract_all_urls(resp)
        self.assertNotIn(self.url_mandje_bestellen, urls)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_product % self.product.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/product.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post(self.url_webwinkel_product % self.product.pk)
        self.assert404(resp, 'Geen toegang')

        # controleer dat het mandje niet getoond wordt
        urls = self.extract_all_urls(resp)
        self.assertNotIn(self.url_mandje_bestellen, urls)

        self.assertTrue(str(self.foto2) != '')
        self.assertTrue(str(self.product3) != '')

        self.product3.kleding_maat = 'M'
        self.assertTrue(str(self.product3) != '')

    def test_sporter(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_webwinkel_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/overzicht.dtl', 'plein/site_layout.dtl'))

        # controleer dat het mandje wel getoond wordt
        urls = self.extract_all_urls(resp)
        self.assertIn(self.url_mandje_bestellen, urls)

        url = self.url_webwinkel_product % self.product.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/product.dtl', 'plein/site_layout.dtl'))

        # controleer dat het mandje wel getoond wordt
        urls = self.extract_all_urls(resp)
        self.assertIn(self.url_mandje_bestellen, urls)

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
            resp = self.client.get(self.url_webwinkel_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/manager.dtl', 'plein/site_layout.dtl'))

    def test_mandje(self):
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
        self.assert404(resp, 'Foutieve parameter (2)')

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

    def test_bestel(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        self.assertEqual(0, WebwinkelKeuze.objects.count())

        url = self.url_webwinkel_product % self.product.pk
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

        self.assertEqual(2, WebwinkelKeuze.objects.count())

        self.verwerk_bestel_mutaties()

        keuze = WebwinkelKeuze.objects.first()
        self.assertTrue(keuze.korte_beschrijving() != '')
        self.assertTrue(str(keuze) != '')

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()

        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        self.assertEqual(1, MailQueue.objects.count())
        email = MailQueue.objects.first()

        # print(email.mail_text)

        self.assertEqual(email.mail_to, self.account_email)
        self.assertTrue("Bestelling op MijnHandboogsport (MH-100" in email.mail_subj)

        self.assertTrue("Deze e-mail is de bevestiging van je bestelling op MijnHandboogsport" in email.mail_text)
        self.assertTrue("Betaalstatus: Te betalen" in email.mail_text)

        self.assertTrue('Test titel 1' in email.mail_text)
        self.assertTrue('Aantal: 1 stuks' in email.mail_text)
        self.assertTrue('€ 1,23' in email.mail_text)

        self.assertTrue('Test titel 2' in email.mail_text)
        self.assertTrue('Aantal: 2 dozen' in email.mail_text)
        self.assertTrue('€ 84,00' in email.mail_text)

        self.assertTrue('Verzendkosten' in email.mail_text)

        self.assertTrue('TOTAAL: € 91,98' in email.mail_text)

        email.delete()

        # wissel naar de MWW
        self.e2e_wissel_naar_functie(self.functie_mww)

        # overboeking doorgeven
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': bestelling.bestel_nr,
                                     'bedrag': bestelling.totaal_euro,
                                     'actie': 'registreer', 'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        self.verwerk_bestel_mutaties()

        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        # koper en backoffice krijgen mails
        self.assertEqual(2, MailQueue.objects.count())
        email = MailQueue.objects.filter(mail_subj__contains='Verstuur webwinkel producten')[0]

        self.assertTrue("Mgr Winkel" in email.mail_text)
        self.assertTrue("Sporter straatnaam 1" in email.mail_text)
        self.assertTrue("Sporter woonplaats" in email.mail_text)
        self.assertTrue("Sporter land" in email.mail_text)

        self.assertTrue("Betaalstatus: Voldaan" in email.mail_text)
        self.assertTrue('Verzendkosten' in email.mail_text)

        self.assertTrue('TOTAAL: € 91,98' in email.mail_text)

        self.assertTrue('Betaling:' in email.mail_text)
        self.assertTrue('Ontvangen: € 91,98' in email.mail_text)
        self.assertTrue('Beschrijving: Overboeking ontvangen' in email.mail_text)

        email.delete()

        email = MailQueue.objects.first()

        self.assertEqual(email.mail_to, self.account_email)
        self.assertTrue("Bevestiging aankoop via MijnHandboogsport (MH-100" in email.mail_subj)
        self.assertTrue("Betaalstatus: Voldaan" in email.mail_text)

    def test_gast(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_sporter()

        # gast-account
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        url = self.url_webwinkel_product % self.product.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/product.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal': '1', 'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('webwinkel/toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

# end of file
