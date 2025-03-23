# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.conf import settings
from Bestelling.definities import (BESTELLING_TRANSPORT_VERZEND, BESTELLING_TRANSPORT_OPHALEN,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD, BESTELLING_REGEL_CODE_WEBWINKEL)
from Bestelling.models import Bestelling, BestellingMutatie, BestellingMandje, BestellingRegel
from Betaal.models import BetaalInstellingenVereniging
from Geo.models import Regio
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal


class TestBestellingMandje(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module mandje """

    url_mandje_toon = '/bestel/mandje/'
    url_mandje_verwijder = '/bestel/mandje/verwijderen/%s/'        # product_pk (=BestellingRegel pk)
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_kies_transport = '/bestel/mandje/transport/'

    url_meer_vragen = '/account/registreer/gast/meer-vragen/'
    url_plein = '/plein/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        ver_bond = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam='Bondsbureau',
                        plaats='Schietstad',
                        regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112))
        ver.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_bond=True)
        instellingen.save()
        self.instellingen = instellingen

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=account,
                        bij_vereniging=ver,
                        postadres_1='Postadres1')
        sporter.save()
        self.sporter = sporter

    @staticmethod
    def _vul_mandje(account, transport=BESTELLING_TRANSPORT_VERZEND):

        mandje, is_created = BestellingMandje.objects.get_or_create(account=account)

        regel1 = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    bedrag_euro=Decimal(10.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel1.save()
        mandje.regels.add(regel1)

        regel2 = BestellingRegel(
                        korte_beschrijving='webwinkel',
                        bedrag_euro=Decimal(1.23),
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel2.save()
        mandje.regels.add(regel2)

        mandje.transport = transport
        mandje.save(update_fields=['transport'])

        return regel1, regel2

    def test_anon(self):
        self.client.logout()

        # inlog vereist voor mandje
        resp = self.client.get(self.url_mandje_toon)
        self.assert403(resp)

        resp = self.client.get(self.url_mandje_verwijder)
        self.assert403(resp)

    def test_bekijk_mandje(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # begin met Het Plein, want die gebruik eval_mandje_inhoud
        resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))

        # tweede keer is de timestamp gezet
        resp = self.client.get(self.url_plein)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))

        # leeg mandje
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_mandje_toon, post=False)

        # controleer dat er geen knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertFalse(self.url_kies_transport in urls)

        # vul het mandje
        regel1, regel2 = self._vul_mandje(self.account_admin)

        with override_settings(WEBWINKEL_TRANSPORT_OPHALEN_MAG=True):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # controleer dat er nu wel een knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_kies_transport in urls)

        mandje = BestellingMandje.objects.get(account=self.account_admin)
        # self.assertTrue(str(mandje) != '')

        self.instellingen.akkoord_via_bond = False
        self.instellingen.save()

        # corner case: geen geld beloven
        regel1.bedrag_euro = -900.0
        regel1.save(update_fields=['bedrag_euro'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        mandje.delete()
        resp = self.client.post(self.url_mandje_toon)
        self.assert404(resp, 'Mandje niet gevonden')

        # corner case
        BetaalInstellingenVereniging.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

    def test_gast(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # gast-account
        self.account_admin.is_gast = True
        self.account_admin.save(update_fields=['is_gast'])

        gast = GastRegistratie(
                    lid_nr=self.account_admin.username,
                    voornaam=self.account_admin.first_name,
                    achternaam=self.account_admin.last_name,
                    email_is_bevestigd=True,
                    email=self.account_admin.bevestigde_email,
                    account=self.account_admin)
        gast.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assert_is_redirect(resp, self.url_meer_vragen)

        gast.fase = REGISTRATIE_FASE_COMPLEET
        gast.save(update_fields=['fase'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # test_gast.py checkt invoeren afleveradres

    def test_verwijder(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % 'hallo')
        self.assert404(resp, 'Verkeerde parameter')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % '1=5')
        self.assert404(resp, 'Verkeerde parameter')

        # vul het mandje
        product1, product2 = self._vul_mandje(self.account_admin)
        # product1 = wedstrijd
        # product2 = webwinkel
        self.assertTrue(str(product1) != '')

        resp = self.client.post(self.url_mandje_verwijder % 999999)
        self.assert404(resp, 'Niet gevonden in jouw mandje')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product1.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        # nog een keer, dan is de mutatie al aangemaakt (is_created is False)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product1.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product2.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        # laat de achtergrondtaak de producten verwijderen uit het mandje
        self.verwerk_bestel_mutaties()

        # nog een keer verwijderen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product1.pk, {'snel': 1})
        self.assert404(resp, 'Niet gevonden in jouw mandje')

        # verwijderen zonder mandje
        mandje = BestellingMandje.objects.get(account=self.account_admin)
        mandje.regels.clear()
        mandje.delete()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product1.pk, {'snel': 1})
        self.assert404(resp, 'Niet gevonden')

    def test_bestellen_ophalen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')
        url = self.url_mandje_toon

        # vul het mandje
        self._vul_mandje(self.account_admin, transport=BESTELLING_TRANSPORT_OPHALEN)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        Bestelling.objects.all().delete()

        # doe de bestelling
        self.assertEqual(0, BestellingMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.assertEqual(1, BestellingMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())

        mutatie = BestellingMutatie.objects.first()
        self.assertTrue(str(mutatie) != '')
        mutatie.code = 99999
        mutatie.is_verwerkt = True
        self.assertTrue(str(mutatie) != '')

        # nog een keer, dan bestaat de mutatie al (is_created is False)
        resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.assertEqual(1, BestellingMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())

        self.verwerk_bestel_mutaties()

        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.first()
        self.assertTrue(str(bestelling) != '')

    def test_bestellen_verzend(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')
        url = self.url_mandje_toon

        # vul het mandje (webwinkel + wedstrijd)
        self._vul_mandje(self.account_admin)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        Bestelling.objects.all().delete()

        # doe de bestelling
        self.assertEqual(0, BestellingMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.assertEqual(1, BestellingMutatie.objects.count())

        self.assertEqual(0, Bestelling.objects.count())
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

    def test_transport(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # leeg mandje
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # controleer dat er geen knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertFalse(self.url_kies_transport in urls)

        # vul het mandje
        product1, product2 = self._vul_mandje(self.account_admin, BESTELLING_TRANSPORT_OPHALEN)
        # product1 = wedstrijd
        # product2 = webwinkel

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # controleer dat er nu wel een knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_kies_transport in urls)

        # verwijder het webwinkel product
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product2.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        self.verwerk_bestel_mutaties()

        # controleer dat de transport knop nu niet getoond wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertFalse(self.url_kies_transport in urls)

# end of file
