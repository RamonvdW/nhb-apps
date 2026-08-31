# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Geo.models import Regio
from Spelden.models import SpeldAanvraagPrep, SpeldVoorwaarden
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestSpeldenBestelStap2(E2EHelpers, TestCase):

    """ tests voor de Spelden applicatie, bestelprocess stap 2 """

    url_begin = '/webwinkel/spelden/'
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

        self.prep = SpeldAanvraagPrep.objects.create(
                                voor_sporter=sporter,
                                wedstrijd_geslacht='M',
                                heeft_data_stap1=True,
                                discipline='IN',
                                boog='R',
                                score='1234')

    def test_stap2_foutjes(self):
        self.e2e_login(self.account_sporter)

        # GET zonder data van stap1
        self.prep.heeft_data_stap1 = False
        self.prep.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap2)
        self.assert404(resp, 'Onvolledige verzoek (2)')

        # GET zonder SpeldenAanvraagPrep
        self.prep.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap2)
        self.assert404(resp, 'Onvolledige verzoek (1)')

    def test_stap2(self):
        self.e2e_login(self.account_sporter)

        # GET, discipline indoor
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap2)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap2.dtl', 'design/site_layout.dtl'))

        # GET, discipline outdoor
        self.prep.discipline = 'OD'
        self.prep.score = 560           # acceptable for 70m
        self.prep.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap2)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap2.dtl', 'design/site_layout.dtl'))

        # POST, discipline outdoor, geen afstand
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap2)
        self.assert404(resp, 'Onbekende afstand')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap2)

        # POST, discipline outdoor
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap2, {'afstand': '70'})
        self.assert_is_redirect(resp, self.url_bestel_stap3)

        # POST, discipline outdoor met onzeker aantal pijlen
        voorwaarde = SpeldVoorwaarden.objects.filter(
                                discipline='OD',
                                afstanden='70',
                                boog_type__afkorting='R',
                                leeftijdsklasse__afkorting='SH').first()
        voorwaarde.aantal_pijlen -= 1
        voorwaarde.save()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap2, {'afstand': '70'})
        self.assert404(resp, 'Kan aantal pijlen niet vaststellen')

        # GET, discipline veld
        self.prep.discipline = 'VE'
        self.prep.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap2)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap2.dtl', 'design/site_layout.dtl'))

        # POST, discipline veld, geen aantal doelen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap2)
        self.assert404(resp, 'Onbekend aantal doelen')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_bestel_stap2, {'doelen': '24'})
        self.assert_is_redirect(resp, self.url_bestel_stap3)

# end of file
