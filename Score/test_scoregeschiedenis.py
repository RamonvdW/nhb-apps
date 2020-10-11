# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Functie.models import maak_functie
from .models import aanvangsgemiddelde_opslaan
from Schutter.models import SchutterBoog, SchutterVoorkeuren
import datetime


class TestScoreGeschiedenis(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie, module Voorkeuren """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_hwl = self.e2e_create_account('hwl', 'hwl@test.com', 'Secretaris')
        self.e2e_account_accepteert_vhpg(self.account_hwl)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        ver.save()
        self.nhbver1 = ver

        self.functie_hwl = maak_functie('HWL 1000', 'HWL')
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_hwl)

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_normaal
        lid.email = lid.account.email
        lid.save()
        self.nhblid1 = lid

        self.boog_r = BoogType.objects.get(afkorting='R')

        # maak een schutterboog aan
        schutterboog = SchutterBoog(nhblid=lid, boogtype=self.boog_r, voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100001 = schutterboog

        # maak een AG aan
        aanvangsgemiddelde_opslaan(schutterboog, 18, 9.123, None, 'Automatisch vastgesteld')

        aanvangsgemiddelde_opslaan(schutterboog, 25, 9.251, self.account_hwl, 'Automatisch vastgesteld')

        self.url_geschiedenis = '/score/geschiedenis/'

    def test_mag_niet(self):
        # moet BB zijn om de geschiedenis in te mogen zien
        self.client.logout()
        resp = self.client.get(self.url_geschiedenis)
        self.assert_is_redirect(resp, '/plein/')

    def test_bb(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_geschiedenis)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))

    def test_zoek(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        url = self.url_geschiedenis + '?zoekterm=%s' % self.nhblid1.nhb_nr
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, self.nhblid1.volledige_naam())
        self.assertContains(resp, 'Recurve')
        self.assertContains(resp, ' (AG)')
        self.assertContains(resp, 'Automatisch vastgesteld')

    def test_zoek_bad(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        url = self.url_geschiedenis + '?zoekterm=999999'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('score/score-geschiedenis.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Niets gevonden')

        url = self.url_geschiedenis + '?zoekterm=xx'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

# end of file
