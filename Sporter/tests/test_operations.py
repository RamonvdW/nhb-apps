# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.operations import maak_functie
from NhbStructuur.models import NhbVereniging, NhbRegio, NhbRayon
from Sporter.models import Sporter
from Sporter.operations import get_request_regio_nr, get_request_rayon_nr
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestSporterOperations(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Operations """

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal', accepteer_vhpg=True)

        self.regio100 = NhbRegio.objects.get(regio_nr=100)
        self.regio111 = NhbRegio.objects.get(regio_nr=111)
        self.rayon2 = NhbRayon.objects.get(rayon_nr=2)

        # maak een test vereniging
        ver = NhbVereniging(
                    naam="Grote Club",
                    ver_nr="1000",
                    regio=NhbRegio.objects.get(pk=111))
        ver.save()
        self.ver = ver

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Piet",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_normaal,
                    email=self.account_normaal.email)
        sporter.save()
        self.sporter = sporter

        # functies
        self.functie_hwl1000 = maak_functie('HWL ver 1000', 'HWL')
        self.functie_hwl1000.nhb_ver = ver
        self.functie_hwl1000.save(update_fields=['nhb_ver'])

        self.functie_rcl111 = maak_functie('RCL regio 111', 'RCL')
        self.functie_rcl111.nhb_regio = self.regio111
        self.functie_rcl111.save(update_fields=['nhb_regio'])

        self.functie_rko2 = maak_functie('RKO rayon 2', 'RKO')
        self.functie_rko2.nhb_rayon = self.rayon2
        self.functie_rko2.save(update_fields=['nhb_rayon'])

        self.functie_anders = maak_functie('Anders', 'MWW')

        self.functie_hwl1000.accounts.add(self.account_normaal)
        self.functie_rcl111.accounts.add(self.account_normaal)
        self.functie_rko2.accounts.add(self.account_normaal)
        self.functie_anders.accounts.add(self.account_normaal)

    def test_regio_nr(self):

        # bezoeker
        self.client.logout()
        resp = self.client.get('/plein/')
        request = resp.wsgi_request

        # bezoeker krijgt default --> regio 101
        self.assertEqual(101, get_request_regio_nr(request))

        # log in als sporter (moet actief lid zijn)
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request

        # maak niet actief lid
        self.sporter.is_actief_lid = False
        self.sporter.save(update_fields=['is_actief_lid'])

        # niet actief lid --> behandel als bezoeker
        self.assertEqual(101, get_request_regio_nr(request))

        # maak weer actief lid
        self.sporter.is_actief_lid = True
        self.sporter.save(update_fields=['is_actief_lid'])

        # sporter in regio 111
        self.assertEqual(111, get_request_regio_nr(request))

        # wissel naar administratieve regio 100
        self.ver.regio = self.regio100
        self.ver.save(update_fields=['regio'])

        self.assertEqual(100, get_request_regio_nr(request))
        self.assertEqual(101, get_request_regio_nr(request, allow_admin_regio=False))

        self.ver.regio = self.regio111
        self.ver.save(update_fields=['regio'])

        # log in als beheerder
        self.e2e_login_and_pass_otp(self.account_normaal)

        # RKO krijgt de eerste regio in zijn rayon
        self.e2e_wissel_naar_functie(self.functie_rko2)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(105, get_request_regio_nr(request))

        # RCL krijgt zijn eigen regio nummer
        self.e2e_wissel_naar_functie(self.functie_rcl111)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(111, get_request_regio_nr(request))

        # andere functies worden behandeld als bezoeker
        self.e2e_wissel_naar_functie(self.functie_anders)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(101, get_request_regio_nr(request))

        # HWL krijgt de regio van zijn vereniging
        self.e2e_wissel_naar_functie(self.functie_hwl1000)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(111, get_request_regio_nr(request))

    def test_rayon_nr(self):
        # bezoeker
        self.client.logout()
        resp = self.client.get('/plein/')
        request = resp.wsgi_request

        # bezoeker krijgt default --> rayon 1
        self.assertEqual(1, get_request_rayon_nr(request))

        # log in als sporter (moet actief lid zijn)
        self.e2e_login(self.account_normaal)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request

        # maak niet actief lid
        self.sporter.is_actief_lid = False
        self.sporter.save(update_fields=['is_actief_lid'])

        # niet actief lid --> behandel als bezoeker
        self.assertEqual(1, get_request_rayon_nr(request))

        # maak weer actief lid
        self.sporter.is_actief_lid = True
        self.sporter.save(update_fields=['is_actief_lid'])

        # sporter in regio 111 --> rayon 3, maar niet actief lid dus behandel als bezoeker
        self.assertEqual(3, get_request_rayon_nr(request))

        # log in als beheerder
        self.e2e_login_and_pass_otp(self.account_normaal)

        # RKO krijgt zijn eigen rayon nummer
        self.e2e_wissel_naar_functie(self.functie_rko2)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(2, get_request_rayon_nr(request))

        # RCL krijgt het rayon van zijn regio
        self.e2e_wissel_naar_functie(self.functie_rcl111)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(3, get_request_rayon_nr(request))

        # andere functies worden behandeld als bezoeker
        self.e2e_wissel_naar_functie(self.functie_anders)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(1, get_request_rayon_nr(request))

        # HWL krijgt het rayon van de regio van zijn vereniging
        self.e2e_wissel_naar_functie(self.functie_hwl1000)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertEqual(3, get_request_rayon_nr(request))

# end of file
