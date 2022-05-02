# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType
from Bestel.models import BestelProduct, BestelMandje, BestelMutatie, Bestelling
from Betaal.models import BetaalInstellingenVereniging
from Kalender.models import (KalenderWedstrijd, KalenderWedstrijdSessie, WEDSTRIJD_STATUS_GEACCEPTEERD,
                             KalenderInschrijving, KalenderWedstrijdKortingscode, KALENDER_KORTING_COMBI)
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Wedstrijden.models import WedstrijdLocatie
from decimal import Decimal


class TestMandje(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie """

    url_mandje_toon = '/bestel/mandje/'
    url_mandje_verwijder = '/bestel/mandje/verwijderen/%s/'        # inhoud_pk
    url_mandje_code_toevoegen = '/bestel/mandje/code-toevoegen/'
    url_bestellingen_overzicht = '/bestel/overzicht/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        ver_nhb = NhbVereniging(
                    ver_nr=settings.BETAAL_VIA_NHB_VER_NR,
                    naam='Bondsbureau',
                    plaats='Schietstad',
                    regio=NhbRegio.objects.get(regio_nr=100))
        ver_nhb.save()
        self.ver_nhb = ver_nhb

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_nhb,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_nhb = instellingen

        ver = NhbVereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=NhbRegio.objects.get(regio_nr=112))
        ver.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_nhb=True)
        instellingen.save()
        self.instellingen = instellingen

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=account,
                        bij_vereniging=ver)
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

        sessie = KalenderWedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    prijs_euro=10.00,
                    max_sporters=50)
        sessie.save()
        # sessie.wedstrijdklassen.add()

        # maak een kalenderwedstrijd aan, met sessie
        wedstrijd = KalenderWedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=ver,
                        voorwaarden_a_status_when=now)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        # wedstrijd.boogtypen.add()

        inschrijving = KalenderInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=sporterboog,
                            koper=account)
        inschrijving.save()
        self.inschrijving = inschrijving

        self.code = 'TESTJE1234'
        korting = KalenderWedstrijdKortingscode(
                    code=self.code,
                    geldig_tot_en_met=datum,
                    uitgegeven_door=ver,
                    voor_vereniging=ver,
                    percentage=42)
        korting.save()
        korting.voor_wedstrijden.add(wedstrijd)
        self.korting = korting

    def _vul_mandje(self, account):

        mandje, is_created = BestelMandje.objects.get_or_create(account=account)

        # geen koppeling aan een mandje
        product = BestelProduct(
                    inschrijving=self.inschrijving,
                    prijs_euro=Decimal(10.0))
        product.save()

        # stop het product in het mandje
        mandje.producten.add(product)

        return product

    def test_anon(self):
        self.client.logout()

        # inlog vereist voor mandje
        resp = self.client.get(self.url_mandje_toon)
        self.assert403(resp)

        resp = self.client.get(self.url_mandje_code_toevoegen)
        self.assert403(resp)

        resp = self.client.get(self.url_mandje_verwijder)
        self.assert403(resp)

    def test_bekijk_mandje(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')
        url = self.url_mandje_toon

        # leeg mandje
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # vul het mandje
        inhoud = self._vul_mandje(self.account_admin)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # corner case: sporter zonder vereniging
        self.sporter.bij_vereniging = None
        self.sporter.save()

        # corner case: te hoge korting
        inhoud.korting_euro = 999
        inhoud.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # koppel een korting
        self.inschrijving.gebruikte_code = self.korting
        self.inschrijving.save()

        # veroorzaak een uitzondering
        self.instellingen_nhb.mollie_api_key = ''
        self.instellingen_nhb.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # verander de korting in een combi-korting
        self.korting.soort = KALENDER_KORTING_COMBI
        self.korting.save()

        # leg een product in het mandje wat geen wedstrijd inschrijving is
        product = BestelProduct()
        product.save()
        self.assertTrue(str(product) != '')
        self.assertTrue(product.korte_beschrijving() != '')

        mandje = BestelMandje.objects.get(account=self.account_admin)
        mandje.producten.add(product)
        self.assertTrue(str(mandje) != '')

        self.instellingen.akkoord_via_nhb = False
        self.instellingen.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Onbekend product')

        # veroorzaak een exception
        BetaalInstellingenVereniging.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

    def test_kortingscode(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # vul het mandje
        product = self._vul_mandje(self.account_admin)

        # zonder code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_code_toevoegen)
        self.assert_is_redirect(resp, self.url_mandje_toon)

        # niet bestaande code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_code_toevoegen, {'code': 'hallo'})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        # numerieke code
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_code_toevoegen, {'code': 99999})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        # controleer dat de code nog niet toegepast is
        inschrijving = KalenderInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertIsNone(inschrijving.gebruikte_code)

        # pas de code toe, inclusief garbage
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_code_toevoegen,
                                    {'code': '@@' + self.code + '!',   # troep wordt verwijderd
                                     'snel': 1})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        self.verwerk_bestel_mutaties()

        # controleer dat de code toegepast is
        inschrijving = KalenderInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertIsNotNone(inschrijving.gebruikte_code)
        self.assertEqual(inschrijving.gebruikte_code.code, self.code)

        product = BestelProduct.objects.get(pk=product.pk)
        self.assertTrue(str(product) != '')

        # mandje tonen met kortingscode
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-mandje.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, '10,00')    # prijs sessie
        self.assertContains(resp, '4,20')     # korting
        self.assertContains(resp, '5,80')     # totaal

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
        product = self._vul_mandje(self.account_admin)
        self.assertTrue(str(product) != '')
        self.assertTrue(product.korte_beschrijving() != '')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % 999999)
        self.assert404(resp, 'Niet gevonden in jouw mandje')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        self.verwerk_bestel_mutaties()

        # nog een keer verwijderen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product.pk, {'snel': 1})
        self.assert404(resp, 'Niet gevonden in jouw mandje')

        # verwijderen zonder mandje
        product = self._vul_mandje(self.account_admin)
        mandje = BestelMandje.objects.get(account=self.account_admin)
        mandje.producten.clear()
        mandje.delete()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % product.pk, {'snel': 1})
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

        # doe de bestelling
        self.assertEqual(0, BestelMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.assertEqual(1, BestelMutatie.objects.count())
        self.assertEqual(0, Bestelling.objects.count())

        mutatie = BestelMutatie.objects.all()[0]
        self.assertTrue(str(mutatie) != '')
        mutatie.code = 99999
        mutatie.is_verwerkt = True
        self.assertTrue(str(mutatie) != '')

        self.verwerk_bestel_mutaties()

        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.all()[0]
        self.assertTrue(str(bestelling) != '')


# end of file
