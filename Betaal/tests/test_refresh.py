# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from Betaal.models import BetaalActief, BetaalInstellingenVereniging
from Geo.models import Regio
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from mollie.api.client import Client


class TestBetaalRefresh(E2EHelpers, TestCase):

    """ tests voor de Betaal-applicatie, CLI mollie_refresh """

    url_betaal_webhook = '/bestel/betaal/webhooks/mollie/'

    def setUp(self):
        self.account = self.e2e_create_account_admin()

        self.regio_111 = Regio.objects.get(regio_nr=111)

        # maak een test vereniging
        self.ver_nr = 1000
        ver = Vereniging(
                    ver_nr=self.ver_nr,
                    naam="Grote Club",
                    regio=self.regio_111)
        ver.save()
        self.ver = ver

        instellingen = BetaalInstellingenVereniging(
                                vereniging=ver,
                                mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen = instellingen

    def _do_mollie_refresh(self, ver_nr=None, debug=False):
        if ver_nr is None:
            ver_nr = self.ver_nr
        f1, f2, = self.run_management_command('mollie_refresh', ver_nr)
        if debug:       # pragma: no cover
            print('\nf1: %s' % f1.getvalue())
            print('f2: %s' % f2.getvalue())

        # controleer op onverwachte fouten
        # let op: [ERROR] komt voor in normaal gebruik
        err_msg = f1.getvalue()
        if 'Traceback:' in err_msg:         # pragma: no cover
            self.fail(msg='Onverwachte fout van mollie_refresh:\n' + err_msg)
        return f1, f2

    def _prep_mollie_websim(self, test_code):
        beschrijving = 'Test betaling %s' % test_code
        bedrag_euro_str = '42.99'

        mollie_client = Client(api_endpoint=settings.BETAAL_API_URL)
        mollie_client.set_api_key(self.instellingen.mollie_api_key)
        mollie_webhook_url = url_betaling_gedaan = settings.SITE_URL + '/plein/'

        data = {
            'amount': {
                'currency': 'EUR',
                'value': bedrag_euro_str
            },
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
            except KeyError:        # pragma: no cover
                payment_id = '??'

        return payment_id

    def test_one(self):
        payment_id_1 = self._prep_mollie_websim(421)   # ideal
        payment_id_2 = self._prep_mollie_websim(422)   # creditcard
        payment_id_3 = self._prep_mollie_websim(423)   # paypal
        payment_id_4 = self._prep_mollie_websim(424)   # bancontact
        payment_id_5 = self._prep_mollie_websim(4291)  # banktransfer
        payment_id_6 = self._prep_mollie_websim(49)    # ideal + refund

        f1, f2 = self._do_mollie_refresh(999999)
        self.assertTrue('[ERROR] Kan BetaalInstellingenVereniging voor vereniging 999999 niet vinden' in f1.getvalue())

        BetaalActief(
                ontvanger=self.instellingen,
                payment_id='illegal',
                payment_status='open').save()

        for payment_id in (payment_id_1, payment_id_2, payment_id_3, payment_id_4, payment_id_5, payment_id_6):
            BetaalActief(
                    ontvanger=self.instellingen,
                    payment_id=payment_id,
                    payment_status='open').save()
        # for

        f1, f2 = self._do_mollie_refresh()
        self.assertTrue("Invalid payment ID: 'illegal'." in f1.getvalue())

    def test_bad(self):
        self.instellingen.mollie_api_key = 'other'
        self.instellingen.save(update_fields=['mollie_api_key'])
        f1, f2 = self._do_mollie_refresh()
        self.assertTrue("Invalid API key: 'other'." in f1.getvalue())

        self.instellingen.mollie_api_key = 'test_fixed'
        self.instellingen.save(update_fields=['mollie_api_key'])
        self._prep_mollie_websim(45)    # bijna lege response
        payment_id = 'tr_1234AbcdEFGH'  # fixed id
        BetaalActief(
            ontvanger=self.instellingen,
            payment_id=payment_id,
            payment_status='open').save()
        f1, f2 = self._do_mollie_refresh()
        self.assertTrue("[ERROR] Missing mandatory information in get payment response: None, None" in f1.getvalue())

        self.instellingen.mollie_api_key = 'test_bad'
        self.instellingen.save(update_fields=['mollie_api_key'])
        f1, f2 = self._do_mollie_refresh()
        self.assertTrue("[ERROR] Unexpected exception from Mollie refunds.list" in f1.getvalue())


# end of file
