# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestel.models import BestelMandje, BestelProduct
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from decimal import Decimal
import datetime


class TestBestelCli(E2EHelpers, TestCase):
    """ unittests voor de Bestel applicatie, management command bestel_mutaties """

    def _leg_webwinkel_in_mandje(self, verleden):

        webwinkel_product = WebwinkelProduct(
                                omslag_titel='Test titel 1',
                                onbeperkte_voorraad=True,
                                bestel_begrenzing='',
                                prijs_euro="1.23")
        webwinkel_product.save()

        keuze = WebwinkelKeuze(
                        wanneer=verleden,
                        koper=self.mandje.account,
                        product=webwinkel_product,
                        aantal=1,
                        totaal_euro=Decimal('1.23'),
                        log='test 1')
        keuze.save()
        product = BestelProduct(
                        webwinkel_keuze=keuze,
                        prijs_euro=Decimal('1.23'))
        product.save()
        self.mandje.producten.add(product)

        # tweede webwinkel product
        keuze = WebwinkelKeuze(
                        wanneer=verleden,
                        koper=self.mandje.account,
                        product=webwinkel_product,
                        aantal=2,
                        totaal_euro=Decimal('2.46'),
                        log='test 2')
        keuze.save()
        product = BestelProduct(
                        webwinkel_keuze=keuze,
                        prijs_euro=Decimal('1.23'))
        product.save()
        self.mandje.producten.add(product)

    def _leg_wedstrijd_in_mandje(self, now, verleden):
        datum = now.date()      # pas op met testen ronde 23:59

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

        sporter1 = Sporter(
                        lid_nr=100001,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.mandje.account,
                        bij_vereniging=ver)
        sporter1.save()

        sporter2 = Sporter(
                        lid_nr=100002,
                        voornaam='Bet',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-07',
                        sinds_datum='2020-02-02',
                        account=self.mandje.account,
                        bij_vereniging=ver)
        sporter2.save()

        boog_r = BoogType.objects.get(afkorting='R')

        sporterboog1_r = SporterBoog(
                            sporter=sporter1,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog1_r.save()

        sporterboog2_r = SporterBoog(
                            sporter=sporter2,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog2_r.save()

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres='Schietweg 1, Boogdorp',
                        plaats='Boogdrop')
        locatie.save()
        locatie.verenigingen.add(ver)

        # maak een kalenderwedstrijd aan, met sessie
        sessie = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    max_sporters=50)
        sessie.save()

        wedstrijd = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=ver,
                        contact_email='organisatie@ver.not',
                        contact_telefoon='0600000001',
                        contact_naam='Organ is a Tie',
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)

        wkls_r = KalenderWedstrijdklasse.objects.filter(boogtype=boog_r, buiten_gebruik=False)

        inschrijving = WedstrijdInschrijving(
                            wanneer=verleden,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_r[0],
                            sporterboog=sporterboog1_r,
                            koper=self.mandje.account)
        inschrijving.save()

        product = BestelProduct(
                        wedstrijd_inschrijving=inschrijving,
                        prijs_euro=Decimal('10.00'))
        product.save()
        self.mandje.producten.add(product)

        inschrijving = WedstrijdInschrijving(
                            wanneer=verleden,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_r[0],
                            sporterboog=sporterboog2_r,
                            koper=self.mandje.account)
        inschrijving.save()

        product = BestelProduct(
                        wedstrijd_inschrijving=inschrijving,
                        prijs_euro=Decimal('10.00'))
        product.save()
        self.mandje.producten.add(product)

    def setUp(self):
        """ initialisatie van de test case """

        self.account = self.e2e_create_account_admin()

        mandje, is_created = BestelMandje.objects.get_or_create(account=self.account)
        self.mandje = mandje

    def test_opschonen1(self):
        # bestel_mutaties doorloopt bij elke opstart alle mandjes
        # en verwijdert producten die al te lang in het mandje liggen

        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)

        self._leg_wedstrijd_in_mandje(now, verleden)

        mandje = BestelMandje.objects.get(pk=self.mandje.pk)
        self.assertEqual(2, mandje.producten.count())

        with self.assert_max_queries(26):
            f1, f2, = self.run_management_command('bestel_mutaties', '--quick', '1')

        # print("\nf1: %s\nf2: %s" % (f1.getvalue(), f2.getvalue()))

        self.assertTrue("[INFO] Opschonen mandjes begin" in f2.getvalue())

        # controleer de inhoud van het mandje
        mandje = BestelMandje.objects.get(pk=mandje.pk)
        self.assertEqual(0, mandje.producten.count())

    def test_opschonen2(self):
        # bestel_mutaties doorloopt bij elke opstart alle mandjes
        # en verwijdert producten die al te lang in het mandje liggen

        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)

        self._leg_webwinkel_in_mandje(verleden)

        mandje = BestelMandje.objects.get(pk=self.mandje.pk)
        self.assertEqual(2, mandje.producten.count())

        with self.assert_max_queries(32):
            f1, f2, = self.run_management_command('bestel_mutaties', '--quick', '1')

        # print("\nf1: %s\nf2: %s" % (f1.getvalue(), f2.getvalue()))

        self.assertTrue("[INFO] Opschonen mandjes begin" in f2.getvalue())

        # controleer de inhoud van het mandje
        mandje = BestelMandje.objects.get(pk=mandje.pk)
        self.assertEqual(0, mandje.producten.count())

# end of file
