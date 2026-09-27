# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Geo.models import Regio
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestSpeldenBestelStap1(E2EHelpers, TestCase):

    """ tests voor de Spelden applicatie, bestelprocess stap 1 """

    url_begin = '/webwinkel/spelden/'
    url_bestel_stap1 = '/webwinkel/spelden/bestel/stap1/'
    url_bestel_stap2 = '/webwinkel/spelden/bestel/stap2/'
    url_bestel_stap3 = '/webwinkel/spelden/bestel/stap3/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()

        # maak een vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        # maak de sporter aan
        self.account_sporter = self.e2e_create_account('100001', 'normaal@test.com', 'Normaal')
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_sporter,
                    email=self.account_sporter.email)
        sporter.save()
        self.sporter_100001 = sporter

        boog_bb = BoogType.objects.get(afkorting='BB')

        self.sporterboog = SporterBoog.objects.create(sporter=sporter, boogtype=boog_bb, voor_wedstrijd=True)

        self.voorkeuren = SporterVoorkeuren.objects.create(sporter=sporter, wedstrijd_geslacht_gekozen=False)

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_bestel_stap1)
        self.assert403(resp, 'Niet ingelogd')

        resp = self.client.get(self.url_bestel_stap2)
        self.assert403(resp, 'Niet ingelogd')

        resp = self.client.get(self.url_bestel_stap3)
        self.assert403(resp, 'Niet ingelogd')

    def test_stap1(self):
        self.e2e_login(self.account_sporter)

        # GET zonder SpeldenAanvraagPrep
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap1)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))

        # GET zonder bogen
        self.sporterboog.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap1)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))

        # POST, geen wedstrijdgeslacht, geen discipline
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap1)
        self.assert404(resp, 'Onbekende discipline')

        self.voorkeuren.wedstrijd_geslacht_gekozen = True
        self.voorkeuren.wedstrijd_geslacht = 'M'
        self.voorkeuren.save()

        # POST, discipline, geen boogtype
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN'})        # Indoor
        self.assert404(resp, 'Onbekende boog')

        # POST, discipline, boogtype, geen score
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                            'boogtype': 'BB'})          # Barebow
        self.assert404(resp, 'Slechte score')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                            'boogtype': 'BB',           # Barebow
                                                            'score': '1234'})
        self.assert_is_redirect(resp, self.url_bestel_stap2)

        # foute score
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                            'boogtype': 'BB',           # Barebow
                                                            'score': '0'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))

        # GET met SpeldenAanvraagPrep
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap1)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))


# end of file
