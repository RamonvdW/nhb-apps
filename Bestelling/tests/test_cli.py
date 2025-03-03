# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.models import BestellingMandje, Bestelling
from Bestelling.models.product_obsolete import BestellingProduct
from Betaal.models import BetaalInstellingenVereniging
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement, EvenementInschrijving
from Functie.models import Functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie, EvenementLocatie
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleiding.models import Opleiding, OpleidingInschrijving
from Sporter.models import Sporter, SporterBoog
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from decimal import Decimal
import datetime


class TestBestellingCli(E2EHelpers, TestCase):

    """ unittests voor de Bestelling applicatie, management command bestel_mutaties """

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
        product = BestellingProduct(
                        webwinkel_keuze=keuze,
                        prijs_euro=Decimal('1.23'))
        product.save()
        self.product1 = product
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
        product = BestellingProduct(
                        webwinkel_keuze=keuze,
                        prijs_euro=Decimal('1.23'))
        product.save()
        self.product2 = product
        self.mandje.producten.add(product)

    def _leg_wedstrijd_in_mandje(self, now, verleden):
        datum = now.date()      # pas op met testen ronde 23:59

        sporter1 = Sporter(
                        lid_nr=100001,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.mandje.account,
                        bij_vereniging=self.ver)
        sporter1.save()

        sporter2 = Sporter(
                        lid_nr=100002,
                        voornaam='Bet',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-07',
                        sinds_datum='2020-02-02',
                        account=self.mandje.account,
                        bij_vereniging=self.ver)
        sporter2.save()
        self.sporter = sporter2

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
        locatie.verenigingen.add(self.ver)

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
                        organiserende_vereniging=self.ver,
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

        product = BestellingProduct(
                        wedstrijd_inschrijving=inschrijving,
                        prijs_euro=Decimal('10.00'))
        product.save()
        self.product3 = product
        self.mandje.producten.add(product)

        inschrijving = WedstrijdInschrijving(
                            wanneer=verleden,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_r[0],
                            sporterboog=sporterboog2_r,
                            koper=self.mandje.account)
        inschrijving.save()

        product = BestellingProduct(
                        wedstrijd_inschrijving=inschrijving,
                        prijs_euro=Decimal('10.00'))
        product.save()
        self.mandje.producten.add(product)

    def _leg_evenement_in_mandje(self, now, verleden):
        locatie = EvenementLocatie(
                    naam='Arnhemhal',
                    vereniging=self.ver,
                    adres='Papendallaan 9\n6816VD Arnhem',
                    plaats='Arnhem')
        locatie.save()

        now_date = now.date()
        soon_date = now_date + datetime.timedelta(days=60)

        evenement = Evenement(
                        titel='Test evenement',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=self.ver,
                        datum=soon_date,
                        aanvang='09:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        contact_naam='Dhr. Organisator',
                        contact_email='info@test.not',
                        contact_website='www.test.not',
                        contact_telefoon='023-1234567',
                        beschrijving='Test beschrijving',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement.save()
        self.evenement = evenement

        sporter = Sporter(
                        lid_nr=100001,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.mandje.account,
                        bij_vereniging=self.ver)
        sporter.save()

        inschrijving = EvenementInschrijving(
                            wanneer=verleden,
                            evenement=evenement,
                            sporter=sporter,
                            koper=self.account)
        inschrijving.save()

        product = BestellingProduct(
                        evenement_inschrijving=inschrijving,
                        prijs_euro=Decimal('15.0'))
        product.save()
        self.mandje.producten.add(product)

    def _leg_opleiding_in_mandje(self, now, verleden):
        sporter = Sporter(
                    lid_nr=100001,
                    voornaam='Thea',
                    achternaam='de Tester',
                    unaccented_naam='Thea de Tester',
                    email='normaal@test.nhb',
                    geboorte_datum="1970-11-15",
                    geboorteplaats='Pijlstad',
                    geslacht='V',
                    sinds_datum='2000-01-01',
                    telefoon='+123456789',
                    lid_tot_einde_jaar=now.year,
                    account=self.account)
        sporter.save()
        self.sporter = sporter

        # maak een basiscursus aan zodat het kaartje Basiscursus getoond wordt op het overzicht
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_begin="2024-11-01",
                        periode_einde="2024-12-01",
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True,
                        kosten_euro=10.00)
        opleiding.save()

        inschrijving = OpleidingInschrijving(
                            opleiding=opleiding,
                            sporter=sporter,
                            koper=self.account,
                            log='test')
        inschrijving.save()
        inschrijving.wanneer_aangemeld = verleden
        inschrijving.save(update_fields=['wanneer_aangemeld'])

        product = BestellingProduct(
                        opleiding_inschrijving=inschrijving,
                        prijs_euro=Decimal('15.0'))
        product.save()
        self.mandje.producten.add(product)

    def setUp(self):
        """ initialisatie van de test case """

        self.account = self.e2e_create_account_admin()

        mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account)
        self.mandje = mandje

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
        self.ver = ver

        instelling = BetaalInstellingenVereniging(
                        vereniging=ver,
                        mollie_api_key='Test')
        instelling.save()
        self.instelling = instelling

        hwl = Functie(
                beschrijving='HWL 1000',
                rol='HWL',
                bevestigde_email='hwl@ver1000.not',
                vereniging=self.ver)
        hwl.save()

    def test_opschonen_wedstrijden(self):
        # bestel_mutaties doorloopt bij elke opstart alle mandjes
        # en verwijdert producten die al te lang in het mandje liggen

        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)

        self._leg_wedstrijd_in_mandje(now, verleden)

        mandje = BestellingMandje.objects.get(pk=self.mandje.pk)
        self.assertEqual(2, mandje.producten.count())

        with self.assert_max_queries(27):
            f1, f2, = self.run_management_command('bestel_mutaties', '--quick', '1')
        # print("\nf1: %s\nf2: %s" % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Opschonen mandjes begin" in f2.getvalue())

        # controleer de inhoud van het mandje
        mandje = BestellingMandje.objects.get(pk=mandje.pk)
        self.assertEqual(0, mandje.producten.count())

    def test_opschonen_evenement(self):
        # bestel_mutaties doorloopt bij elke opstart alle mandjes
        # en verwijdert producten die al te lang in het mandje liggen

        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)

        self._leg_evenement_in_mandje(now, verleden)

        mandje = BestellingMandje.objects.get(pk=self.mandje.pk)
        self.assertEqual(1, mandje.producten.count())

        with self.assert_max_queries(26):
            f1, f2, = self.run_management_command('bestel_mutaties', '--quick', '1')
        # print("\nf1: %s\nf2: %s" % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Opschonen mandjes begin" in f2.getvalue())

        # controleer de inhoud van het mandje
        mandje = BestellingMandje.objects.get(pk=mandje.pk)
        self.assertEqual(0, mandje.producten.count())

    def test_opschonen_webwinkel(self):
        # bestel_mutaties doorloopt bij elke opstart alle mandjes
        # en verwijdert producten die al te lang in het mandje liggen

        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)

        self._leg_webwinkel_in_mandje(verleden)

        mandje = BestellingMandje.objects.get(pk=self.mandje.pk)
        self.assertEqual(2, mandje.producten.count())

        with self.assert_max_queries(36):
            f1, f2, = self.run_management_command('bestel_mutaties', '--quick', '1')
        # print("\nf1: %s\nf2: %s" % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Opschonen mandjes begin" in f2.getvalue())

        # controleer de inhoud van het mandje
        mandje = BestellingMandje.objects.get(pk=mandje.pk)
        self.assertEqual(0, mandje.producten.count())

    def test_opschonen_opleiding(self):
        # bestel_mutaties doorloopt bij elke opstart alle mandjes
        # en verwijdert producten die al te lang in het mandje liggen

        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)

        self._leg_opleiding_in_mandje(now, verleden)

        mandje = BestellingMandje.objects.get(pk=self.mandje.pk)
        self.assertEqual(1, mandje.producten.count())

        with self.assert_max_queries(23):
            f1, f2, = self.run_management_command('bestel_mutaties', '--quick', '1')
        # print("\nf1: %s\nf2: %s" % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Opschonen mandjes begin" in f2.getvalue())

        # controleer de inhoud van het mandje
        mandje = BestellingMandje.objects.get(pk=mandje.pk)
        self.assertEqual(0, mandje.producten.count())

    def test_stuur_overboeken_herinneringen(self):
        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)
        self._leg_webwinkel_in_mandje(verleden)
        self._leg_wedstrijd_in_mandje(now, verleden)

        bestelling = Bestelling(
                        bestel_nr=42,
                        account=self.account,
                        ontvanger=self.instelling)
        bestelling.save()
        bestelling.aangemaakt -= datetime.timedelta(days=5)
        bestelling.save(update_fields=['aangemaakt'])
        bestelling.producten.add(self.product1)
        bestelling.producten.add(self.product2)
        bestelling.producten.add(self.product3)

        locatie = EvenementLocatie(
                        naam='Test',
                        vereniging=self.ver,
                        adres='Test')
        locatie.save()

        evenement = Evenement(
                        titel='Test',
                        organiserende_vereniging=self.ver,
                        datum='2000-01-01',
                        locatie=locatie)
        evenement.save()

        inschrijving = EvenementInschrijving(
                            wanneer=verleden,
                            evenement=evenement,
                            sporter=self.sporter,
                            koper=self.account)
        inschrijving.save()

        product = BestellingProduct(
                        evenement_inschrijving=inschrijving,
                        prijs_euro=Decimal('1.23'))
        product.save()
        bestelling.producten.add(product)

        self.assertEqual(0, Taak.objects.count())
        with self.assert_max_queries(20):
            f1, f2, = self.run_management_command('stuur_overboeken_herinneringen')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(' 1 onbetaalde bestellingen voor vereniging [1000] Grote Club' in f2.getvalue())
        self.assertEqual(1, Taak.objects.count())

        # nog een keer; controleer dat geen nieuwe taak aangemaakt wordt
        f1, f2, = self.run_management_command('stuur_overboeken_herinneringen')
        self.assertTrue(' 1 onbetaalde bestellingen voor vereniging [1000] Grote Club' in f2.getvalue())
        self.assertEqual(1, Taak.objects.count())

# end of file
