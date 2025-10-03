# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from GoogleDrive.models import Transactie, Token
from GoogleDrive.operations import check_heeft_toestemming, get_authorization_url, handle_authentication_response
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch


class TestGoogleDriveAuthenticatie(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, module authenticatie """

    def test_get(self):
        Token.objects.all().delete()
        self.assertFalse(check_heeft_toestemming())

        Token.objects.create(creds='{"test": "nja"}', has_failed=False)
        self.assertTrue(check_heeft_toestemming())

        self.assertEqual(Transactie.objects.count(), 0)
        url = get_authorization_url('test_user', 'mr.test@test.not')
        self.assertEqual(Transactie.objects.count(), 1)

        self.assertTrue(url.startswith('https://accounts.google.com/o/oauth2/auth?response_type=code&client_id='))

    def test_response(self):
        # TODO: deze test is afhankelijk van een credentials bestand dat in /tmp moet staan
        url = 'x'
        token = handle_authentication_response(url)
        self.assertIsNone(token)

        # url = '/webhook/?code=1234'
        # token = handle_authentication_response(url)     # dit doet een echte transactie over het internet :(
        # self.assertIsNone(token)


# end of file
