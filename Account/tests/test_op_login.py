# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from Account.operations.login import auto_login_gast_account
from TestHelpers.e2ehelpers import E2EHelpers
from types import SimpleNamespace


class TestAccountOpLogin(E2EHelpers, TestCase):

    """ tests voor de Account applicatie; operations module login """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_gast = self.e2e_create_account('gast', 'gast@test.com', 'Gast')
        self.account_gast.is_gast = True
        self.account_gast.save(update_fields=['is_gast'])

    def test_login_gast(self):
        # niet ingelogd
        request = SimpleNamespace()
        request.META = dict()
        request.user = AnonymousUser()
        request.session = self.client.session

        auto_login_gast_account(request, self.account_gast)


# end of file
