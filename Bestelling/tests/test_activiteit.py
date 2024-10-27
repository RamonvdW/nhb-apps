# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD)
from Bestelling.models import Bestelling, BestellingProduct
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_PAYMENT
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Evenement.definities import EVENEMENT_AFMELDING_STATUS_AFGEMELD
from Evenement.models import Evenement, EvenementLocatie, EvenementInschrijving, EvenementAfgemeld
from Functie.models import Functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_KORTING_VERENIGING
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from decimal import Decimal
import datetime


class TestBestellingActiviteit(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module Activiteit """

    test_after = ('Bestelling.tests.test_mandje',)

    url_activiteit = '/bestel/activiteit/'
    url_omzet = '/bestel/omzet/'

    volgende_bestel_nr = 1234567

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save(update_fields=['is_BB'])

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
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
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
        self.sessie = sessie
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
        self.wedstrijd = wedstrijd

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

        bestelling = Bestelling(
                        bestel_nr=1235,
                        account=self.account_admin,
                        ontvanger=self.instellingen_bond,
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
        bestelling.save()
        bestelling.producten.add(product2)
        self.bestelling = bestelling

        locatie = EvenementLocatie(
                        naam='Test',
                        vereniging=ver,
                        adres='Test')
        locatie.save()

        evenement = Evenement(
                        titel='Test',
                        organiserende_vereniging=ver,
                        datum='2000-01-01',
                        locatie=locatie)
        evenement.save()

        inschrijving = EvenementInschrijving(
                            wanneer=now,
                            evenement=evenement,
                            sporter=self.sporter,
                            koper=self.account_admin)
        inschrijving.save()
        self.inschrijving2 = inschrijving

        product = BestellingProduct(
                        evenement_inschrijving=inschrijving,
                        prijs_euro=Decimal('1.23'))
        product.save()
        self.product3 = product
        bestelling.producten.add(product)

    def _maak_bestellingen(self):
        bestel = Bestelling(
                    bestel_nr=self.volgende_bestel_nr,
                    # account=       # van wie is deze bestelling
                    ontvanger=self.instellingen,
                    verkoper_naam='Test',
                    verkoper_adres1='Adres1',
                    verkoper_adres2='Adres2',
                    verkoper_kvk='Kvk',
                    verkoper_email='test@test.not',
                    verkoper_telefoon='tel nr',
                    verkoper_iban='IBAN',
                    verkoper_bic='BIC123',
                    verkoper_heeft_mollie=True,
                    totaal_euro=Decimal('12.34'),
                    status=BESTELLING_STATUS_NIEUW,
                    log='Aangemaakt')
        bestel.save()
        self.bestel1 = bestel
        self.volgende_bestel_nr += 1

        product = BestellingProduct(
                        wedstrijd_inschrijving=self.inschrijving,
                        prijs_euro=Decimal('14.34'),
                        korting_euro='2.00')
        product.save()
        bestel.producten.add(product)

        # product wat geen wedstrijd is
        product = BestellingProduct()
        product.save()
        bestel.producten.add(product)

    def test_activiteit(self):
        # inlog vereist
        self.client.logout()
        resp = self.client.get(self.url_activiteit)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        # geen bestellingen, geen zoekterm
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # slechte zoekterm (veel te lang)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=' + 'haha' * 100)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, gratis filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&gratis=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        afgemeld = EvenementAfgemeld(
                        wanneer_inschrijving=self.inschrijving2.wanneer,
                        nummer=42,
                        wanneer_afgemeld=timezone.now(),
                        status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                        evenement=self.inschrijving2.evenement,
                        sporter=self.inschrijving2.sporter,
                        koper=self.inschrijving2.koper,
                        bedrag_ontvangen=10,
                        bedrag_retour=7.50,
                        log='test\ntest\n')
        afgemeld.save()

        self.product3.evenement_afgemeld = afgemeld
        self.product3.evenement_inschrijving = None
        self.product3.save()

        # lege zoekterm, evenementen filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&evenementen=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, webwinkel filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&webwinkel=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, wedstrijden filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&wedstrijden=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm getal
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=1234')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=test')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        self._maak_bestellingen()

        # zoekterm bestelnummer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=MH-1234')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm nog te betalen / mislukte betalingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=**')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        bestel = Bestelling(
                    bestel_nr=self.volgende_bestel_nr,
                    # account=       # van wie is deze bestelling
                    ontvanger=self.instellingen,
                    verkoper_naam='Test',
                    verkoper_adres1='Adres1',
                    verkoper_adres2='Adres2',
                    verkoper_kvk='Kvk',
                    verkoper_email='test@test.not',
                    verkoper_telefoon='tel nr',
                    verkoper_iban='IBAN',
                    verkoper_bic='BIC123',
                    verkoper_heeft_mollie=True,
                    totaal_euro=Decimal('12.34'),
                    status=BESTELLING_STATUS_AFGEROND,
                    log='Aangemaakt')
        bestel.save()

        bestel.pk = None
        bestel.bestel_nr += 1
        bestel.status = BESTELLING_STATUS_MISLUKT
        bestel.save()

        bestel.pk = None
        bestel.bestel_nr += 1
        bestel.status = BESTELLING_STATUS_GEANNULEERD
        bestel.save()

        transactie = BetaalTransactie(
                            when=timezone.now(),
                            bedrag_handmatig=10)
        transactie.save()
        bestel.transacties.add(transactie)

        transactie = BetaalTransactie(
                            when=timezone.now(),
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                            payment_id='test',
                            payment_status='test',
                            bedrag_te_ontvangen=10,
                            bedrag_terugbetaald=5,
                            bedrag_teruggevorderd=4)
        transactie.save()
        bestel.transacties.add(transactie)

        self.volgende_bestel_nr += 1
        # checkboxes "toon webwinkel" en "toon wedstrijden"
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&webwinkel=on&wedstrijden=on&gratis=ja')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # toon de nieuwste bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_mww)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

    def test_omzet(self):
        # inlog vereist
        self.client.logout()
        resp = self.client.get(self.url_omzet)
        self.assert403(resp)

        ver2 = Vereniging(
                    ver_nr=1001,
                    naam="Tweede Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver2.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver2,
                            akkoord_via_bond=True)
        instellingen.save()

        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_omzet)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/omzet.dtl', 'plein/site_layout.dtl'))

        self._maak_bestellingen()
        bestelling1 = Bestelling.objects.first()
        bestelling1.aangemaakt -= datetime.timedelta(days=60)
        bestelling1.ontvanger = instellingen
        bestelling1.save(update_fields=['aangemaakt', 'ontvanger'])

        self._maak_bestellingen()
        bestelling2 = Bestelling.objects.exclude(pk=bestelling1.pk).first()
        bestelling2.totaal_euro = 0
        bestelling2.save(update_fields=['totaal_euro'])

        self._maak_bestellingen()
        bestelling3 = Bestelling.objects.exclude(pk__in=(bestelling1.pk, bestelling2.pk)).first()
        bestelling3.aangemaakt -= datetime.timedelta(days=60)
        bestelling3.save(update_fields=['aangemaakt'])

        self._maak_bestellingen()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_omzet)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/omzet.dtl', 'plein/site_layout.dtl'))

        # geen is_staff vlag
        self.account_admin.is_staff = False
        self.account_admin.save(update_fields=['is_staff'])

        resp = self.client.get(self.url_omzet)
        self.assert403(resp)


# end of file
