# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestel.models import (BestelMandje, BestelMutatie, Bestelling,
                           BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_WACHT_OP_BETALING, BESTELLING_STATUS_NIEUW,
                           BESTELLING_STATUS_MISLUKT)
from Bestel.mutaties import (bestel_mutatieverzoek_inschrijven_wedstrijd, bestel_mutatieverzoek_betaling_afgerond,
                             bestel_mutatieverzoek_kortingscode_toepassen, bestel_mutatieverzoek_afmelden_wedstrijd)
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalTransactie
from Mailer.models import MailQueue
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Wedstrijden.models import (Wedstrijd, WedstrijdSessie, WEDSTRIJD_STATUS_GEACCEPTEERD, WedstrijdLocatie,
                                WedstrijdInschrijving, WedstrijdKortingscode,
                                INSCHRIJVING_STATUS_RESERVERING_MANDJE, INSCHRIJVING_STATUS_RESERVERING_BESTELD,
                                INSCHRIJVING_STATUS_DEFINITIEF, INSCHRIJVING_STATUS_AFGEMELD)
from decimal import Decimal
import io


class TestBestelBestelling(E2EHelpers, TestCase):

    """ tests voor de Bestel applicatie, module bestellingen """

    test_after = ('Bestel.test_mandje',)

    url_mandje_bestellen = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_bestelling_details = '/bestel/details/%s/'          # bestel_nr
    url_bestelling_afrekenen = '/bestel/afrekenen/%s/'      # bestel_nr
    url_check_status = '/bestel/check-status/%s/'           # bestel_nr
    url_na_de_betaling = '/bestel/na-de-betaling/%s/'       # bestel_nr

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

        self.code = 'TESTJE1234'
        korting = WedstrijdKortingscode(
                    code=self.code,
                    geldig_tot_en_met=datum,
                    uitgegeven_door=ver,
                    voor_vereniging=ver,
                    percentage=42)
        korting.save()
        korting.voor_wedstrijden.add(wedstrijd)
        self.korting = korting

        mandje, is_created = BestelMandje.objects.get_or_create(account=account)
        self.mandje = mandje

    def test_anon(self):
        self.client.logout()

        # inlog vereist voor mandje
        resp = self.client.get(self.url_bestellingen_overzicht)
        self.assert403(resp)

        resp = self.client.get(self.url_bestelling_details % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_bestelling_afrekenen % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_na_de_betaling % 999999)
        self.assert403(resp)

    def test_bestelling(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # bekijk de bestellingen (lege lijst)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.prefetch_related('producten').all()[0]
        self.assertEqual(1, bestelling.producten.count())
        product1 = bestelling.producten.all()[0]

        self.assertEqual(1, MailQueue.objects.count())
        email = MailQueue.objects.all()[0]
        self.assert_email_html_ok(email.mail_html, 'email_bestel/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(email)

        # bekijk de bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

        # fout: dikke korting zonder code (te betalen wordt negatief)
        product1.korting_euro = Decimal('100')
        product1.save()
        # fout: sporter niet meer bij vereniging
        self.sporter.bij_vereniging = None
        self.sporter.save()
        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # mutileer het product (doorzetten vanuit het mandje lukt niet)
        product1.wedstrijd_inschrijving = None
        product1.save(update_fields=['wedstrijd_inschrijving'])

        # bekijk de bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_bestelling_details % 999999)
        self.assert404(resp, 'Niet gevonden')

        resp = self.client.get(self.url_bestelling_details % '1=5')
        self.assert404(resp, 'Niet gevonden')

    def test_geen_instellingen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        # verwijder de instellingen van de vereniging
        self.instellingen.delete()

        # nu kan de bestelling niet aangemaakt worden
        self.verwerk_bestel_mutaties()
        self.assertEqual(0, Bestelling.objects.count())

    def test_geen_instellingen_nhb(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        # verwijder de instellingen van de vereniging
        self.instellingen_nhb.delete()

        # nu kan de bestelling niet aangemaakt worden
        self.verwerk_bestel_mutaties()
        self.assertEqual(0, Bestelling.objects.count())

    def test_geen_mandje(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)

        mutatie = BestelMutatie.objects.all()[0]
        mutatie.account = None
        mutatie.save(update_fields=['account'])

        f1, f2 = self.verwerk_bestel_mutaties(fail_on_error=False, show_warnings=False)
        self.assertTrue('[ERROR] Mutatie' in f1.getvalue())
        self.assertTrue('heeft geen account' in f1.getvalue())

    def test_afrekenen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname met kortingscode
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_kortingscode_toepassen(self.account_admin, self.korting.code, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='open',
                            log='test')
        betaalactief.save()

        BetaalTransactie(
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                is_restitutie=False,
                bedrag_euro_klant=Decimal('10'),
                bedrag_euro_boeking=Decimal('9.75'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        # zonder BetaalActief gekoppeld aan de Bestelling werkt het niet (mutatie verzoek wordt niet eens verstuurd)
        self.assertEqual(3, BestelMutatie.objects.count())
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestelMutatie.objects.count())
        self.assertEqual(MailQueue.objects.count(), 1)      # bevestiging van de bestelling
        MailQueue.objects.all().delete()

        # koppel transactie aan de bestelling, zodat deze gevonden kan worden
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # betaling mislukt
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=False, snel=True)
        self.assertEqual(4, BestelMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        self.assertTrue('Betaling niet gelukt voor bestelling' in f2.getvalue())
        self.assertEqual(MailQueue.objects.count(), 0)

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_MISLUKT)
        self.assertIsNone(bestelling.betaal_actief)

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # dubbel verzoek heeft geen effect
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(5, BestelMutatie.objects.count())
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(5, BestelMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())

        # er moet nu een mail in de MailQueue staan
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.all()[0]
        self.assert_email_html_ok(mail.mail_html, 'email_bestel/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail)

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        # haal de details op nu de betaling gedaan is
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        # corner cases
        resp = self.client.get(self.url_bestelling_afrekenen % 999999)
        self.assert404(resp, 'Niet gevonden')

        # test met een bestelling aan van een ander account
        account = self.e2e_create_account('user', 'user@nhb.not', 'User')
        andere = Bestelling(bestel_nr=1234, account=account)
        andere.save()

        # verkeerd account
        resp = self.client.post(self.url_check_status % andere.bestel_nr)
        self.assert404(resp, 'Niet gevonden')       # want verkeerd account

        url = self.url_check_status % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'afgerond')

        # transactie met bestelling in verkeerde status
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        bestelling.betaal_actief = betaalactief
        bestelling.save(update_fields=['betaal_actief'])

        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties(show_warnings=False)
        self.assertTrue('wacht niet op een betaling (status=' in f2.getvalue())

    def test_afrekenen_te_weinig(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]

        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()

        # koppel transactie aan de bestelling, zodat deze gevonden kan worden
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # deze betaling is 1 cent te weinig
        BetaalTransactie(
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                is_restitutie=False,
                bedrag_euro_klant=Decimal('9.99'),
                bedrag_euro_boeking=Decimal('9.75'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=False, snel=True)      # corner case
        f1, f2 = self.verwerk_bestel_mutaties(show_warnings=False)    # suppress warning from corner case
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        self.assertTrue('heeft geen actieve transactie' in f2.getvalue())                   # corner case

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_WACHT_OP_BETALING)
        self.assertIsNone(bestelling.betaal_actief)

    def test_restitutie(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]

        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # maak een transactie geschiedenis aan met een restitutie, maar toch genoeg betaald
        BetaalTransactie(
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving 1",
                is_restitutie=False,
                bedrag_euro_klant=Decimal('5'),
                bedrag_euro_boeking=Decimal('4.75'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        BetaalTransactie(
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving 2",
                is_restitutie=True,
                bedrag_euro_klant=Decimal('5'),
                bedrag_euro_boeking=Decimal('5.25'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        BetaalTransactie(
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving 3",
                is_restitutie=False,
                bedrag_euro_klant=Decimal('10'),
                bedrag_euro_boeking=Decimal('9.75'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.verwerk_bestel_mutaties()

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        # haal de details op nu de betaling gedaan is met restitutie
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        # opnieuw de bestelling af willen rekenen met een bestelling waar een restitutie in zit
        # TODO: onduidelijk hoe hier mee om te gaan, want bestelling is AFGEROND
        # url = self.url_check_status % bestelling.bestel_nr
        # with self.assert_max_queries(20):
        #     resp = self.client.post(url, {'snel': 1})
        # self.assertEqual(resp.status_code, 200)
        # data = resp.json()
        # self.assertTrue('status' in data.keys())
        # status = data['status']
        # self.assertEqual(status, 'error')

    def test_nul_bedrag(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # maak de wedstrijd gratis
        self.wedstrijd.prijs_euro_normaal = Decimal('0')
        self.wedstrijd.prijs_euro_onder18 = Decimal('0')
        self.wedstrijd.save(update_fields=['prijs_euro_normaal', 'prijs_euro_onder18'])

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue(' wordt meteen afgerond' in f2.getvalue())
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]
        # TODO: niet af?

    def test_mutatie(self):
        # een paar corner cases
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)

        # duration > 1
        # fake-hoogste
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('bestel_mutaties', '2', '--fake-hoogste', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[INFO] vorige hoogste BestelMutatie pk is -1' in f2.getvalue())

        # geen nuttig werk gedaan
        self.verwerk_bestel_mutaties()

        # aantal mutaties gelijk aan 0
        BestelMutatie.objects.all().delete()
        self.verwerk_bestel_mutaties()

        # onbekende mutatie
        BestelMutatie(code=9999).save()
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[ERROR] Onbekende mutatie code 9999' in f2.getvalue())

    def test_afmelden_voor_betalen(self):
        # inschrijven, bestellen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEquals(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_MANDJE)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('0'))
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(inschrijving.ontvangen_euro, inschrijving.retour_euro)     # nog steeds 0

        # afmelden voor de wedstrijd
        bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue(' met status="besteld" afmelden voor wedstrijd' in f2.getvalue())
        self.assertTrue('status Gereserveerd, wacht op betaling --> Afgemeld' in f2.getvalue())
        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_AFGEMELD)

        # nog een keer afmelden
        bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue(' met status="besteld" afmelden voor wedstrijd' not in f2.getvalue())

    def test_afmelden_tijdens_betalen(self):
        # inschrijven, bestellen, gedeeltelijk betalen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEquals(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(inschrijving.ontvangen_euro, inschrijving.retour_euro)     # nog steeds 0

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
        bestelling.betaal_actief = betaalactief
        bestelling.save(update_fields=['betaal_actief', 'status'])
        BetaalTransactie(
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                is_restitutie=False,
                bedrag_euro_klant=Decimal('5'),
                bedrag_euro_boeking=Decimal('4.75'),
                klant_naam="Pietje Pijlsnel",
                klant_account="IBAN1234567801234").save()
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestelMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_WACHT_OP_BETALING)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('0'))     # TODO: verwachting = 5
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

        # afmelden voor de wedstrijd
        bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=True)
        self.verwerk_bestel_mutaties()
        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_AFGEMELD)

    def test_afmelden_na_betalen(self):
        # inschrijven, bestellen, betalen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEquals(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(inschrijving.ontvangen_euro, inschrijving.retour_euro)     # nog steeds 0

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_WACHT_OP_BETALING
        bestelling.save(update_fields=['betaal_actief', 'status'])
        BetaalTransactie(
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                is_restitutie=False,
                bedrag_euro_klant=Decimal('10'),
                bedrag_euro_boeking=Decimal('9.75'),
                klant_naam="Pietje Pijlsnel",
                klant_account="IBAN1234567801234").save()
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestelMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('10'))
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

        # afmelden voor de wedstrijd
        bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=True)
        self.verwerk_bestel_mutaties()
        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_AFGEMELD)

    def test_afgerond(self):
        # inschrijven, bestellen, betalen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEquals(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        url = self.url_na_de_betaling % bestelling.bestel_nr

        # wacht op betaling
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # transacties ontvangen en restitutie
        transactie = BetaalTransactie(
                            payment_id='testje',
                            when=timezone.now(),
                            beschrijving="Test beschrijving",
                            is_restitutie=False,
                            bedrag_euro_klant=Decimal('10'),
                            bedrag_euro_boeking=Decimal('9.75'),
                            klant_naam="Pietje Pijlsnel",
                            klant_account="1234.5678.9012.3456")
        transactie.save()
        bestelling.transacties.add(transactie)

        # nu is er genoeg ontvangen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # restitutie toevoegen voor de coverage
        transactie = BetaalTransactie(
                            payment_id='testje',
                            when=timezone.now(),
                            beschrijving="Test beschrijving",
                            is_restitutie=True,
                            bedrag_euro_klant=Decimal('5'),
                            bedrag_euro_boeking=Decimal('5.25'),
                            klant_naam="Pietje Pijlsnel",
                            klant_account="1234.5678.9012.3456")
        transactie.save()
        bestelling.transacties.add(transactie)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # status = afgerond
        bestelling.status = BESTELLING_STATUS_AFGEROND
        bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # corner case
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_na_de_betaling % 99999)
        self.assert404(resp, "Niet gevonden")

# end of file
