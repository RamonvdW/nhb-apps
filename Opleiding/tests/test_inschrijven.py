# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from Bestelling.models import Bestelling, BestellingMandje
from Bestelling.operations.mutaties import bestel_mutatieverzoek_maak_bestellingen
from Betaal.models import BetaalMutatie, BetaalInstellingenVereniging
from Betaal.mutaties import betaal_mutatieverzoek_start_ontvangst
from Functie.models import Functie
from Geo.models import Regio
from Instaptoets.models import Vraag, Instaptoets
from Mailer.models import MailQueue
from Opleiding.definities import (OPLEIDING_STATUS_INSCHRIJVEN, OPLEIDING_STATUS_GEANNULEERD,
                                  OPLEIDING_INSCHRIJVING_STATUS_INSCHRIJVEN,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                                  OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF)
from Opleiding.models import Opleiding, OpleidingInschrijving, OpleidingAfgemeld
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal
import datetime
import json
import re


class TestOpleidingInschrijven(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit Inschrijven """

    test_after = ('Account', 'Functie', 'Bestelling.tests.test_bestelling')

    url_inschrijven_basiscursus = '/opleiding/inschrijven/basiscursus/'
    url_toevoegen_aan_mandje = '/opleiding/inschrijven/toevoegen-mandje/'
    url_mandje_toon = '/bestel/mandje/'
    url_mandje_verwijder = '/bestel/mandje/verwijderen/%s/'     # product_pk
    url_na_de_betaling = '/bestel/na-de-betaling/%s/'           # bestel_nr
    url_betaal_webhook = '/bestel/betaal/webhooks/mollie/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

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

        now = timezone.now()
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
                    account=self.account_normaal)
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
        self.opleiding = opleiding

        # geannuleerde opleiding
        opleiding = Opleiding(
                        titel="Test 2",
                        is_basiscursus=True,
                        periode_begin="2024-02-01",
                        periode_einde="2024-03-01",
                        beschrijving="Test niet meer",
                        status=OPLEIDING_STATUS_GEANNULEERD)
        opleiding.save()
        self.opleiding_geannuleerd = opleiding

        # niet-basiscursus
        Opleiding(
                titel="Test 3",
                is_basiscursus=False,
                periode_begin="2024-02-01",
                periode_einde="2024-03-01",
                beschrijving="Test nog steeds",
                status=OPLEIDING_STATUS_INSCHRIJVEN).save()

        # maak de instaptoets beschikbaar
        Vraag().save()

        # instaptoets in progress
        toets = Instaptoets(
                    sporter=sporter,
                    aantal_vragen=10,
                    aantal_antwoorden=5)
        toets.save()
        self.toets = toets
        self.toets_niet_afgerond_datetime = toets.afgerond

    def _zet_instaptoets_gehaald(self):
        now = timezone.now() - datetime.timedelta(days=10)
        Instaptoets.objects.filter(pk=self.toets.pk).update(
                afgerond=now,
                aantal_antwoorden=10,
                is_afgerond=True,
                aantal_goed=9,
                geslaagd=True)

    def _zet_instaptoets_gezakt(self):
        Instaptoets.objects.filter(pk=self.toets.pk).update(
                afgerond=self.toets_niet_afgerond_datetime,
                aantal_antwoorden=10,
                is_afgerond=True,
                aantal_goed=5,
                geslaagd=False)

    def _zet_instaptoets_niet_af(self):
        Instaptoets.objects.filter(pk=self.toets.pk).update(
                afgerond=self.toets_niet_afgerond_datetime,
                aantal_antwoorden=5,
                is_afgerond=False,
                aantal_goed=0,
                geslaagd=False)

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assert_is_redirect_login(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus)
        self.assert_is_redirect_login(resp)

    def test_gast(self):
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assert403(resp, 'Geen toegang')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus)
        self.assert403(resp, 'Geen toegang')

    def test_beheerder(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assert403(resp, 'Geen toegang')

    def test_geen_opleiding(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        Opleiding.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assert404(resp, 'Basiscursus niet gevonden')

    def test_toets_niet_gestart(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self.toets.delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_toets_niet_af(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_niet_af()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_toets_gezakt(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gezakt()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

    def test_toets_gehaald(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [self.url_toevoegen_aan_mandje])

    def test_wijzigen_doorgeven(self):
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # geen JSON
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus)       # geen data
        self.assert404(resp, 'Geen valide verzoek')
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # foute keys
        data = {'niet nodig': 'onverwacht'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # nieuwe gegevens
        data = {'email': 'voor.opleiding@khsn.not',
                'plaats': 'Boogstad',
                'telefoon': '12345'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.aanpassing_email, 'voor.opleiding@khsn.not')
        self.assertEqual(inschrijving.aanpassing_telefoon, '12345')
        self.assertEqual(inschrijving.aanpassing_geboorteplaats, 'Boogstad')

        # geen wijzigingen --> geen toevoegingen aan logboekje
        data = {'email': 'voor.opleiding@khsn.not',
                'plaats': 'Boogstad',
                'telefoon': '12345'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        # get toont ingevoerde gegevens
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))

        # gelijk aan bekende gegevens
        data = {'email': self.sporter.email,
                'plaats': self.sporter.geboorteplaats,
                'telefoon': self.sporter.telefoon}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.aanpassing_email, '')
        self.assertEqual(inschrijving.aanpassing_telefoon, '')
        self.assertEqual(inschrijving.aanpassing_geboorteplaats, '')

        self.assertTrue(inschrijving.korte_beschrijving() != '')
        self.assertTrue(str(inschrijving) != '')

        # corner case: geen basiscursus
        OpleidingInschrijving.objects.all().delete()
        Opleiding.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)

    def test_mandje(self):
        # leg de inschrijving voor de opleiding in het mandje
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)

        # zonder opleiding_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje)
        self.assert404(resp, 'Slecht verzoek')

        # bad opleiding_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': '##'})
        self.assert404(resp, 'Slecht verzoek')

        # niet bestaande opleiding_pk
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': 999999})
        self.assert404(resp, 'Slecht verzoek (2)')

        self.assertEqual(OpleidingInschrijving.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_INSCHRIJVEN)

        # laat de achtergrond taak het toevoegen aan het mandje verwerken
        self.verwerk_bestel_mutaties()

        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE)
        self.assertTrue('Toegevoegd aan het mandje van' in inschrijving.log)

        # bekijk de inhoud van het mandje (dit vraagt om beschrijving van de opleiding)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_mandje_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/toon-mandje.dtl', 'plein/site_layout.dtl'))

        # verwijder uit het mandje
        regel = inschrijving.bestelling
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_mandje_verwijder % regel.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_mandje_toon)

        # laat de achtergrond taak het verwijderen uit het mandje verwerken
        self.verwerk_bestel_mutaties()

        # omdat het nog geen bestelling was, is alles verwijderd
        self.assertEqual(OpleidingInschrijving.objects.filter(pk=inschrijving.pk).count(), 0)
        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)
        self.assertEqual(Bestelling.objects.count(), 0)

        # geen rol=sporter
        self.e2e_wissel_naar_functie(self.functie_mo)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje)
        self.assert403(resp, 'Geen toegang')

        # corner case: gast-account
        self.e2e_wisselnaarrol_sporter()
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje)
        self.assert403(resp, 'Geen toegang')

    def test_bestelling_gratis(self):
        # bestel een gratis opleiding
        # deze wordt meteen definitief gemaakt bij omzetten mandje naar bestelling
        self.opleiding.kosten_euro = 0
        self.opleiding.save(update_fields=['kosten_euro'])

        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()

        self.assertEqual(OpleidingInschrijving.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        # laat de achtergrond taak het toevoegen aan het mandje verwerken
        self.verwerk_bestel_mutaties()

        # omzetten in een bestelling
        self.assertEqual(Bestelling.objects.count(), 0)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1: %s\nf2: %s\n' % (f1.getvalue(), f2.getvalue()))

        self.assertEqual(Bestelling.objects.count(), 1)
        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF)

        # check the mail die gemaakt is
        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail)

    def test_bestelling_betaling(self):
        # maak een bestelling
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()

        self.assertEqual(OpleidingInschrijving.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)
        inschrijving = OpleidingInschrijving.objects.first()

        # laat de achtergrond taak het toevoegen aan het mandje verwerken
        self.verwerk_bestel_mutaties()

        # omzetten in een bestelling
        self.assertEqual(Bestelling.objects.count(), 0)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1: %s\nf2: %s\n' % (f1.getvalue(), f2.getvalue()))

        self.assertEqual(Bestelling.objects.count(), 1)
        bestelling = Bestelling.objects.first()

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_BESTELD)

        # check the mail die gemaakt is
        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail)        # , ignore=('>Prijs:', '>Korting:')

        # betaling opstarten
        url_betaling_gedaan = '/plein/'     # FUTURE: betere url kiezen
        description = 'Test betaling 421'       # 421 = paid, iDEAL
        betaal_mutatieverzoek_start_ontvangst(bestelling, description, self.opleiding.kosten_euro,
                                              url_betaling_gedaan, snel=True)
        f1, f2 = self.verwerk_betaal_mutaties()
        # print('\nf1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        # haal de betaal status pagina op
        bestelling.refresh_from_db()
        betaal_mutatie = bestelling.betaal_mutatie
        self.assertTrue(betaal_mutatie.url_checkout != '')
        self.assertTrue(betaal_mutatie.payment_id != '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_na_de_betaling % bestelling.bestel_nr, {'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # fake het gebruik van de CPSP checkout en de payment-status-changed callback
        count = BetaalMutatie.objects.count()
        resp = self.client.post(self.url_betaal_webhook, {'id': betaal_mutatie.payment_id})
        # self.e2e_dump_resp(resp)
        self.assertEqual(resp.status_code, 200)     # 200 = success, 400 = error
        self.assertEqual(BetaalMutatie.objects.count(), count+1)

        # laat de mutatie verwerken die door de callback aangemaakt is
        f1, f2 = self.verwerk_betaal_mutaties()
        self.assertTrue("status aangepast: 'open' --> 'paid'" in f2.getvalue())

        # maak de uitgaande mail queue leeg
        MailQueue.objects.all().delete()

        # laat mutatie verwerken die betaal daemon richting bestel daemon heeft gestuurd
        f1, f2 = self.verwerk_bestel_mutaties()
        msg = f2.getvalue()
        msg = re.sub(r'pk=[0-9]+', 'pk=X', msg)
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling MH-1002001 (pk=X)' in msg)
        self.assertTrue('[INFO] Bestelling MH-1002001 (pk=X) heeft € 10,00 van de € 10,00 ontvangen' in msg)
        self.assertTrue('[INFO] Bestelling MH-1002001 (pk=X) is afgerond' in msg)

        self.assertEqual(1, bestelling.transacties.count())

        # controleer dat een e-mailbevestiging van de betaling aangemaakt is
        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-betaling.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Prijs:', '>Korting:'))

        # controleer dat de inschrijving nu op 'definitief' staat
        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(inschrijving.bedrag_ontvangen, Decimal('10'))

    def test_inschrijven_met_wijzigingen(self):
        # geef eerst wijzigingen door
        # daarna inschrijven

        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()

        # wijzigingen doorgeven
        self.assertEqual(OpleidingInschrijving.objects.count(), 0)
        data = {'email': 'voor.opleiding@khsn.not',
                'plaats': 'Boogstad',
                'telefoon': '12345'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_inschrijven_basiscursus,
                                    json.dumps(data),
                                    content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)

        # laat de achtergrond taak het toevoegen aan het mandje verwerken
        self.verwerk_bestel_mutaties()

        # omzetten in een bestelling
        self.assertEqual(Bestelling.objects.count(), 0)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1: %s\nf2: %s\n' % (f1.getvalue(), f2.getvalue()))

        self.assertEqual(Bestelling.objects.count(), 1)

    def test_al_ingeschreven(self):
        # controleer dat dubbel inschrijven niet mogelijk is
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self._zet_instaptoets_gehaald()

        self.opleiding.kosten_euro = 0
        self.opleiding.save(update_fields=['kosten_euro'])

        # haal de inschrijfpagina op en controleer dat er een knop is om in te schrijven
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_toevoegen_aan_mandje in urls)

        self.assertEqual(OpleidingInschrijving.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        self.verwerk_bestel_mutaties()

        mandje = BestellingMandje.objects.first()
        self.assertEqual(mandje.aantal_in_mandje(), 1)

        self.assertEqual(OpleidingInschrijving.objects.count(), 1)
        inschrijving = OpleidingInschrijving.objects.first()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # haal de inschrijfpagina op en controleer dat er GEEN knop is om in te schrijven
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_toevoegen_aan_mandje not in urls)

        # probeer nog een keer in te schrijven
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assert404(resp, 'Dubbel inschrijven niet mogelijk')

        self.verwerk_bestel_mutaties()
        self.assertEqual(mandje.aantal_in_mandje(), 1)

        # omzetten in een bestelling
        self.assertEqual(Bestelling.objects.count(), 0)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        self.assertEqual(Bestelling.objects.count(), 1)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF)

        mandje = BestellingMandje.objects.first()
        self.assertEqual(mandje.aantal_in_mandje(), 0)

        # probeer nog een keer in te schrijven (met een leeg mandje)

        # haal de inschrijfpagina op en controleer dat er GEEN knop is om in te schrijven
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_inschrijven_basiscursus)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-basiscursus.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_toevoegen_aan_mandje not in urls)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assert404(resp, 'Dubbel inschrijven niet mogelijk')
        self.assertEqual(mandje.aantal_in_mandje(), 0)


# end of file
