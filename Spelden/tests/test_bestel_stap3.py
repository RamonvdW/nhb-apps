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


class TestSpeldenBestelStap3(E2EHelpers, TestCase):

    """ tests voor de Spelden applicatie, bestelprocess stap 3 """

    url_begin = '/webwinkel/spelden/'
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
                                discipline='OD',
                                boog='R',
                                score='500',
                                heeft_data_stap2=True,
                                afstanden='70',
                                aantal_pijlen=72,
                                aantal_doelen=48)

    def test_stap3_foutjes(self):
        self.e2e_login(self.account_sporter)

        # GET zonder data van stap2
        self.prep.heeft_data_stap2 = False
        self.prep.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap3)
        self.assert404(resp, 'Onvolledige verzoek (2)')

        # GET zonder SpeldenAanvraagPrep
        self.prep.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap3)
        self.assert404(resp, 'Onvolledige verzoek (1)')

    def test_stap3(self):
        self.e2e_login(self.account_sporter)

        # GET, discipline outdoor
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap3)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap3.dtl', 'design/site_layout.dtl'))

        # GET, discipline veld
        self.prep.discipline = 'VE'
        self.prep.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestel_stap3)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('spelden/bestel_stap3.dtl', 'design/site_layout.dtl'))


# end of file
