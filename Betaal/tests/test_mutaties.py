# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase, override_settings
from Betaal.models import BetaalMutatie, BetaalActief, BetaalTransactie, BetaalInstellingenVereniging
from Betaal.mutaties import betaal_mutatieverzoek_start_ontvangst, betaal_mutatieverzoek_payment_status_changed
from Bestelling.models import Bestelling, BestellingMutatie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal
from mollie.api.client import Client
import datetime
import time


class TestBetaalMutaties(E2EHelpers, TestCase):

    """ tests voor de Betaal-applicatie, interactie achtergrond taak met CPSP """

    url_betaal_webhook = '/bestel/betaal/webhooks/mollie/'

    def setUp(self):
        self.account = self.e2e_create_account_admin()

        self.regio_100 = Regio.objects.get(regio_nr=100)
        self.regio_111 = Regio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=self.regio_111)
        ver.save()
        self.ver = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        instellingen = BetaalInstellingenVereniging(
                                vereniging=ver,
                                mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen = instellingen

    def _run_achtergrondtaak(self, debug=False, seconden=1):
        f1, f2 = self.verwerk_betaal_mutaties(seconden)
        if debug:           # pragma: no cover
            print('f1: %s' % f1.getvalue())
            print('f2: %s' % f2.getvalue())

        return f1, f2

    @staticmethod
    def _prep_mollie_websim(test_code):
        beschrijving = 'Test betaling %s' % test_code
        bedrag_euro_str = '42.99'

        mollie_client = Client(api_endpoint=settings.BETAAL_API_URL)
        mollie_client.set_api_key('test_1234prep')
        mollie_webhook_url = url_betaling_gedaan = settings.SITE_URL + '/plein/'

        data = {
            'amount': {'currency': 'EUR', 'value': bedrag_euro_str},
            'description': beschrijving,
            'webhookUrl': mollie_webhook_url,
            'redirectUrl': url_betaling_gedaan,
        }

        payment = mollie_client.payments.create(data)
        # print('prep_mollie_websim: payment=%s' % repr(payment))

        try:
            payment_id = payment['id_original']
        except KeyError:
            try:
                payment_id = payment['id']
            except KeyError:
                payment_id = '??'

        return payment_id

    def test_start_ontvangst(self):
        # initieer een betaling
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('42.42'))
        bestelling.save()

        # de bestelde producten met prijs en korting
        # producten = models.ManyToManyField(BestelProduct)

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        mutatie = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 42",     # 42 triggered 'paid'
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertFalse(mutatie.is_verwerkt)
        self.assertEqual(BetaalActief.objects.count(), 0)

        self._run_achtergrondtaak()

        mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        self.assertTrue(mutatie.is_verwerkt)

        self.assertEqual(BetaalActief.objects.count(), 1)
        actief = BetaalActief.objects.first()
        self.assertEqual(actief.ontvanger.pk, bestelling.ontvanger.pk)

        # genereer het payment status-changed event
        resp = self.client.post(self.url_betaal_webhook, {'id': actief.payment_id})
        self.assertEqual(resp.status_code, 200)

        self._run_achtergrondtaak()

        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertEqual(actief.payment_status, 'paid')

    def test_betaal_via_bond(self):
        # start ontvangst met betaling via de bond

        # maak de instellingen van de bond aan
        ver = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam="De bond",
                        regio=self.regio_100)
        ver.save()
        instellingen_bond = BetaalInstellingenVereniging(
                                vereniging=ver,
                                mollie_api_key='test_1234bond')
        instellingen_bond.save()

        self.instellingen.akkoord_via_bond = True
        self.instellingen.save(update_fields=['akkoord_via_bond'])

        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('42.42'))
        bestelling.save()

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        mutatie = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 42",     # 42 triggered 'paid'
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertFalse(mutatie.is_verwerkt)
        self.assertEqual(BetaalActief.objects.count(), 0)

        self._run_achtergrondtaak()

        mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        self.assertTrue(mutatie.is_verwerkt)

        self.assertEqual(BetaalActief.objects.count(), 1)
        actief = BetaalActief.objects.first()
        self.assertEqual(actief.ontvanger.pk, instellingen_bond.pk)

    def test_exceptions(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('45.45'))
        bestelling.save()

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 45",     # 45 triggert onvolledige response
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 46",  # 46 triggert bogus status
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)  # snel

        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] Missing mandatory information in create payment response: None, None, None'
                        in f1.getvalue())
        self.assertTrue("[ERROR] Onverwachte status 'bogus' in create payment response" in f1.getvalue())

        _ = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 48",  # 48 triggert te lange checkout URL
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)  # snel

        f1, f2 = self._run_achtergrondtaak()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[ERROR] Onverwachte fout tijdens betaal_mutaties:' in f1.getvalue())
        self.assertTrue('value too long for type character varying' in f1.getvalue())

        # het is niet meer mogelijk om database transacties te doen totdat deze testcase eindigt

    def test_max_pogingen(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('45.45'))
        bestelling.save()

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        mutatie = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 38",  # 38 triggert betaling "failed"
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)  # snel

        f1, f2 = self._run_achtergrondtaak()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] 1 BetaalMutaties verwerkt in 0' in f2.getvalue())

        mutatie.refresh_from_db()
        self.assertTrue(mutatie.is_verwerkt)
        self.assertEqual(mutatie.pogingen, 1)

        mutatie.is_verwerkt = False
        mutatie.pogingen = 4
        mutatie.save()

        f1, f2 = self._run_achtergrondtaak()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] 1 BetaalMutaties verwerkt in 0' in f2.getvalue())

        mutatie.refresh_from_db()
        self.assertTrue(mutatie.is_verwerkt)
        self.assertEqual(mutatie.pogingen, 5)

        # het maximum is 5, dus de volgende keer wordt deze mutatie niet meer verwerkt
        mutatie.is_verwerkt = False
        mutatie.save()

        f1, f2 = self._run_achtergrondtaak(seconden=60)
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertFalse('[INFO] 1 BetaalMutaties verwerkt in 0' in f2.getvalue())

    def test_bad_api_key(self):
        self.instellingen.mollie_api_key = 'bad_1234'
        self.instellingen.save(update_fields=['mollie_api_key'])

        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('42.42'))
        bestelling.save()

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        mutatie = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 42",     # 42 triggered 'paid'
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertFalse(mutatie.is_verwerkt)
        self.assertEqual(BetaalActief.objects.count(), 0)

        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('Invalid API key' in f1.getvalue())

        mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        self.assertTrue(mutatie.is_verwerkt)

        # er zal nu geen betaling opgestart zijn
        self.assertEqual(BetaalActief.objects.count(), 0)

    def test_betaal_failed(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('43.43'))
        bestelling.save()

        # de bestelde producten met prijs en korting
        # producten = models.ManyToManyField(BestelProduct)

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        mutatie = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 43",     # 43 triggert 'canceled'
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertFalse(mutatie.is_verwerkt)
        self.assertEqual(BetaalActief.objects.count(), 0)

        self._run_achtergrondtaak()

        mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        self.assertTrue(mutatie.is_verwerkt)

        self.assertEqual(BetaalActief.objects.count(), 1)
        actief = BetaalActief.objects.first()
        self.assertEqual(actief.ontvanger.pk, bestelling.ontvanger.pk)

        # genereer het payment status-changed event
        resp = self.client.post(self.url_betaal_webhook, {'id': actief.payment_id})
        self.assertEqual(resp.status_code, 200)

        self._run_achtergrondtaak()

        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertEqual(actief.payment_status, 'canceled')

    def test_betaal_expired(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('44.44'))
        bestelling.save()

        # de bestelde producten met prijs en korting
        # producten = models.ManyToManyField(BestelProduct)

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        mutatie = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test betaling 44",     # 44 triggert 'expired'
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertFalse(mutatie.is_verwerkt)
        self.assertEqual(BetaalActief.objects.count(), 0)

        self._run_achtergrondtaak()

        mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        self.assertTrue(mutatie.is_verwerkt)

        self.assertEqual(BetaalActief.objects.count(), 1)
        actief = BetaalActief.objects.first()
        self.assertEqual(actief.ontvanger.pk, bestelling.ontvanger.pk)

        # genereer het payment status-changed event
        resp = self.client.post(self.url_betaal_webhook, {'id': actief.payment_id})
        self.assertEqual(resp.status_code, 200)

        self._run_achtergrondtaak()

        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertEqual(actief.payment_status, 'expired')

    def test_bad(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('42.42'))
        bestelling.save()

        # de bestelde producten met prijs en korting
        # producten = models.ManyToManyField(BestelProduct)

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Test beschrijving",
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        # run with wrong port
        with override_settings(BETAAL_API_URL=settings.BETAAL_API_URL[:-2] + '99'):
            f1, f2 = self.run_management_command('betaal_mutaties', '1', '--quick')
        self.assertTrue('Unable to communicate' in f1.getvalue())

        mutatie1 = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Dit geeft code 500",
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('API response (status code: 500)' in f1.getvalue())

        # doe een dubbele aanvraag
        mutatie2 = betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        "Dit geeft code 500",
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertEqual(mutatie1.pk, mutatie2.pk)

        # genereer het payment status-changed event met een niet-bestaand payment id
        resp = self.client.post(self.url_betaal_webhook)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(self.url_betaal_webhook, {'id': 'test_niet_bestaand'})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(self.url_betaal_webhook, {'id': 'test&inject=%s!'})
        self.assertEqual(resp.status_code, 200)

        # model str() functies
        betaal = BetaalActief(payment_id="test", ontvanger=self.instellingen)
        betaal.save()
        self.assertTrue(str(betaal) != '')

        transactie = BetaalTransactie(payment_id="test", beschrijving="hoi", when=betaal.when)
        self.assertTrue(str(transactie) != '')

        instellingen = self.instellingen
        self.assertTrue(str(instellingen) != '')

        self.assertTrue(instellingen.mollie_api_key not in instellingen.obfuscated_mollie_api_key())

        mutatie = BetaalMutatie()
        mutatie.save()
        self.assertTrue(str(mutatie) != '')

        mutatie.is_verwerkt = True
        mutatie.code = 1
        self.assertTrue(str(mutatie) != '')

    def test_status_changed(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('99.01'))
        bestelling.save()

        payment_id = 'test123'

        # ignore, want geen BetaalActief
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        self._run_achtergrondtaak()
        # lastig / niet te checken

        # maak de BetaalActief aan
        BetaalActief(
            payment_id=payment_id,
            ontvanger=self.instellingen,
            log='testje').save()
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] Unexpected exception from Mollie payments.get: Invalid payment ID' in f1.getvalue())

        # maak de payment aan in de websim met een foutieve payment_id
        payment_id = self._prep_mollie_websim(47)
        actief = BetaalActief(
            payment_id=payment_id,
            ontvanger=self.instellingen,
            log='testje')
        actief.save()
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] Mismatch in payment id:' in f1.getvalue())

        # maak de payment aan in de websim met een bijna leeg antwoord
        self._prep_mollie_websim(45)        # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] Missing mandatory information in get payment response: None, None' in f1.getvalue())

        # een status=failed payment
        self._prep_mollie_websim(39)        # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue("[INFO] Payment tr_1234AbcdEFGH status aangepast: '' --> 'failed'" in f2.getvalue())

        # een status=pending payment
        self._prep_mollie_websim(40)        # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue("[INFO] Payment tr_1234AbcdEFGH status aangepast: 'failed' --> 'pending'" in f2.getvalue())

        # een status=open payment
        self._prep_mollie_websim(41)        # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue("[INFO] Payment tr_1234AbcdEFGH status aangepast: 'pending' --> 'open'" in f2.getvalue())

        # een status=canceled payment
        self._prep_mollie_websim(43)        # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue("[INFO] Payment tr_1234AbcdEFGH status aangepast: 'open' --> 'canceled'" in f2.getvalue())
        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertTrue('Betaling is mislukt' in actief.log)

        # een status=paid, with issue
        self._prep_mollie_websim(425)       # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] {payment_opslaan} Incomplete details voor card: ' in f1.getvalue())
        self.assertTrue('[WARNING] Payment tr_1234AbcdEFGH bevat een probleem' in f2.getvalue())

        # een status=paid, with issue
        self._prep_mollie_websim(426)       # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] {payment_opslaan} Incomplete details over consumer: ' in f1.getvalue())
        self.assertTrue('[WARNING] Payment tr_1234AbcdEFGH bevat een probleem' in f2.getvalue())

        # een status=paid, with issue
        self._prep_mollie_websim(427)       # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] {payment_opslaan} Probleem met value in' in f1.getvalue())
        self.assertTrue('[WARNING] Payment tr_1234AbcdEFGH bevat een probleem' in f2.getvalue())

        # een status=paid, with issue
        self._prep_mollie_websim(428)       # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('[ERROR] {payment_opslaan} Currency not in EUR' in f1.getvalue())
        self.assertTrue('[WARNING] Payment tr_1234AbcdEFGH bevat een probleem' in f2.getvalue())

        # een status=paid, with issue (geen settlement amount)
        self._prep_mollie_websim(429)       # hergebruik standaard websim payment_id
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2 = self._run_achtergrondtaak()
        self.assertFalse('[ERROR] {payment_opslaan} Missing field: ' in f1.getvalue())

    def test_paid_ideal(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('99.01'))
        bestelling.save()

        self.assertEqual(0, BestellingMutatie.objects.count())

        # maak de payment met status=paid en method=ideal
        payment_id = self._prep_mollie_websim(421)
        actief = BetaalActief(
                        payment_id=payment_id,
                        ontvanger=self.instellingen,
                        log='testje')
        actief.save()
        bestelling.betaal_actief = actief
        bestelling.save(update_fields=['betaal_actief'])
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        self._run_achtergrondtaak()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertTrue('Betaling is voldaan' in actief.log)

        # controleer dat een BestellingMutatie aangemaakt is
        self.assertEqual(1, BestellingMutatie.objects.count())

    def test_paid_creditcard(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('99.01'))
        bestelling.save()

        # maak de payment met status=paid en method=creditcard
        payment_id = self._prep_mollie_websim(422)
        actief = BetaalActief(
            payment_id=payment_id,
            ontvanger=self.instellingen,
            log='testje')
        actief.save()
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        self._run_achtergrondtaak()
        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertTrue('Betaling is voldaan' in actief.log)

    def test_paid_paypal(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('99.01'))
        bestelling.save()

        # maak de payment met status=paid en method=paypal
        payment_id = self._prep_mollie_websim(423)
        actief = BetaalActief(
                        payment_id=payment_id,
                        ontvanger=self.instellingen,
                        log='testje')
        actief.save()
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        self._run_achtergrondtaak()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertTrue('Betaling is voldaan' in actief.log)

    def test_paid_bancontact(self):
        # 'method': 'bancontact',
        # 'details': {'consumerName': None,                       # LET OP!
        #             'consumerAccount': 'BE12345678901234',
        #             'consumerBic': 'AXABBE22'},               # noqa
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('99.01'))
        bestelling.save()

        # maak de payment met status=paid en method=bancontact
        payment_id = self._prep_mollie_websim(424)
        actief = BetaalActief(
            payment_id=payment_id,
            ontvanger=self.instellingen,
            log='testje')
        actief.save()
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        self._run_achtergrondtaak()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        actief = BetaalActief.objects.get(pk=actief.pk)
        self.assertTrue('Betaling is voldaan' in actief.log)

    def test_status_changed_bad_api_key(self):
        self.instellingen.mollie_api_key = 'hallo daar'
        self.instellingen.save()

        payment_id = 'test123'

        # maak de BetaalActief aan
        BetaalActief(
            payment_id=payment_id,
            ontvanger=self.instellingen,
            log='testje').save()
        betaal_mutatieverzoek_payment_status_changed(payment_id)

        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('Unexpected exception from Mollie set API key' in f1.getvalue())

    def test_status_changed_via_bond(self):
        # maak de instellingen van de bond aan
        ver = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam="De bond",
                        regio=self.regio_100)
        ver.save()
        instellingen_bond = BetaalInstellingenVereniging(
                                vereniging=ver,
                                mollie_api_key='test_1234bond')
        instellingen_bond.save()

        # heeft Mollie key, dus hoeft niet handmatig
        self.assertFalse(self.instellingen.moet_handmatig())
        self.instellingen.akkoord_via_bond = True
        self.assertFalse(self.instellingen.moet_handmatig())

        self.instellingen.save(update_fields=['akkoord_via_bond'])

        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('99.01'))
        bestelling.save()

        payment_id = 'test123'

        # maak de BetaalActief aan
        BetaalActief(
            payment_id=payment_id,
            ontvanger=self.instellingen,
            log='testje').save()
        betaal_mutatieverzoek_payment_status_changed(payment_id)
        f1, f2, = self._run_achtergrondtaak()

        self.assertTrue('[ERROR] Unexpected exception from Mollie payments.get: Invalid payment ID' in f1.getvalue())

        self.instellingen.mollie_api_key = ''
        self.instellingen.akkoord_via_bond = False
        self.assertTrue(self.instellingen.moet_handmatig())

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
        self.run_management_command('betaal_mutaties', '1', '--quick',
                                    '--stop_exactly=%s' % now.minute)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # trigger the negative case
        prev_min = (now.minute - 1) % 60
        self.run_management_command('betaal_mutaties', '1', '--quick',
                                    '--stop_exactly=%s' % prev_min)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # now = datetime.datetime.now()
        # if now.minute == 59:                             # pragma: no cover
        #     print('Waiting until clock is past xx:59')
        #     while now.minute == 59:
        #         time.sleep(5)
        #         now = datetime.datetime.now()
        #     # while

        # trigger the positive case
        next_min = (now.minute + 1) % 60
        self.run_management_command('betaal_mutaties', '1', '--quick',
                                    '--stop_exactly=%s' % next_min)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))


# end of file
