# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_NIEUW,
                                   BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_REGEL_CODE_OPLEIDING)
from Bestelling.models import BestellingMandje, Bestelling, BestellingRegel
from Bestelling.operations import bestel_mutatieverzoek_inschrijven_wedstrijd
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalMutatie, BetaalTransactie
from Betaal.mutaties import betaal_mutatieverzoek_start_ontvangst
from Geo.models import Regio
from Mailer.models import MailQueue
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.definities import VER_NR_BONDSBUREAU
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from decimal import Decimal
import re


# TODO: strip intieme kennis over bestellingen en betalingen --> laat bestelling/betaal helper dat regelen

# TODO: voeg een test toe die controleert dat we echt op een checkout pagina terecht komen

class TestBestellingBetaling(E2EHelpers, TestCase):

    """ tests voor de applicatie Bestelling, samenwerking met applicatie Bestelling en Betaal """

    test_after = ('Bestelling.tests.test_bestelling',)

    url_afrekenen = '/bestel/afrekenen/%s/'                 # bestel_nr
    url_check_status = '/bestel/check-status/%s/'           # bestel_nr
    url_na_de_betaling = '/bestel/na-de-betaling/%s/'       # bestel_nr
    url_betaal_webhook = '/bestel/betaal/webhooks/mollie/'

    url_mandje_bestellen = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'

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
                    regio=Regio.objects.get(regio_nr=112))
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

        mandje, is_created = BestellingMandje.objects.get_or_create(account=account)
        self.mandje = mandje

        ver = Vereniging.objects.get(ver_nr=VER_NR_BONDSBUREAU)
        ver.naam = 'Bondsbureau'
        ver.adres_regel1 = 'Sportlaan 1'
        ver.adres_regel2 = 'Sportstad'
        ver.kvk_nummer = '123456'
        ver.telefoonnummer = '123456789'
        ver.bank_iban = 'IBAN123456789'
        ver.bank_bic = 'BIC4NL'
        ver.save()

    def _maak_bestelling(self):
        # bestel wedstrijddeelname in het mandje
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)   # !is_created
        self.verwerk_bestel_mutaties()

        # zorg dat alle mogelijke optionele velden in gebruik zijn
        mandje = BestellingMandje.objects.get(account=self.account_admin)
        mandje.afleveradres_regel_1 = 'Ontvanger'
        mandje.afleveradres_regel_2 = 'Straat'
        mandje.afleveradres_regel_3 = 'Postcode'
        mandje.afleveradres_regel_4 = 'Plaats'
        mandje.afleveradres_regel_5 = 'Land'
        mandje.save()

        regel = BestellingRegel(
                    korte_beschrijving='test btw 1',
                    bedrag_euro=Decimal(2),
                    btw_percentage='21,1',
                    btw_euro=Decimal(1),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()
        mandje.regels.add(regel)

        regel = BestellingRegel(
                    korte_beschrijving='test btw 2',
                    bedrag_euro=Decimal(2),
                    btw_percentage='15',
                    btw_euro=Decimal(1),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()
        mandje.regels.add(regel)

        regel = BestellingRegel(
                    korte_beschrijving='test btw 3',
                    bedrag_euro=Decimal(2),
                    btw_percentage='9',
                    btw_euro=Decimal(1),
                    code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()
        mandje.regels.add(regel)

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)

        self.verwerk_bestel_mutaties(fail_on_error=False)

        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        return bestelling

    def test_anon(self):
        resp = self.client.get(self.url_afrekenen % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_check_status % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_na_de_betaling % 999999)
        self.assert403(resp)

    def test_afrekenen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        resp = self.client.get(self.url_afrekenen % 999999)
        self.assert404(resp, 'Niet gevonden')

        # maak de uitgaande mail queue leeg
        MailQueue.objects.all().delete()

        bestelling = self._maak_bestelling()

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_afrekenen % bestelling.bestel_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afrekenen.dtl', 'plein/site_layout.dtl'))

        # betaling opstarten
        url_betaling_gedaan = '/plein/'     # FUTURE: betere url kiezen
        description = 'Test betaling 421'       # 421 = paid, iDEAL
        betaal_mutatieverzoek_start_ontvangst(bestelling, description, bestelling.totaal_euro,
                                              url_betaling_gedaan, snel=True)
        self.verwerk_betaal_mutaties()

        # check dat de transactie inderdaad opgestart is
        bestelling = Bestelling.objects.select_related('betaal_mutatie', 'betaal_actief').get(pk=bestelling.pk)
        self.assertIsNotNone(bestelling.betaal_mutatie)     # BetaalMutatie
        self.assertIsNotNone(bestelling.betaal_actief)      # BetaalActief
        self.assertEqual(0, bestelling.transacties.count())
        self.assertTrue(str(bestelling) != '')

        betaal_mutatie = bestelling.betaal_mutatie
        self.assertTrue(betaal_mutatie.url_checkout != '')
        self.assertTrue(betaal_mutatie.payment_id != '')

        betaal_actief = bestelling.betaal_actief
        self.assertEqual(betaal_actief.ontvanger, self.instellingen_bond)    # want akkoord_via_bond
        self.assertTrue(betaal_actief.payment_id != '')
        self.assertEqual(betaal_actief.payment_status, 'open')

        # haal de betaal status pagina op
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
        count = BetaalTransactie.objects.count()
        f1, f2 = self.verwerk_betaal_mutaties()
        self.assertTrue("status aangepast: 'open' --> 'paid'" in f2.getvalue())

        betaal_actief = BetaalActief.objects.get(pk=bestelling.betaal_actief.pk)
        self.assertEqual(betaal_actief.payment_status, 'paid')

        # betaal mutatie heeft BetaalTransactie aangemaakt
        self.assertEqual(BetaalTransactie.objects.count(), count+1)

        # koppeling van transactie aan bestelling wordt door bestel daemon gedaan
        bestelling.refresh_from_db()
        self.assertEqual(0, bestelling.transacties.count())

        # maak de uitgaande mail queue leeg
        MailQueue.objects.all().delete()

        # laat mutatie verwerken die de Betaal richting Bestelling heeft gestuurd
        f1, f2 = self.verwerk_bestel_mutaties(fail_on_error=False)
        msg = f2.getvalue()
        msg = re.sub(r'pk=[0-9]+', 'pk=X', msg)
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling MH-1002001 (pk=X)' in msg)
        self.assertTrue('[INFO] Bestelling MH-1002001 (pk=X) heeft € 16,00 van de € 16,00 ontvangen' in msg)
        self.assertTrue('[INFO] Bestelling MH-1002001 (pk=X) is afgerond' in msg)

        self.assertEqual(1, bestelling.transacties.count())

        # controleer dat een e-mailbevestiging van de betaling aangemaakt is
        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-betaling.dtl')
        self.assert_consistent_email_html_text(mail)  #, ignore=('>Prijs:', '>Korting:'))
        print('{betaling email} %s' % mail.mail_text)

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertIsNotNone(bestelling.betaal_mutatie)     # BetaalMutatie
        self.assertIsNone(bestelling.betaal_actief)         # BetaalActief
        self.assertEqual(1, bestelling.transacties.count())

        # controleer dat de inschrijving nu op 'definitief' staat
        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('10'))
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

        # bij nog een poging om te betalen worden we doorgestuurd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_afrekenen % bestelling.bestel_nr)
        self.assert_is_redirect(resp, self.url_na_de_betaling % bestelling.bestel_nr)

    def test_afrekenen_nogmaals(self):
        self.e2e_login(self.account_admin)
        self.e2e_check_rol('sporter')

        resp = self.client.get(self.url_afrekenen % 999999)
        self.assert404(resp, 'Niet gevonden')

        bestelling = self._maak_bestelling()

        bestelling.status = BESTELLING_STATUS_MISLUKT
        bestelling.save(update_fields=['status'])

        url = self.url_afrekenen % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

        bestelling.refresh_from_db()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_NIEUW)

        # nog een keer heeft geen zin
        resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

    def test_check_status(self):
        self.e2e_login(self.account_admin)
        self.e2e_check_rol('sporter')

        resp = self.client.get(self.url_check_status % 999999)
        self.assert405(resp)

        resp = self.client.post(self.url_check_status % 999999)
        self.assert404(resp, 'Niet gevonden')

        bestelling = self._maak_bestelling()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status % bestelling.bestel_nr)
        data = self.assert200_json(resp)
        self.assertEqual(data, {'status': 'nieuw'})

        # transitie van Nieuw naar Betaling actief
        self.verwerk_betaal_mutaties()
        bestelling.refresh_from_db()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_BETALING_ACTIEF)

        # lege checkout url
        mutatie = bestelling.betaal_mutatie
        mutatie.url_checkout = ''
        mutatie.save()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status % bestelling.bestel_nr)
        data = self.assert200_json(resp)
        self.assertEqual(data, {'status': 'error'})

        # normale checkout url
        mutatie.url_checkout = '/checkout/'
        mutatie.save()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status % bestelling.bestel_nr)
        data = self.assert200_json(resp)
        self.assertEqual(data, {'status': 'betaal', 'checkout_url': '/checkout/'})

        # geen betaling mutatie
        bestelling.betaal_mutatie = None
        bestelling.save(update_fields=['betaal_mutatie'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status % bestelling.bestel_nr)
        data = self.assert200_json(resp)
        self.assertEqual(data, {'status': 'error'})

        # afgerond
        bestelling.status = BESTELLING_STATUS_AFGEROND
        bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status % bestelling.bestel_nr)
        data = self.assert200_json(resp)
        self.assertEqual(data, {'status': 'afgerond'})

        # mislukt
        bestelling.status = BESTELLING_STATUS_MISLUKT
        bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status % bestelling.bestel_nr)
        data = self.assert200_json(resp)
        # print(repr(data))
        self.assertEqual(data, {'status': 'mislukt'})

        bestelling.status = BESTELLING_STATUS_GEANNULEERD
        bestelling.save(update_fields=['status'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_check_status % bestelling.bestel_nr)
        self.assert404(resp, 'Onbekende status')

    def test_afgerond(self):
        self.e2e_login(self.account_admin)
        self.e2e_check_rol('sporter')

        resp = self.client.get(self.url_na_de_betaling % 999999)
        self.assert404(resp, 'Niet gevonden')

        bestelling = self._maak_bestelling()

        bestelling.status = BESTELLING_STATUS_AFGEROND
        bestelling.save(update_fields=['status'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_na_de_betaling % bestelling.bestel_nr, {'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        bestelling.status = BESTELLING_STATUS_MISLUKT
        bestelling.save(update_fields=['status'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_na_de_betaling % bestelling.bestel_nr, {'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))


# end of file
