# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_AFGEROND,
                                   BESTELLING_STATUS_GEANNULEERD, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
from Bestelling.models import Bestelling, BestellingRegel, BestellingMutatie
from Betaal.definities import (TRANSACTIE_TYPE_MOLLIE_PAYMENT, TRANSACTIE_TYPE_MOLLIE_RESTITUTIE,
                               TRANSACTIE_TYPE_HANDMATIG)
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from decimal import Decimal


class TestBestellingBestelling(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module bestellingen """

    test_after = ('Bestelling.tests.test_mandje',)

    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_bestelling_details = '/bestel/details/%s/'      # bestel_nr
    url_annuleer_bestelling = '/bestel/annuleer/%s/'        # bestel_nr

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        self.account_normaal = self.e2e_create_account('100001', 'normaal@test.com', 'Normaal')

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.club1000.not',
                    contact_email='club1000@khsn.not',
                    telefoonnummer='12345678')
        ver.save()
        self.ver1 = ver

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_bond=True)
        instellingen.save()
        self.instellingen = instellingen

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Nor',
                        achternaam='Maal',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        postadres_1='Zoef 2',
                        postadres_2='9999ZZ Boogdorp',
                        account=self.account_normaal,
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
                        plaats='Boogdorp')
        locatie.save()
        locatie.verenigingen.add(ver)

        # maak een kalenderwedstrijd aan, met sessie
        sessie = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    max_sporters=50)
        sessie.save()
        self.sessie = sessie

        wedstrijd = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        minuten_voor_begin_sessie_aanwezig_zijn=42,
                        organiserende_vereniging=ver,
                        contact_email='organisatie@ver.not',
                        contact_telefoon='0600000001',
                        contact_naam='Organ is a Tie',
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=42.00)
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
                            koper=self.account_normaal)
        inschrijving.save()
        self.wedstrijd_inschrijving = inschrijving

    def test_anon(self):
        self.client.logout()

        # inlog vereist voor mandje
        resp = self.client.get(self.url_bestellingen_overzicht)
        self.assert403(resp)

        resp = self.client.get(self.url_bestelling_details % 999999)
        self.assert403(resp)

        resp = self.client.post(self.url_bestelling_details % 999999)
        self.assert403(resp)

    def test_bestelling(self):
        self.e2e_login(self.account_normaal)

        # bekijk de bestellingen (lege lijst)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        status=BESTELLING_STATUS_NIEUW)
        bestelling.save()

        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        status=BESTELLING_STATUS_MISLUKT)
        bestelling.save()

        # bekijk de bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

    def test_details_nieuw(self):
        self.e2e_login(self.account_normaal)

        # bestaat niet
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestelling_details % 999999)
        self.assert404(resp, 'Niet gevonden')

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        totaal_euro=Decimal(1.0),
                        ontvanger=self.instellingen,
                        status=BESTELLING_STATUS_NIEUW)
        bestelling.save()

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_details_actief(self):
        self.e2e_login(self.account_normaal)

        self.instellingen.akkoord_via_bond = False
        self.instellingen.save(update_fields=['akkoord_via_bond'])

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        totaal_euro=Decimal(1.0),
                        ontvanger=self.instellingen,
                        status=BESTELLING_STATUS_BETALING_ACTIEF)
        bestelling.save()

        # met transacties
        transactie = BetaalTransactie(
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                            payment_id='testje1',
                            when=timezone.now(),
                            beschrijving="Test beschrijving 1",
                            bedrag_beschikbaar=Decimal('10'),
                            klant_naam="Pietje Pijlsnel",
                            klant_account="1234.5678.9012.3456")
        transactie.save()
        bestelling.transacties.add(transactie)

        # restitutie
        transactie = BetaalTransactie(
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE,
                            payment_id='testje2',
                            when=timezone.now(),
                            beschrijving="Test beschrijving 2",
                            bedrag_beschikbaar=Decimal('10'),
                            klant_naam="Pietje Pijlsnel",
                            klant_account="1234.5678.9012.3456")
        transactie.save()
        bestelling.transacties.add(transactie)

        # handmatig
        transactie = BetaalTransactie(
                            transactie_type=TRANSACTIE_TYPE_HANDMATIG,
                            payment_id='testje3',
                            when=timezone.now(),
                            beschrijving="Test beschrijving 3",
                            bedrag_beschikbaar=Decimal('10'),
                            klant_naam="Pietje Pijlsnel",
                            klant_account="1234.5678.9012.3456")
        transactie.save()
        bestelling.transacties.add(transactie)

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

    def test_details_geannuleerd(self):
        self.e2e_login(self.account_normaal)

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        status=BESTELLING_STATUS_GEANNULEERD)
        bestelling.save()

        # corner case: negatief totaalbedrag
        regel = BestellingRegel(
                    korte_beschrijving='korting',
                    bedrag_euro=Decimal(-1.0),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
        regel.save()
        bestelling.regels.add(regel)

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        # coverage
        self.assertFalse(regel.is_webwinkel())
        regel.korte_beschrijving = "Dit is een erg lange beschrijving die afgekapt gaat worden op 60 tekens"
        self.assertTrue(str(regel) != '')

    def test_details_mislukt(self):
        self.e2e_login(self.account_normaal)

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        status=BESTELLING_STATUS_MISLUKT)
        bestelling.save()

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

    def test_details_afgerond(self):
        self.e2e_login(self.account_normaal)

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        status=BESTELLING_STATUS_AFGEROND)
        bestelling.save()

        # wedstrijd zonder kwalificatiescores
        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()
        bestelling.regels.add(regel)

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

    def test_details_kwalificatiescores(self):
        self.e2e_login(self.account_normaal)

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        status=BESTELLING_STATUS_AFGEROND)
        bestelling.save()

        regel = BestellingRegel(
                    korte_beschrijving='wedstrijd',
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()
        bestelling.regels.add(regel)

        self.wedstrijd_inschrijving.bestelling = regel
        self.wedstrijd_inschrijving.save(update_fields=['bestelling'])

        # wedstrijd eis kwalificatie scores
        self.wedstrijd.eis_kwalificatie_scores = True
        self.wedstrijd.save(update_fields=['eis_kwalificatie_scores'])

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

    def test_details_met_mollie_restitutie(self):
        self.e2e_login(self.account_normaal)

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        totaal_euro=Decimal(1.0),
                        ontvanger=self.instellingen,
                        status=BESTELLING_STATUS_AFGEROND)
        bestelling.save()

        # met transacties
        transactie = BetaalTransactie(
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                            payment_id='testje5',
                            when=timezone.now(),
                            beschrijving="Test beschrijving 1",
                            bedrag_beschikbaar=Decimal('10'),
                            # klant_naam="Pietje Pijlsnel",
                            klant_account="1234.5678.9012.3456",
                            bedrag_terugbetaald=Decimal(9.50))
        transactie.save()
        bestelling.transacties.add(transactie)

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

    def test_details_met_mollie_failed(self):
        self.e2e_login(self.account_normaal)

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        totaal_euro=Decimal(1.0),
                        ontvanger=self.instellingen,
                        status=BESTELLING_STATUS_AFGEROND)
        bestelling.save()

        # met transacties
        transactie = BetaalTransactie(
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                            payment_id='testje5',
                            payment_status='failed',
                            when=timezone.now(),
                            beschrijving="Test beschrijving 1",
                            bedrag_beschikbaar=Decimal('0'))
        transactie.save()
        bestelling.transacties.add(transactie)

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

    def test_annuleer(self):
        # maak een bestelling en annuleer deze weer
        self.e2e_login_and_pass_otp(self.account_normaal)

        # bestelling bestaat niet
        resp = self.client.post(self.url_annuleer_bestelling % 999999)
        self.assert404(resp, 'Niet gevonden')

        # maak een bestelling aan
        bestelling = Bestelling(
                        bestel_nr=1,
                        account=self.account_normaal,
                        totaal_euro=Decimal(1.0),
                        ontvanger=self.instellingen,
                        status=BESTELLING_STATUS_NIEUW)
        bestelling.save()

        self.assertEqual(BestellingMutatie.objects.count(), 0)

        # annuleer de bestelling
        url = self.url_annuleer_bestelling % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        self.assertEqual(BestellingMutatie.objects.count(), 1)

        # dubbele annuleer werkt niet omdat de dubbele mutatie niet aangemaakt wordt
        resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        self.assertEqual(BestellingMutatie.objects.count(), 1)

        # corner case: verkeerde status
        bestelling.status = BESTELLING_STATUS_AFGEROND
        bestelling.save(update_fields=['status'])

        url = self.url_annuleer_bestelling % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        self.assertEqual(BestellingMutatie.objects.count(), 1)

# end of file
