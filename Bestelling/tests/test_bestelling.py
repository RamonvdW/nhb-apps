# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_IFAA
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_MUTATIE_ANNULEER)
from Bestelling.models import BestellingMandje, BestellingMutatie, Bestelling
from Bestelling.operations.mutaties import (bestel_mutatieverzoek_inschrijven_wedstrijd,
                                            bestel_mutatieverzoek_webwinkel_keuze,
                                            bestel_mutatieverzoek_inschrijven_evenement,
                                            bestel_mutatieverzoek_afmelden_evenement,
                                            bestel_mutatieverzoek_betaling_afgerond,
                                            bestel_mutatieverzoek_afmelden_wedstrijd)
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_PAYMENT, TRANSACTIE_TYPE_MOLLIE_RESTITUTIE
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalTransactie, BetaalMutatie
from Evenement.definities import (EVENEMENT_STATUS_GEACCEPTEERD,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_BESTELD,
                                  EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF)
from Evenement.models import Evenement, EvenementInschrijving, EvenementAfgemeld
from Functie.models import Functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie, EvenementLocatie
from Mailer.models import MailQueue
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.definities import VERZENDKOSTEN_BRIEFPOST
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_KORTING_VERENIGING,
                                    WEDSTRIJD_KORTING_SPORTER,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting
from decimal import Decimal
import datetime
import time


class TestBestellingBestelling(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module bestellingen """

    test_after = ('Bestelling.tests.test_mandje',)

    url_mandje_bestellen = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_bestelling_details = '/bestel/details/%s/'          # bestel_nr
    url_bestelling_afrekenen = '/bestel/afrekenen/%s/'      # bestel_nr
    url_check_status = '/bestel/check-status/%s/'           # bestel_nr
    url_na_de_betaling = '/bestel/na-de-betaling/%s/'       # bestel_nr
    url_annuleer_bestelling = '/bestel/annuleer/%s/'        # bestel_nr

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
        self.ver1 = ver

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
                        postadres_1='Snelweg 12',
                        postadres_2='9999ZZ Boogdorp',
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

        mandje, is_created = BestellingMandje.objects.get_or_create(account=account)
        self.mandje = mandje

        self.functie_mww = Functie.objects.filter(rol='MWW').first()
        self.functie_mww.bevestigde_email = 'mww@bond.tst'
        self.functie_mww.save(update_fields=['bevestigde_email'])

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='meervoud',
                        bestel_begrenzing='1-5',
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
        self.keuze = keuze

        locatie = EvenementLocatie(
                        naam='Test locatie E',
                        vereniging=ver,
                        adres='Het Veer 5, 1234XX Doel',
                        plaats='Doel')
        locatie.save()

        evenement = Evenement(
                        titel='Test evenement',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver,
                        datum=datum,
                        locatie=locatie,
                        contact_naam='Het contact',
                        contact_email='contact@test.not',
                        contact_website='www.contact.not',
                        contact_telefoon='12345678',
                        beschrijving="Test evenement voor alle testen",
                        prijs_euro_normaal=15.0,
                        prijs_euro_onder18=9.5)
        evenement.save()
        self.evenement = evenement

        inschrijving = EvenementInschrijving(
                            wanneer=now,
                            nummer=42,
                            evenement=evenement,
                            sporter=sporter,
                            koper=self.account_admin)
        inschrijving.save()
        self.evenement_inschrijving = inschrijving

    def test_anon(self):
        self.client.logout()

        # inlog vereist voor mandje
        resp = self.client.get(self.url_bestellingen_overzicht)
        self.assert403(resp)

        resp = self.client.get(self.url_bestelling_details % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_bestelling_afrekenen % 999999)
        self.assert403(resp)

        resp = self.client.post(self.url_bestelling_afrekenen % 999999)
        self.assert403(resp)

        resp = self.client.post(self.url_check_status % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_na_de_betaling % 999999)
        self.assert403(resp)

        resp = self.client.post(self.url_bestelling_details % 999999)
        self.assert403(resp)

    def test_bestelling(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_admin, self.keuze, snel=True)
        bestel_mutatieverzoek_inschrijven_evenement(self.account_admin, self.evenement_inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # bekijk de bestellingen (lege lijst)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties(kosten_pakket=10.42, kosten_brief=5.43)
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.prefetch_related('producten').first()
        self.assertEqual(str(bestelling.verzendkosten_euro), '10.42')
        self.assertEqual(3, bestelling.producten.count())
        product1 = bestelling.producten.exclude(wedstrijd_inschrijving=None).first()

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Bedrag:', '>Korting:'))
        self.assertTrue('Verzendkosten' in mail.mail_text)

        # bekijk de bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

        # fout: dikke korting (te betalen wordt negatief)
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
        self.assert_template_used(resp, ('bestelling/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # maak het product "kapot" zodat doorzetten vanuit het mandje niet meer kan
        product1.wedstrijd_inschrijving = None
        product1.save(update_fields=['wedstrijd_inschrijving'])

        # bekijk de bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_bestelling_details % 999999)
        self.assert404(resp, 'Niet gevonden')

        resp = self.client.get(self.url_bestelling_details % '1=5')
        self.assert404(resp, 'Niet gevonden')

    def test_briefpost(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        self.product.type_verzendkosten = VERZENDKOSTEN_BRIEFPOST
        self.product.save(update_fields=['type_verzendkosten'])

        # bestel de producten
        bestel_mutatieverzoek_webwinkel_keuze(self.account_admin, self.keuze, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties(kosten_pakket=10.42, kosten_brief=5.43)
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.first()
        self.assertEqual(1, bestelling.producten.count())
        self.assertEqual(str(bestelling.verzendkosten_euro), '5.43')

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Bedrag:', '>Korting:'))
        self.assertTrue('Verzendkosten' in mail.mail_text)

        # bekijk de bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

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

        # de bestelling wordt toch aangemaakt, zodat handmatig betaald kan worden
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

    def test_geen_instellingen_bond(self):
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
        self.instellingen_bond.delete()

        # de bestelling wordt toch aangemaakt, zodat er handmatig betaald kan worden
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

    def test_geen_mandje(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)

        mutatie = BestellingMutatie.objects.first()
        mutatie.account = None
        mutatie.save(update_fields=['account'])

        f1, f2 = self.verwerk_bestel_mutaties(fail_on_error=False, show_warnings=False)
        self.assertTrue('[ERROR] Mutatie' in f1.getvalue())
        self.assertTrue('heeft geen account' in f1.getvalue())

    def test_afrekenen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname met korting
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_inschrijven_evenement(self.account_admin, self.evenement_inschrijving, snel=True)
        # korting moet automatisch toegepast worden
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # simuleer een betaling
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='open',
                            log='test')
        betaalactief.save()

        BetaalTransactie(
                transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                bedrag_beschikbaar=Decimal('20.80'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        # zonder BetaalActief gekoppeld aan de Bestelling werkt het niet (mutatie verzoek wordt niet eens verstuurd)
        self.assertEqual(3, BestellingMutatie.objects.count())
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestellingMutatie.objects.count())
        self.assertEqual(MailQueue.objects.count(), 1)      # bevestiging van de bestelling
        MailQueue.objects.all().delete()

        # koppel transactie aan de bestelling, zodat deze gevonden kan worden
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # betaling mislukt
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=False, snel=True)
        self.assertEqual(4, BestellingMutatie.objects.count())
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
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # dubbel verzoek heeft geen effect
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(5, BestellingMutatie.objects.count())
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(5, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())

        # er moet nu een mail in de MailQueue staan
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-betaling.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Bedrag:', '>Korting:'))

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        # haal de details op nu de betaling gedaan is
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        # corner cases
        resp = self.client.get(self.url_bestelling_afrekenen % 999999)
        self.assert404(resp, 'Niet gevonden')

        # test met een bestelling aan van een ander account
        account = self.e2e_create_account('user', 'user@test.not', 'User')
        andere = Bestelling(bestel_nr=1234, account=account)
        andere.save()

        # verkeerd account
        resp = self.client.post(self.url_check_status % andere.bestel_nr)
        self.assert404(resp, 'Niet gevonden')       # want verkeerd account

        self.e2e_assert_other_http_commands_not_supported(self.url_check_status % andere.bestel_nr,
                                                          get=True, post=False)

        url = self.url_check_status % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url)
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

    def test_kortingen_lid(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        self.wedstrijd.organisatie = ORGANISATIE_IFAA
        self.wedstrijd.save(update_fields=['organisatie'])

        # bestel wedstrijddeelname met korting
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        # korting wordt automatisch toegepast
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()

        bestelling = Bestelling.objects.first()

        # fake de korting: persoonlijk
        product = bestelling.producten.first()
        inschrijving = product.wedstrijd_inschrijving
        korting = inschrijving.korting
        korting.soort = WEDSTRIJD_KORTING_SPORTER
        korting.save(update_fields=['soort'])

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

    def test_opnieuw_afrekenen(self):
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
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # simuleer een betaling
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='open',
                            log='test')
        betaalactief.save()

        BetaalTransactie(
                transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                bedrag_beschikbaar=Decimal('10'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        # zonder BetaalActief gekoppeld aan de Bestelling werkt het niet (mutatie verzoek wordt niet eens verstuurd)
        self.assertEqual(2, BestellingMutatie.objects.count())
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(2, BestellingMutatie.objects.count())
        self.assertEqual(MailQueue.objects.count(), 1)      # bevestiging van de bestelling
        MailQueue.objects.all().delete()

        # koppel transactie aan de bestelling, zodat deze gevonden kan worden
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # betaling mislukt
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=False, snel=True)
        self.assertEqual(3, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        self.assertTrue('Betaling niet gelukt voor bestelling' in f2.getvalue())
        self.assertEqual(MailQueue.objects.count(), 0)

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_MISLUKT)

        # start the betaling opnieuw op
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        # corner case: status is niet MISLUKT
        resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

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
        bestelling = Bestelling.objects.first()

        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()

        # koppel transactie aan de bestelling, zodat deze gevonden kan worden
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # deze betaling is 1 cent te weinig
        BetaalTransactie(
                transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                bedrag_beschikbaar=Decimal('9.99'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=False, snel=True)      # corner case
        f1, f2 = self.verwerk_bestel_mutaties(show_warnings=False)    # suppress warning from corner case
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        self.assertTrue('wacht niet op een betaling' in f2.getvalue())                      # corner case

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        # self.assertEqual(bestelling.status, BESTELLING_STATUS_WACHT_OP_BETALING)      # TODO: resolve
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
        bestelling = Bestelling.objects.first()

        url = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        # maak een transactie geschiedenis aan met een restitutie, maar toch genoeg betaald
        BetaalTransactie(
                transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving 1",
                bedrag_beschikbaar=Decimal('5'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        BetaalTransactie(
                transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE,
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving 2",
                bedrag_refund=Decimal('5'),
                klant_naam="Pietje Pijlsnel",
                klant_account="1234.5678.9012.3456").save()

        BetaalTransactie(
                transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving 3",
                bedrag_beschikbaar=Decimal('10'),
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
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

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
        # inschrijving door iemand anders
        account_koper = self.e2e_create_account('koper', 'koper@test.com', 'Koper')
        self.inschrijving.koper = account_koper
        self.inschrijving.save(update_fields=['koper'])

        sporter_koper = Sporter(
                        lid_nr=102000,
                        voornaam='Ko',
                        achternaam='de Koper',
                        geboorte_datum='1986-08-08',
                        sinds_datum='2010-08-08',
                        account=account_koper,
                        bij_vereniging=self.ver1)
        sporter_koper.save()
        self.e2e_login(account_koper)

        # maak de wedstrijd gratis
        self.wedstrijd.prijs_euro_normaal = Decimal('0')
        self.wedstrijd.prijs_euro_onder18 = Decimal('0')
        self.wedstrijd.save(update_fields=['prijs_euro_normaal', 'prijs_euro_onder18'])

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(account_koper, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue(' wordt meteen afgerond' in f2.getvalue())
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        self.assertEqual(2, MailQueue.objects.count())
        mail = MailQueue.objects.get(mail_to=account_koper.bevestigde_email)
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail)

        mail = MailQueue.objects.get(mail_to=self.sporter.account.bevestigde_email)
        # print('\nmail_text = %s' % mail.mail_text)
        # print('mail_html = %s' % mail.mail_html)
        self.assertTrue(self.wedstrijd.locatie.plaats in mail.mail_text)
        self.assert_email_html_ok(mail, 'email_bestelling/info-inschrijving-wedstrijd.dtl')
        self.assertTrue('09:18' in mail.mail_text)        # 10:00 - 42min
        self.assert_consistent_email_html_text(mail)

    def test_nul_bedrag_geen_email(self):
        # inschrijving door iemand anders
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        account_koper = self.e2e_create_account('koper', 'koper@test.com', 'Koper')
        self.inschrijving.koper = account_koper
        self.inschrijving.save(update_fields=['koper'])

        # maak de wedstrijd gratis
        self.wedstrijd.prijs_euro_normaal = Decimal('0')
        self.wedstrijd.prijs_euro_onder18 = Decimal('0')
        self.wedstrijd.save(update_fields=['prijs_euro_normaal', 'prijs_euro_onder18'])

        sporter = self.inschrijving.sporterboog.sporter
        sporter.account = None
        # sporter.email = ''        # is al leeg
        sporter.save(update_fields=['account'])

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue(' wordt meteen afgerond' in f2.getvalue())
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        # TODO: niet af?

    def test_nul_bedrag_geen_account(self):
        # inschrijving door iemand anders
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        account_koper = self.e2e_create_account('koper', 'koper@test.com', 'Koper')
        self.inschrijving.koper = account_koper
        self.inschrijving.save(update_fields=['koper'])

        # maak de wedstrijd gratis
        self.wedstrijd.organisatie = ORGANISATIE_IFAA      # geeft schietstijl ipv boogtype
        self.wedstrijd.prijs_euro_normaal = Decimal('0')
        self.wedstrijd.prijs_euro_onder18 = Decimal('0')
        self.wedstrijd.save(update_fields=['prijs_euro_normaal', 'prijs_euro_onder18', 'organisatie'])

        sporter = self.inschrijving.sporterboog.sporter
        sporter.account = None
        sporter.email = 'sporter@test.not'
        sporter.save(update_fields=['account', 'email'])

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue(' wordt meteen afgerond' in f2.getvalue())
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        # TODO: niet af?

        self.assertEqual(2, MailQueue.objects.count())
        mail = MailQueue.objects.get(mail_to=sporter.email)
        self.assertTrue('Aanwezig zijn om:' in mail.mail_text)
        # self.assertTrue('Schietstijl:' in mail.mail_text)

    def test_kwalificatie_scores(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # wedstrijd eis kwalificatie scores
        self.wedstrijd.eis_kwalificatie_scores = True
        self.wedstrijd.save(update_fields=['eis_kwalificatie_scores'])

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        # bekijk de bestelling waarop nu de sectie kwalificatie scores getoond wordt
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Kwalificatie scores')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls: %s' % repr(urls))
        urls = [url for url in urls if url.startswith('/wedstrijden/inschrijven/kwalificatie-scores-doorgeven/')]
        self.assertEqual(1, len(urls))

    def test_prijs_onder18(self):
        now = timezone.now().date()
        self.sporter.geboorte_datum = now - datetime.timedelta(days=16*365)
        self.sporter.save(update_fields=['geboorte_datum'])

        self.korting.delete()

        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())

        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        self.assertEqual(bestelling.totaal_euro, 42.0)

    def test_mutatie(self):
        # een paar corner cases
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)

        # duration > 1
        # fake-hoogste
        f1, f2 = self.run_management_command('bestel_mutaties', '60', '--quick')
        self.assertTrue('[INFO] vorige hoogste BestellingMutatie pk is 0' in f2.getvalue())

        # geen nuttig werk gedaan
        self.verwerk_bestel_mutaties()

        # aantal mutaties gelijk aan 0
        BestellingMutatie.objects.all().delete()
        self.verwerk_bestel_mutaties()

        # onbekende mutatie
        BestellingMutatie(code=9999).save()
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[ERROR] Onbekende mutatie code 9999' in f2.getvalue())

    def test_afmelden_voor_betalen(self):
        # inschrijven, bestellen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_inschrijven_evenement(self.account_admin, self.evenement_inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        self.inschrijving.refresh_from_db()
        self.assertEqual(self.inschrijving.koper, self.account_admin)
        self.assertEqual(self.inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)
        self.assertEqual(self.inschrijving.ontvangen_euro, Decimal('0'))
        self.assertEqual(self.inschrijving.retour_euro, Decimal('0'))

        self.evenement_inschrijving.refresh_from_db()
        self.assertEqual(self.evenement_inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE)
        self.assertEqual(self.evenement_inschrijving.koper, self.account_admin)
        self.assertEqual(self.evenement_inschrijving.bedrag_ontvangen, Decimal('0'))

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        self.inschrijving.refresh_from_db()
        self.assertEqual(self.inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(self.inschrijving.ontvangen_euro, self.inschrijving.retour_euro)     # nog steeds 0

        self.evenement_inschrijving.refresh_from_db()
        self.assertEqual(self.evenement_inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_BESTELD)

        # afmelden voor de wedstrijd
        bestel_mutatieverzoek_afmelden_wedstrijd(self.inschrijving, snel=True)
        bestel_mutatieverzoek_afmelden_evenement(self.evenement_inschrijving, snel=True)

        self.assertEqual(EvenementAfgemeld.objects.count(), 0)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue(' met status="besteld" afmelden voor wedstrijd' in f2.getvalue())
        self.assertTrue(' met status="besteld" afmelden voor evenement' in f2.getvalue())
        self.assertTrue('status Gereserveerd, wacht op betaling --> Verwijderd' in f2.getvalue())
        self.assertTrue('status Gereserveerd, wacht op betaling --> afgemeld pk=' in f2.getvalue())
        self.assertEqual(EvenementAfgemeld.objects.count(), 1)

        self.inschrijving.refresh_from_db()
        self.assertEqual(self.inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
        self.assertEqual(EvenementInschrijving.objects.filter(pk=self.evenement_inschrijving.pk).count(), 0)

        # nog een keer afmelden
        bestel_mutatieverzoek_afmelden_wedstrijd(self.inschrijving, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertFalse(' met status="besteld" afmelden voor wedstrijd' in f2.getvalue())

    def test_afmelden_tijdens_betalen(self):
        # inschrijven, bestellen, gedeeltelijk betalen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(inschrijving.ontvangen_euro, inschrijving.retour_euro)     # nog steeds 0

        # betaling verwerken
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.betaal_actief = betaalactief
        bestelling.save(update_fields=['betaal_actief', 'status'])
        BetaalTransactie(
                transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                payment_id='testje',
                when=betaalactief.when,
                beschrijving="Test beschrijving",
                bedrag_beschikbaar=Decimal('5'),
                klant_naam="Pietje Pijlsnel",
                klant_account="IBAN1234567801234").save()
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_BETALING_ACTIEF)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('0'))     # TODO: verwachting = 5
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

        # afmelden voor de wedstrijd
        bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=True)
        self.verwerk_bestel_mutaties()
        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)

    def test_afmelden_na_betalen(self):
        # inschrijven, bestellen, betalen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_inschrijven_evenement(self.account_admin, self.evenement_inschrijving, snel=True)
        # coverage: 2e verzoek voor dezelfde mutatie
        bestel_mutatieverzoek_inschrijven_evenement(self.account_admin, self.evenement_inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        self.evenement_inschrijving.refresh_from_db()
        self.assertEqual(self.evenement_inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_BESTELD)
        self.assertEqual(inschrijving.ontvangen_euro, inschrijving.retour_euro)     # nog steeds 0

        self.evenement_inschrijving.refresh_from_db()
        self.assertEqual(self.evenement_inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_BESTELD)

        # simuleer een betaling
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        BetaalTransactie(
                when=betaalactief.when,
                transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                payment_id='testje',
                beschrijving="Test beschrijving",
                bedrag_beschikbaar=Decimal('20.80'),
                klant_naam="Pietje Pijlsnel",
                klant_account="IBAN1234567801234").save()
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(4, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('5.80'))      # prijs minus korting
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

        self.evenement_inschrijving.refresh_from_db()
        self.assertEqual(self.evenement_inschrijving.status, EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF)

        # afmelden voor de wedstrijd
        bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=True)
        bestel_mutatieverzoek_afmelden_evenement(self.evenement_inschrijving, snel=True)
        # coverage: 2e verzoek voor dezelfde mutatie
        bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel=True)
        bestel_mutatieverzoek_afmelden_evenement(self.evenement_inschrijving, snel=True)
        self.verwerk_bestel_mutaties()
        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD)

    def test_afgerond(self):
        # inschrijven, bestellen, betalen, afmelden
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        # coverage: 2e verzoek voor dezelfde mutatie
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.koper, self.account_admin)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # activeer bericht over "moet handmatig betalen"
        self.instellingen.akkoord_via_bond = False
        self.instellingen.save()

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        url = self.url_na_de_betaling % bestelling.bestel_nr

        # wacht op betaling
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # transacties ontvangen en restitutie
        transactie = BetaalTransactie(
                            when=timezone.now(),
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                            payment_id='testje',
                            beschrijving="Test beschrijving",
                            bedrag_te_ontvangen=Decimal('10'),
                            bedrag_beschikbaar=Decimal('10'),
                            klant_naam="",            # sommige diensten geven de naam niet door
                            klant_account="1234.5678.9012.3456")
        transactie.save()
        bestelling.transacties.add(transactie)

        # haal de details op (met de lege klant naam)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestelling_details % bestelling.bestel_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        # nu is er genoeg ontvangen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # restitutie toevoegen voor de coverage
        transactie = BetaalTransactie(
                            when=timezone.now(),
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE,
                            payment_id='testje',
                            beschrijving="Test beschrijving",
                            bedrag_refund=Decimal('5'),
                            klant_naam="Pietje Pijlsnel",
                            klant_account="1234.5678.9012.3456")
        transactie.save()
        bestelling.transacties.add(transactie)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # status = afgerond
        bestelling.status = BESTELLING_STATUS_AFGEROND
        bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # opnieuw afrekenen terwijl deze al betaald is
        url2 = self.url_bestelling_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url2)
        self.assert_is_redirect(resp, url)

        # corner case
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_na_de_betaling % 99999)
        self.assert404(resp, "Niet gevonden")

    def test_annuleer(self):
        # maak een bestelling en annuleer deze weer
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # leg producten in het mandje
        self.product.onbeperkte_voorraad = True
        self.product.save(update_fields=['onbeperkte_voorraad'])
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_admin, self.keuze, snel=True)
        # coverage: 2e verzoek voor dezelfde mutatie
        bestel_mutatieverzoek_webwinkel_keuze(self.account_admin, self.keuze, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.prefetch_related('producten').first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        MailQueue.objects.all().delete()

        # annuleer de bestelling
        url = self.url_annuleer_bestelling % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        # dubbele annuleer werkt niet omdat de dubbele mutatie niet aangemaakt wordt
        resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        self.verwerk_bestel_mutaties()

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_GEANNULEERD)

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Bedrag:', '>Korting:'))

        # bekijk de lijst van bestellingen, met de geannuleerde bestelling
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # haal de details op van de geannuleerde bestelling
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))

        # dubbele annuleren werkt niet (verkeerde status)
        url = self.url_annuleer_bestelling % bestelling.bestel_nr
        resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        # corner cases
        resp = self.client.post(self.url_annuleer_bestelling % 999999, {'snel': 1})
        self.assert404(resp, 'Niet gevonden')

        # annulering van geannuleerde bestelling
        url = self.url_annuleer_bestelling % bestelling.bestel_nr
        bestelling.status = BESTELLING_STATUS_NIEUW
        bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        bestelling.status = BESTELLING_STATUS_GEANNULEERD
        bestelling.save(update_fields=['status'])

        f1, f2 = self.verwerk_bestel_mutaties(show_warnings=False)
        self.assertTrue(' niet annuleren, want status ' in f2.getvalue())

        self.assertEqual(1, MailQueue.objects.count())

        # trigger een fout in de achtergrondtaak: annuleer mutatie zonder bestelling
        BestellingMutatie(code=BESTELLING_MUTATIE_ANNULEER).save()
        f1, f2, = self.verwerk_bestel_mutaties(fail_on_error=False)
        self.assertTrue('[ERROR] Onverwachte fout tijdens bestel_mutaties' in f1.getvalue())

    def test_check_status(self):
        # de dynamische aspecten van een bestelling
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # leg producten in het mandje
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_admin, self.keuze, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.prefetch_related('producten').first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        url = self.url_check_status % bestelling.bestel_nr

        # mislukt
        bestelling.status = BESTELLING_STATUS_MISLUKT
        bestelling.save(update_fields=['status'])

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # print('json data: %s' % repr(data))
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'mislukt')

        # afgerond
        bestelling.status = BESTELLING_STATUS_AFGEROND
        bestelling.save(update_fields=['status'])

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # print('json data: %s' % repr(data))
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'afgerond')

        # wacht op betaling, zonder betaal_mutatie
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['status'])

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # print('json data: %s' % repr(data))
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'error')

        # wacht op betaling, met betaal_mutatie maar zonder checkout url
        mutatie = BetaalMutatie()
        mutatie.save()
        bestelling.betaal_mutatie = mutatie
        bestelling.save(update_fields=['betaal_mutatie'])

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # print('json data: %s' % repr(data))
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'error')

        # voeg de checkout_url toe
        bestelling.betaal_mutatie.url_checkout = 'checkout_test_url'
        bestelling.betaal_mutatie.save(update_fields=['url_checkout'])

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # print('json data: %s' % repr(data))
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'betaal')
        self.assertTrue('checkout_url' in data.keys())
        checkout = data['checkout_url']
        self.assertEqual(checkout, 'checkout_test_url')

        # nieuw
        bestelling.status = BESTELLING_STATUS_NIEUW
        bestelling.betaal_mutatie = None
        bestelling.save(update_fields=['status', 'betaal_mutatie'])

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # print('json data: %s' % repr(data))
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'nieuw')

        # opnieuw (na mislukt), met bestaande transacties
        bestelling.status = BESTELLING_STATUS_NIEUW
        bestelling.save(update_fields=['status'])
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

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # print('json data: %s' % repr(data))
        self.assertTrue('status' in data.keys())
        status = data['status']
        self.assertEqual(status, 'nieuw')

        # corner case: niet bestaande status
        bestelling.status = '?'
        bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Onbekende status')

        # corner case
        url = self.url_check_status % 999999
        resp = self.client.post(url)
        self.assert404(resp, 'Niet gevonden')

    def test_stop_exactly(self):
        now = datetime.datetime.now()
        if now.minute == 0:                             # pragma: no cover
            print('Waiting until clock is past xx:00')
            while now.minute == 0:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        now = datetime.datetime.now()
        if now.second > 55:                             # pragma: no cover
            print('Waiting until clock is past xx:xx:59')
            while now.second > 55:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the current minute
        f1, f2 = self.run_management_command('bestel_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % now.minute)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # trigger the negative case
        f1, f2 = self.run_management_command('bestel_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute - 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        now = datetime.datetime.now()
        if now.minute == 59:                             # pragma: no cover
            print('Waiting until clock is past xx:59')
            while now.minute == 59:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the positive case
        f1, f2 = self.run_management_command('bestel_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute + 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

    def test_evenement_ander(self):
        # koop evenement deelname voor iemand anders
        self.sporter.email = 'sporter%s@test.not' % self.sporter.lid_nr
        sporter_account = self.e2e_create_account(str(self.sporter.lid_nr), self.sporter.email, self.sporter.voornaam)
        self.sporter.account = sporter_account
        self.sporter.save(update_fields=['account', 'email'])

        self.e2e_login(sporter_account)

        bestel_mutatieverzoek_inschrijven_evenement(sporter_account, self.evenement_inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        # simuleer een betaling
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        self.assertEqual(1, MailQueue.objects.count())
        BetaalTransactie(
            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
            payment_id='testje',
            when=betaalactief.when,
            beschrijving="Test beschrijving",
            bedrag_beschikbaar=Decimal('20.80'),
            klant_naam="Pietje Pijlsnel",
            klant_account="IBAN1234567801234").save()
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

        self.assertEqual(3, MailQueue.objects.count())
        mail = MailQueue.objects.filter(mail_subj='Inschrijving voor evenement').first()
        # print('\nmail_text = %s' % mail.mail_text)
        # print('mail_html = %s' % mail.mail_html)
        self.assert_email_html_ok(mail, 'email_bestelling/info-inschrijving-evenement.dtl')
        self.assert_consistent_email_html_text(mail)

    def test_evenement_ander_no_email_1(self):
        # koop evenement deelname voor iemand anders die geen bevestigde email heeft
        self.sporter.email = 'sporter%s@test.not' % self.sporter.lid_nr
        sporter_account = self.e2e_create_account(str(self.sporter.lid_nr), self.sporter.email, self.sporter.voornaam)
        self.sporter.account = sporter_account
        self.sporter.save(update_fields=['account', 'email'])

        self.e2e_login(sporter_account)

        # wel een account maar email is niet bevestigd
        # achtergrondtaak kies dan email van Sporter
        sporter_account.email_is_bevestigd = False
        sporter_account.save(update_fields=['email_is_bevestigd'])

        bestel_mutatieverzoek_inschrijven_evenement(sporter_account, self.evenement_inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        # simuleer een betaling
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        BetaalTransactie(
            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
            payment_id='testje',
            when=betaalactief.when,
            beschrijving="Test beschrijving",
            bedrag_beschikbaar=Decimal('20.80'),
            klant_naam="Pietje Pijlsnel",
            klant_account="IBAN1234567801234").save()
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)

    def test_evenement_ander_no_email_2(self):
        # koop evenement deelname voor iemand anders die geen email heeft
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        self.sporter.email = ''
        self.sporter.account = None
        self.sporter.save(update_fields=['account', 'email'])

        bestel_mutatieverzoek_inschrijven_evenement(self.account_admin, self.evenement_inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        # simuleer een betaling
        betaalactief = BetaalActief(
                            ontvanger=self.instellingen,
                            payment_id='testje',
                            payment_status='paid',
                            log='test')
        betaalactief.save()
        bestelling.betaal_actief = betaalactief
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_actief', 'status'])

        BetaalTransactie(
            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
            payment_id='testje',
            when=betaalactief.when,
            beschrijving="Test beschrijving",
            bedrag_beschikbaar=Decimal('20.80'),
            klant_naam="Pietje Pijlsnel",
            klant_account="IBAN1234567801234").save()
        bestel_mutatieverzoek_betaling_afgerond(betaalactief, gelukt=True, snel=True)
        self.assertEqual(3, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling' in f2.getvalue())
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)


# end of file
