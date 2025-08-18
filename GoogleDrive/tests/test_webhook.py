# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from GoogleDrive.models import Transactie, Token, maak_unieke_code
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch


class TestGoogleDriveWebHook(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, module views_webhook """

    url_webhook = '/google/webhook/oauth/'
    url_resultaat_mislukt = '/google/resultaat-mislukt/'
    url_resultaat_gelukt = '/google/resultaat-gelukt/'

    def test_webhook(self):
        # no state
        resp = self.client.get(self.url_webhook)
        self.assert404(resp, 'Onvolledig verzoek')

        # state, no code/error
        resp = self.client.get(self.url_webhook + '?state=1234')
        self.assert404(resp, 'Onvolledig verzoek')

        # state + code, no Transaction
        resp = self.client.get(self.url_webhook + '?state=1234&code=1234')
        self.assert404(resp, 'Onbekend verzoek')

        # maak een transactie aan, zodat we door de filtering in webhook komen
        transactie = Transactie.objects.create(unieke_code='1234')
        self.assertTrue(str(transactie) != '')

        # error handling
        with patch('GoogleDrive.views_webhook.handle_authentication_response', return_value=None):
            resp = self.client.get(self.url_webhook + '?state=1234&error=jammer')
            self.assert_is_redirect(resp, self.url_resultaat_mislukt)

        transactie.has_been_used=False
        transactie.save(update_fields=['has_been_used'])

        token = Token.objects.create(creds='{"test": "nja"}', has_failed=False)
        self.assertTrue(str(token) != '')

        with patch('GoogleDrive.views_webhook.handle_authentication_response', return_value=token):
            resp = self.client.get(self.url_webhook + '?state=1234&code=1234')
            self.assert_is_redirect(resp, self.url_resultaat_gelukt)

        self.assertEqual(len(maak_unieke_code(test="hallo")), 32)

# end of file
