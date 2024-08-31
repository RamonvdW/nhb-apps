# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestel.definities import BESTEL_MUTATIE_VERWIJDER, BESTEL_TRANSPORT_VERZEND, BESTEL_TRANSPORT_OPHALEN
from Bestel.models import BestelProduct, Bestelling, BestelMutatie, BestelMandje
from Betaal.models import BetaalInstellingenVereniging
from Functie.models import Functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Registreer.models import GastRegistratie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_KORTING_COMBI, WEDSTRIJD_KORTING_VERENIGING
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from decimal import Decimal


class TestBestelMandje(E2EHelpers, TestCase):

    """ tests voor de Bestel applicatie, module mandje """

    url_mandje_toon = '/bestel/mandje/'
    url_mandje_verwijder = '/bestel/mandje/verwijderen/%s/'        # inhoud_pk
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

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_bond,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_bond = instellingen

        self.assertEqual(settings.BETAAL_VIA_BOND_VER_NR, settings.WEBWINKEL_VERKOPER_VER_NR)

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

        boog_r = BoogType.objects.get(afkorting='R')

        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog.save()

        now = timezone.now()
        datum = now.date()      # pas op met testen ronde 23:59

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres='Schietweg 1, Boogdorp',
                        plaats='Boogdrop')
        locatie.save()
        locatie.verenigingen.add(ver)

        sessie = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    max_sporters=50)
        sessie.save()
        # sessie.wedstrijdklassen.add()

        # maak een kalenderwedstrijd aan, met sessie
        wedstrijd = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=ver,
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        # wedstrijd.boogtypen.add()

        wkls_r = KalenderWedstrijdklasse.objects.filter(boogtype=boog_r, buiten_gebruik=False)

        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_r[0],
                            sporterboog=sporterboog,
                            koper=account)
        inschrijving.save()
        self.inschrijving = inschrijving

        korting = WedstrijdKorting(
                    geldig_tot_en_met=datum,
                    soort=WEDSTRIJD_KORTING_VERENIGING,
                    uitgegeven_door=ver,
                    percentage=42)
        korting.save()
        korting.voor_wedstrijden.add(wedstrijd)
        self.korting = korting

        self.functie_mww = Functie.objects.filter(rol='MWW').first()

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        bestel_begrenzing='1-5',
                        eenheid='test,tests',
                        bevat_aantal=6,
                        prijs_euro="1.23")
        product.save()
        self.product = product

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        koper=self.account_admin,
                        product=product,
                        aantal=2,
                        totaal_euro=Decimal('1.23'),
                        log='test')
        keuze.save()
        self.keuze = keuze

    def _vul_mandje(self, account, transport=BESTEL_TRANSPORT_VERZEND):

        mandje, is_created = BestelMandje.objects.get_or_create(account=account)

        # geen koppeling aan een mandje
        product1 = BestelProduct(
                    wedstrijd_inschrijving=self.inschrijving,
                    prijs_euro=Decimal(10.0))
        product1.save()

        # stop het product in het mandje
        mandje.producten.add(product1)

        product2 = BestelProduct(
                        webwinkel_keuze=self.keuze,
                        prijs_euro=Decimal(1.23))
        product2.save()
        mandje.producten.add(product2)

        mandje.transport = transport
        mandje.save(update_fields=['transport'])

        return product1, product2

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
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_mandje_toon, post=False)

        # controleer dat er geen knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertFalse(self.url_kies_transport in urls)

        # vul het mandje
        product1, product2 = self._vul_mandje(self.account_admin)

        with override_settings(WEBWINKEL_TRANSPORT_OPHALEN_MAG=True):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # controleer dat er nu wel een knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_kies_transport in urls)

        # corner case: sporter zonder vereniging
        self.sporter.bij_vereniging = None
        self.sporter.save()

        # corner case: te hoge korting
        product1.korting_euro = 999
        product1.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # koppel een korting
        self.inschrijving.korting = self.korting
        self.inschrijving.save()

        # veroorzaak een uitzondering
        self.instellingen_bond.mollie_api_key = ''
        self.instellingen_bond.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # verander de korting in een combi-korting
        self.korting.soort = WEDSTRIJD_KORTING_COMBI
        self.korting.save()

        # leg een product in het mandje wat geen wedstrijd inschrijving is
        product = BestelProduct()
        product.save()
        self.assertTrue(str(product) != '')
        self.assertTrue(product.korte_beschrijving() != '')

        mandje = BestelMandje.objects.get(account=self.account_admin)
        mandje.producten.add(product)
        self.assertTrue(str(mandje) != '')

        self.instellingen.akkoord_via_bond = False
        self.instellingen.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Onbekend product')

        mandje.delete()
        resp = self.client.post(self.url_mandje_toon)
        self.assert404(resp, 'Mandje niet gevonden')

        # veroorzaak een exception
        BetaalInstellingenVereniging.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

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
        self.assertTrue(product1.korte_beschrijving() != '')

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

        self.verwerk_bestel_mutaties()

        # maak een verwijder mutatie aan zonder product
        BestelMutatie(
            code=BESTEL_MUTATIE_VERWIJDER,
            account=self.account_admin).save()

        # maak een eigen verwijder mutatie met onbekend product
        product = BestelProduct()
        product.save()
        BestelMutatie(
            code=BESTEL_MUTATIE_VERWIJDER,
            product=product,
            account=self.account_admin).save()

        mandje = BestelMandje.objects.get(account=self.account_admin)
        mandje.producten.add(product)

        f1, f2 = self.verwerk_bestel_mutaties(show_warnings=False, fail_on_error=False)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(": Type niet ondersteund" in f1.getvalue())
        self.assertTrue(" niet meer in het mandje gevonden" in f2.getvalue())

        # nog een keer verwijderen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product1.pk, {'snel': 1})
        self.assert404(resp, 'Niet gevonden in jouw mandje')

        # verwijderen zonder mandje
        product1, product2 = self._vul_mandje(self.account_admin)
        product2.korting_euro = 1
        self.assertTrue(str(product2) != '')
        self.assertTrue(product2.korte_beschrijving() != '')

        mandje = BestelMandje.objects.get(account=self.account_admin)
        mandje.producten.clear()
        mandje.delete()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product1.pk, {'snel': 1})
        self.assert404(resp, 'Niet gevonden')

    def test_bestellen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')
        url = self.url_mandje_toon

        # vul het mandje
        self._vul_mandje(self.account_admin)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        Bestelling.objects.all().delete()

        # doe de bestelling
        self.assertEqual(0, BestelMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.assertEqual(1, BestelMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())

        mutatie = BestelMutatie.objects.first()
        self.assertTrue(str(mutatie) != '')
        mutatie.code = 99999
        mutatie.is_verwerkt = True
        self.assertTrue(str(mutatie) != '')

        # nog een keer, dan bestaat de mutatie al (is_created is False)
        resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.assertEqual(1, BestelMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())

        self.verwerk_bestel_mutaties()

        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.first()
        self.assertTrue(str(bestelling) != '')

    def test_transport(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # leeg mandje
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # controleer dat er geen knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertFalse(self.url_kies_transport in urls)

        # vul het mandje
        product1, product2 = self._vul_mandje(self.account_admin, BESTEL_TRANSPORT_OPHALEN)
        # product1 = wedstrijd
        # product2 = webwinkel

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # controleer dat er geen knop is om transport in te stellen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertFalse(self.url_kies_transport in urls)


# end of file
