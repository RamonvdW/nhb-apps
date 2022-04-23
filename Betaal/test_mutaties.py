# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.core import management
from django.conf import settings
from Betaal.models import BetaalMutatie, BetaalActief, BetaalTransactie, BetaalInstellingenVereniging
from Betaal.mutaties import betaal_start_ontvangst, betaal_payment_status_changed
from Bestel.models import Bestelling
from Functie.models import maak_functie
from NhbStructuur.models import NhbVereniging, NhbRegio
from TestHelpers.e2ehelpers import E2EHelpers
from decimal import Decimal
import io


class TestBetaalMutaties(E2EHelpers, TestCase):

    """ tests voor de Betaal applicatie, interactie achtergrond taak met CPSP """

    url_websim_api = 'http://localhost:8125'
    url_betaal_webhook = '/bestel/betaal/webhooks/mollie/'

    def setUp(self):
        self.account = self.e2e_create_account_admin()

        self.regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        instellingen = BetaalInstellingenVereniging(
                                vereniging=ver,
                                mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen = instellingen

    def _run_achtergrondtaak(self, betaal_api=None, debug=False):
        if betaal_api is None:
            betaal_api = self.url_websim_api

        f1 = io.StringIO()
        f2 = io.StringIO()
        with override_settings(BETAAL_API=betaal_api):
            management.call_command('betaal_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if debug:
            print('f1: %s' % f1.getvalue())
            print('f2: %s' % f2.getvalue())

        return f1, f2

    def test_betaal(self):
        bestelling = Bestelling(
                            bestel_nr=1,
                            account=self.account,
                            ontvanger=self.instellingen,
                            totaal_euro=Decimal('42.42'))
        bestelling.save()

        # de bestelde producten met prijs en korting
        # producten = models.ManyToManyField(BestelProduct)

        url_betaling_gedaan = settings.SITE_URL + '/plein/'

        mutatie = betaal_start_ontvangst(
                        bestelling,
                        "Test betaling 42",
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertFalse(mutatie.is_verwerkt)
        self.assertEqual(BetaalActief.objects.count(), 0)

        self._run_achtergrondtaak()

        mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        self.assertTrue(mutatie.is_verwerkt)

        self.assertEqual(BetaalActief.objects.count(), 1)
        actief = BetaalActief.objects.all()[0]
        self.assertEqual(actief.ontvanger.pk, bestelling.ontvanger.pk)

        # genereer het payment status-changed event
        resp = self.client.post(self.url_betaal_webhook, {'id': actief.payment_id})
        self.assertEqual(resp.status_code, 200)

        self._run_achtergrondtaak(debug=True)
        # TODO: complete

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

        betaal_start_ontvangst(
                        bestelling,
                        "Test beschrijving",
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        # run with wrong port
        f1, f2 = self._run_achtergrondtaak(betaal_api=self.url_websim_api[:-2] + '99')
        self.assertTrue('Unable to communicate' in f1.getvalue())

        mutatie1 = betaal_start_ontvangst(
                        bestelling,
                        "Dit geeft code 500",
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel
        f1, f2 = self._run_achtergrondtaak()
        self.assertTrue('API response (status code: 500)' in f1.getvalue())

        # doe een dubbele aanvraag
        mutatie2 = betaal_start_ontvangst(
                        bestelling,
                        "Dit geeft code 500",
                        bestelling.totaal_euro,
                        url_betaling_gedaan,
                        True)       # snel

        self.assertEqual(mutatie1.pk, mutatie2.pk)

        # genereer het payment status-changed event met een niet-bestaand payment id
        resp = self.client.post(self.url_betaal_webhook)
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post(self.url_betaal_webhook, {'id': 'test_nietbestaand'})
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post(self.url_betaal_webhook, {'id': 'test&inject=%s!'})
        self.assertEqual(resp.status_code, 400)

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

# end of file
