# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_AFGEROND,
                                   BESTELLING_STATUS_GEANNULEERD)
from Bestelling.models import BestellingProduct, Bestelling, BestellingMutatie
from Betaal.models import BetaalInstellingenVereniging
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from decimal import Decimal


class TestBestellingOverboeking(E2EHelpers, TestCase):

    """ tests voor de applicatie Bestelling, module Overboeking """

    url_overboeking_ontvangen = '/bestel/vereniging/overboeking-ontvangen/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112))
        ver.save()
        self.ver1 = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_bond=False)
        instellingen.save()
        self.instellingen = instellingen

        ver_webshop = Vereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)
        instellingen_webshop = BetaalInstellingenVereniging(
                                    vereniging=ver_webshop,
                                    akkoord_via_bond=False)
        instellingen_webshop.save()
        self.instellingen_webshop = instellingen_webshop

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

        product = BestellingProduct(
                    wedstrijd_inschrijving=inschrijving,
                    prijs_euro=Decimal(10.0))
        product.save()

        bestelling = Bestelling(
                        bestel_nr=1234,
                        account=self.account_admin,
                        ontvanger=instellingen,
                        verkoper_naam='Ver naam',
                        verkoper_adres1='Ver adres 1',
                        verkoper_adres2='Ver adres 2',
                        verkoper_kvk='Ver Kvk',
                        verkoper_email='contact@ver.not',
                        verkoper_telefoon='0123456789',
                        verkoper_iban='NL2BANK0123456789',
                        verkoper_bic='VER2BIC',
                        verkoper_heeft_mollie=False,
                        totaal_euro='10.50',
                        status=BESTELLING_STATUS_BETALING_ACTIEF,
                        log='Een beginnetje\n')
        bestelling.save()
        bestelling.producten.add(product)
        self.bestelling = bestelling

        ver2 = Vereniging(
                    ver_nr=1001,
                    naam="Andere Club",
                    regio=Regio.objects.get(regio_nr=113))
        ver2.save()
        self.ver2 = ver2

        self.functie_mww = Functie.objects.filter(rol='MWW').first()

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=True,
                        bestel_begrenzing='',
                        prijs_euro="1.23")
        product.save()
        self.product = product

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        koper=self.account_admin,
                        product=product,
                        aantal=1,
                        totaal_euro=Decimal('1.23'),
                        log='test')
        keuze.save()

        product2 = BestellingProduct(
                        webwinkel_keuze=keuze,
                        prijs_euro=Decimal(1.23))
        product2.save()
        self.product2 = product2

        bestelling2 = Bestelling(
                        bestel_nr=1235,
                        account=self.account_admin,
                        ontvanger=instellingen_webshop,
                        verkoper_naam='Ver naam',
                        verkoper_adres1='Ver adres 1',
                        verkoper_adres2='Ver adres 2',
                        verkoper_kvk='Ver Kvk',
                        verkoper_email='contact@ver.not',
                        verkoper_telefoon='0123456799',
                        verkoper_iban='NL2BANK0123456799',
                        verkoper_bic='VER2BIC',
                        verkoper_heeft_mollie=False,
                        totaal_euro='1.23',
                        status=BESTELLING_STATUS_BETALING_ACTIEF,
                        log='Een beginnetje\n')
        bestelling2.save()
        bestelling2.producten.add(product2)
        self.bestelling2 = bestelling2

    def test_anon(self):
        self.client.logout()

        # inlog en HWL rol vereist
        resp = self.client.get(self.url_overboeking_ontvangen)
        self.assert403(resp)

        resp = self.client.post(self.url_overboeking_ontvangen)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        resp = self.client.get(self.url_overboeking_ontvangen)
        self.assert403(resp)

    def test_invoeren(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overboeking_ontvangen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overboeking_ontvangen, post=False)

        # gaan parameters --> invoerscherm wordt weer getoond
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        # bedrag, maar geen bestelnummer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'bedrag': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Bestelnummer wordt niet herkend')

        # bestelnummer, maar geen bedrag
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': '1234'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Bestelnummer wordt niet herkend')
        self.assertContains(resp, 'Verwacht bedrag:')

        # bestelnummer + bedrag
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen, {'kenmerk': '1234', 'bedrag': '1', 'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Bestelnummer wordt niet herkend')
        self.assertContains(resp, 'Verwacht bedrag:')

        # juiste informatie maar geen bevestiging van de gebruiker
        self.assertEqual(self.bestelling.status, BESTELLING_STATUS_BETALING_ACTIEF)
        self.assertEqual(0, self.bestelling.transacties.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': '1234', 'bedrag': '10,50', 'actie': 'check'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        # juiste informatie en bevestiging van de gebruiker
        self.assertEqual(self.bestelling.status, BESTELLING_STATUS_BETALING_ACTIEF)
        self.assertEqual(0, self.bestelling.transacties.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': '1234', 'bedrag': '10,50', 'actie': 'registreer', 'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        # coverage: 2e verzoek voor dezelfde mutatie
        resp = self.client.post(self.url_overboeking_ontvangen,
                                {'kenmerk': '1234', 'bedrag': '10,50', 'actie': 'registreer', 'snel': '1'})

        self.assertEqual(1, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Overboeking 10.50 euro ontvangen voor bestelling MH-1234" in f2.getvalue())
        self.assertTrue("[INFO] Betaling is gelukt voor bestelling MH-1234" in f2.getvalue())
        self.bestelling = Bestelling.objects.get(pk=self.bestelling.pk)
        self.assertEqual(self.bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertEqual(1, self.bestelling.transacties.count())
        transactie = self.bestelling.transacties.first()

        # bestelling is al afgerond
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': '1234', 'bedrag': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Betaling is al geregistreerd')
        # self.bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
        # self.bestelling.save(update_fields=['status'])

        # bestelling is geannuleerd
        self.bestelling.status = BESTELLING_STATUS_GEANNULEERD
        self.bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': '1234', 'bedrag': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Bestelling is geannuleerd')

        # bestelling voor andere vereniging
        self.instellingen.vereniging = self.ver2
        self.instellingen.save(update_fields=['vereniging'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': '1234', 'bedrag': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Bestelnummer is niet voor jullie vereniging')

    def test_mww(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_mww)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overboeking_ontvangen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        # juiste informatie en bevestiging van de gebruiker
        self.assertEqual(self.bestelling2.status, BESTELLING_STATUS_BETALING_ACTIEF)
        self.assertEqual(0, self.bestelling2.transacties.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': self.bestelling2.bestel_nr, 'bedrag': '1,23',
                                     'actie': 'registreer', 'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Overboeking 1.23 euro ontvangen voor bestelling MH-1235" in f2.getvalue())
        self.assertTrue("[INFO] Betaling is gelukt voor bestelling MH-1235" in f2.getvalue())
        self.bestelling2 = Bestelling.objects.get(pk=self.bestelling2.pk)
        self.assertEqual(self.bestelling2.status, BESTELLING_STATUS_AFGEROND)
        self.assertEqual(1, self.bestelling2.transacties.count())

    def test_afwijkend_bedrag(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_mww)

        self.bestelling2.status = BESTELLING_STATUS_NIEUW
        self.bestelling2.save(update_fields=['status'])

        # afwijkend bedrag
        self.assertEqual(0, BestellingMutatie.objects.count())
        self.assertEqual(0, self.bestelling2.transacties.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': self.bestelling2.bestel_nr, 'bedrag': '1,00',   # moet zijn: 1,23
                                     'actie': 'registreer', 'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, 'Afwijkend bedrag')
        self.assertEqual(0, BestellingMutatie.objects.count())
        self.assertEqual(0, self.bestelling2.transacties.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': self.bestelling2.bestel_nr, 'bedrag': '1,00',   # moet zijn: 1,23
                                     'actie': 'registreer', 'accept_bedrag': 'ja', 'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()

        self.assertTrue("[INFO] Overboeking 1.00 euro ontvangen voor bestelling MH-1235" in f2.getvalue())
        self.bestelling2 = Bestelling.objects.get(pk=self.bestelling2.pk)
        self.assertEqual(self.bestelling2.status, BESTELLING_STATUS_BETALING_ACTIEF)
        self.assertEqual(1, self.bestelling2.transacties.count())

# end of file
