# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers

# tests van de SAML2 Identity Provider voor single sign-on ondersteuning

if settings.ENABLE_WIKI:

    class TestSingleSignOn(E2EHelpers, TestCase):

        """ tests voor de het SSO deel van de Beheer applicatie """

        def test_saml2idp(self):
            resp = self.client.get('/idp/metadata/')
            self.assertEqual(resp.status_code, 200)     # 200=OK
            self.assertContains(resp, "NHB IT applications SAML2 Identity Provider")

            # no code yet to simulate a true SAML2 request
            # the line below causes a binascii.Error exception in djangosaml2idp :-(

            #resp = self.client.get('/idp/sso/redirect?SAMLRequest=garbage&RelayState=https://whatever/', follow=True)
            #self.e2e_dump_resp(resp)

            resp = self.client.get('/idp/sso/redirect?SAMLRequest')
            self.assertEqual(resp.status_code, 301)

            resp = self.client.get('/idp/sso/login?SAMLRequest')
            self.assertEqual(resp.status_code, 301)


# capture request (partial):
# https://test.handboogsport.nl/idp/sso/redirect?
#    SAMLRequest=pVLL<ulr-encoded-string>el%2F1%2Fq%2Bh8%3D
#    &RelayState=https%3A%2F%2Fwiki.handboogsport.st-visir.nl%2Fmediawiki%2Findex.php%2FSpeciaal%3APluggableAuthLogin

# end of file
