# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.operations import maak_functie
from NhbStructuur.models import Regio
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.models import WedstrijdLocatie


class TestWedstrijdenManager(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Manager """

    url_wedstrijden_manager = '/wedstrijden/manager/'
    url_wedstrijden_manager_geannuleerd = '/wedstrijden/manager/geannuleerd/'
    url_wedstrijden_vereniging = '/wedstrijden/vereniging/'
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        # geef de vereniging een wedstrijdlocatie
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.ver1)

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

    def test_manager(self):
        # anon mag niet
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_manager)
        self.assert_is_redirect_not_plein(resp)

        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_manager_geannuleerd)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)

        # wissel terug naar BB
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden_manager, post=False)


# end of file
