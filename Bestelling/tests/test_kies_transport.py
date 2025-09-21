# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Bestelling.definities import (BESTELLING_TRANSPORT_VERZEND, BESTELLING_TRANSPORT_OPHALEN,
                                   BESTELLING_REGEL_CODE_WEBWINKEL)
from Bestelling.models import BestellingMandje, Bestelling, BestellingRegel
from Geo.models import Regio
from Mailer.models import MailQueue
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.definities import VER_NR_BONDSBUREAU
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelKeuze, WebwinkelProduct
from decimal import Decimal


class TestBestellingBestelling(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module Kies Transport """

    test_after = ('Bestelling.tests.test_mandje',)

    url_kies_transport = '/bestel/mandje/transport/'
    url_mandje_bestellen = '/bestel/mandje/'
    url_mandje_toon = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=103))
        ver.save()

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=account,
                        bij_vereniging=ver,
                        postadres_1='Oplegger 5',
                        postadres_2='5678ZZ Boogstad',
                        postadres_3='Nederland',
        )
        sporter.save()
        self.sporter = sporter

        ver = Vereniging.objects.get(ver_nr=VER_NR_BONDSBUREAU)
        ver.naam = 'Bondsbureau'
        ver.adres_regel1 = 'Sportlaan 1'
        ver.adres_regel2 = 'Sportstad'
        ver.kvk_nummer = '123456'
        ver.telefoonnummer = '123456789'
        ver.bank_iban = 'IBAN123456789'
        ver.bank_bic = 'BIC4NL'
        ver.save()

        product = WebwinkelProduct(
                            omslag_titel='test',
                            prijs_euro=Decimal(1.0),
                            #type_verzendkosten=VERZENDKOSTEN_PAKKETPOST
                            )
        product.save()
        self.webwinkel_product = product

    def test_anon(self):
        self.client.logout()

        # inlog vereist
        resp = self.client.get(self.url_kies_transport)
        self.assert403(resp)

        resp = self.client.post(self.url_kies_transport)
        self.assert403(resp)

    def test_view(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        with override_settings(WEBWINKEL_TRANSPORT_OPHALEN_MAG=True):
            # geen mandje
            # BestellingMandje.objects.filter(account=self.account_admin).delete()
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_kies_transport)
            self.assert404(resp, 'Mandje is leeg')

            # leeg mandje
            mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account_admin)

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_kies_transport)
            self.assert404(resp, 'Niet van toepassing')

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_kies_transport)
            self.assert404(resp, 'Niet van toepassing')

            # voeg een webwinkel product toe aan het mandje
            regel = BestellingRegel(
                            korte_beschrijving='webwinkel',
                            bedrag_euro=Decimal(1.23),
                            code=BESTELLING_REGEL_CODE_WEBWINKEL)
            regel.save()
            mandje.regels.add(regel)

            mandje.transport = BESTELLING_TRANSPORT_OPHALEN
            mandje.save(update_fields=['transport'])

            # nu kan er een keuze gemaakt worden
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_kies_transport)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('bestelling/kies-transport.dtl', 'plein/site_layout.dtl'))

            # maak een foutieve wijziging (POST)
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_kies_transport, {'snel': 1})
            self.assert404(resp, 'Verkeerde parameter')

            # maak een foutieve wijziging (POST)
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_kies_transport, {'snel': 1, 'keuze': 'wat hier dan ook moet staan'})
            self.assert404(resp, 'Verkeerde parameter')

    def test_verzend(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        with override_settings(WEBWINKEL_TRANSPORT_OPHALEN_MAG=True):
            # leeg mandje
            mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account_admin)
            mandje.transport = BESTELLING_TRANSPORT_OPHALEN
            mandje.save(update_fields=['transport'])

            # voeg een webwinkel product toe aan het mandje
            regel = BestellingRegel(
                            korte_beschrijving='webwinkel',
                            bedrag_euro=Decimal(1.23),
                            code=BESTELLING_REGEL_CODE_WEBWINKEL)
            regel.save()
            mandje.regels.add(regel)

            keuze = WebwinkelKeuze(
                            wanneer=timezone.now(),
                            bestelling=regel,
                            product=self.webwinkel_product,
                            aantal=1)
            keuze.save()

            # wijzig naar verzenden
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_kies_transport, {'snel': 1, 'keuze': 'verzend'})
            self.assert_is_redirect(resp, self.url_mandje_toon)

            self.verwerk_bestel_mutaties()

            mandje = BestellingMandje.objects.get(pk=mandje.pk)
            self.assertEqual(mandje.transport, BESTELLING_TRANSPORT_VERZEND)

            # bestelling afronden
            self.assertEqual(MailQueue.objects.count(), 0)
            resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
            self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
            self.verwerk_bestel_mutaties()

            self.assertEqual(Bestelling.objects.count(), 1)

            # controleer wat er in de mail staat
            self.assertEqual(MailQueue.objects.count(), 1)
            mail = MailQueue.objects.first()
            # print('{test_verzend}', mail.mail_text)
            self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
            self.assert_consistent_email_html_text(mail, ignore=('>Bedrag:', '>Korting:'))
            self.assertTrue('Verzendkosten' in mail.mail_text)
            self.assertTrue('Levering' in mail.mail_text)
            self.assertFalse('Ophalen' in mail.mail_text)
            self.assertTrue(self.sporter.postadres_2 in mail.mail_text)

        self.e2e_assert_other_http_commands_not_supported(self.url_kies_transport, post=False)

    def test_ophalen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        with override_settings(WEBWINKEL_TRANSPORT_OPHALEN_MAG=True):
            mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account_admin)
            mandje.transport = BESTELLING_TRANSPORT_VERZEND
            mandje.save(update_fields=['transport'])

            # voeg een webwinkel product toe aan het mandje
            regel = BestellingRegel(
                            korte_beschrijving='webwinkel',
                            bedrag_euro=Decimal(1.23),
                            code=BESTELLING_REGEL_CODE_WEBWINKEL)
            regel.save()
            mandje.regels.add(regel)

            keuze = WebwinkelKeuze(
                            wanneer=timezone.now(),
                            bestelling=regel,
                            product=self.webwinkel_product,
                            aantal=1)
            keuze.save()

            # nu kan er een keuze gemaakt worden
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_kies_transport)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('bestelling/kies-transport.dtl', 'plein/site_layout.dtl'))

            # wijzig naar ophalen
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_kies_transport, {'snel': 1, 'keuze': 'ophalen'})
            self.assert_is_redirect(resp, self.url_mandje_toon)
            # coverage: 2e verzoek voor dezelfde mutatie
            self.client.post(self.url_kies_transport, {'snel': 1, 'keuze': 'ophalen'})

            self.verwerk_bestel_mutaties()

            mandje = BestellingMandje.objects.get(pk=mandje.pk)
            self.assertEqual(mandje.transport, BESTELLING_TRANSPORT_OPHALEN)

            # bestelling afronden
            self.assertEqual(MailQueue.objects.count(), 0)
            resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
            self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
            self.verwerk_bestel_mutaties()

            self.assertEqual(Bestelling.objects.count(), 1)

        self.e2e_assert_other_http_commands_not_supported(self.url_kies_transport, post=False)


# end of file
