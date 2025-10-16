# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Geo.models import Regio
from Registreer.models import GastLidNummer
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestRegistreerBegin(E2EHelpers, TestCase):

    """ tests voor de Registreer applicatie; begin scherm """

    test_after = ('Account',)

    url_begin = '/account/registreer/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="normaal@test.com",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_normaal)
        sporter.save()

    def test_get(self):
        # anon
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('registreer/begin.dtl', 'design/site_layout.dtl'))

        # ingelogd
        self.e2e_login(self.account_normaal)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assert_is_redirect(resp, '/plein/')

        # kill-switch
        volgende = GastLidNummer.objects.first()
        volgende.kan_aanmelden = False
        volgende.save(update_fields=['kan_aanmaken'])

        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        # TODO: check resp


# end of file
