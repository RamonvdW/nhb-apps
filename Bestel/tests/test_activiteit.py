# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestel.models import (Bestelling, BestelProduct,
                           BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_WACHT_OP_BETALING, BESTELLING_STATUS_NIEUW,
                           BESTELLING_STATUS_MISLUKT)
from Betaal.models import BetaalInstellingenVereniging
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Wedstrijden.models import (Wedstrijd, WedstrijdSessie, WEDSTRIJD_STATUS_GEACCEPTEERD, WedstrijdLocatie,
                                WedstrijdInschrijving, WedstrijdKorting,
                                INSCHRIJVING_STATUS_RESERVERING_MANDJE, INSCHRIJVING_STATUS_RESERVERING_BESTELD,
                                INSCHRIJVING_STATUS_DEFINITIEF, INSCHRIJVING_STATUS_AFGEMELD)
from decimal import Decimal


class TestBestelActiviteit(E2EHelpers, TestCase):

    """ tests voor de Bestel applicatie, module Activiteit """

    test_after = ('Bestel.test_mandje',)

    url_activiteit = '/bestel/activiteit/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save(update_fields=['is_BB'])

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
                    regio=NhbRegio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer = '12345678')
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
                    uitgegeven_door=ver,
                    voor_vereniging=ver,
                    percentage=42)
        korting.save()
        korting.voor_wedstrijden.add(wedstrijd)
        self.korting = korting

    def _maak_bestellingen(self):
        bestel = Bestelling(
                    bestel_nr=1234567,
                    #account=       # van wie is deze bestelling
                    ontvanger=self.instellingen,
                    verkoper_naam='Test',
                    verkoper_adres1='Adres1',
                    verkoper_adres2='Adres2',
                    verkoper_kvk='Kvk',
                    verkoper_email='test@nhb.not',
                    verkoper_telefoon='telnr',
                    verkoper_iban='IBAN',
                    verkoper_bic='BICBIC',
                    verkoper_heeft_mollie=True,
                    totaal_euro=Decimal('12.34'),
                    status=BESTELLING_STATUS_NIEUW,
                    log='Aangemaakt')
        bestel.save()
        self.bestel1 = bestel

        product = BestelProduct(
                        wedstrijd_inschrijving=self.inschrijving,
                        prijs_euro=Decimal('14.34'),
                        korting_euro='2.00')
        product.save()
        bestel.producten.add(product)

        # product wat geen wedstrijd is
        product = BestelProduct()
        product.save()
        bestel.producten.add(product)

        # de opgestarte betaling/restitutie wordt hier bijgehouden
        # de BetaalMutatie wordt opgeslagen zodat deze is aangemaakt. Daarin zet de achtergrond taak een payment_id.
        # daarmee kunnen we het BetaalActief record vinden met de status van de betaling en de log
        #betaal_mutatie = models.ForeignKey(BetaalMutatie, on_delete=models.SET_NULL, null=True, blank=True)
        #betaal_actief = models.ForeignKey(BetaalActief, on_delete=models.SET_NULL, null=True, blank=True)

        # de afgeronde betalingen: ontvangst en restitutie
        #transacties = models.ManyToManyField(BetaalTransactie, blank=True)

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
        self.assert_template_used(resp, ('bestel/activiteit.dtl', 'plein/site_layout.dtl'))

        # slechte zoekterm (veel te lang)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=' + 'haha' * 100)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm getal
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=1234')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=test')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/activiteit.dtl', 'plein/site_layout.dtl'))

        self._maak_bestellingen()

        # toon de nieuwste bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/activiteit.dtl', 'plein/site_layout.dtl'))


# end of file
