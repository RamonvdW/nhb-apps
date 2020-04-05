# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
from Functie.rol import Rollen, rol_zet_sessionvars_na_login, rol_get_huidige
from .models import SchutterBoog
from .leeftijdsklassen import leeftijdsklassen_plugin_na_login
import datetime


class TestSchutterVoorkeuren(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie, module Voorkeuren """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_normaal
        lid.save()
        self.nhblid1 = lid

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        self.boog_R = BoogType.objects.get(afkorting='R')

        self.url_voorkeuren = '/schutter/voorkeuren/'

    def test_view(self):
        # zonder login --> terug naar het plein
        resp = self.client.get(self.url_voorkeuren, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        # met schutter-login wel toegankelijk
        self.e2e_login(self.account_normaal)

        # initieel zijn er geen voorkeuren opgeslagen
        self.assertEqual(len(SchutterBoog.objects.all()), 0)
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/voorkeuren.dtl', 'plein/site_layout.dtl'))

        # na bekijken voorkeuren zijn ze aangemaakt
        self.assertEqual(len(SchutterBoog.objects.all()), 5)

        # controleer dat ze niet nog een keer aangemaakt worden
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(len(SchutterBoog.objects.all()), 5)

        obj = SchutterBoog.objects.get(account=self.account_normaal, boogtype=self.boog_R)
        self.assertTrue(obj.heeft_interesse)
        self.assertFalse(obj.voor_wedstrijd)
        self.assertFalse(obj.voorkeur_dutchtarget_18m)

        # maak wat wijzigingen
        resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on', 'info_BB': 'on', 'voorkeur_DT_18m': 'on'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/voorkeuren-opgeslagen.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(SchutterBoog.objects.all()), 5)

        obj = SchutterBoog.objects.get(account=self.account_normaal, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)
        self.assertTrue(obj.voorkeur_dutchtarget_18m)

        # coverage
        self.assertTrue(str(obj) != "")

        # GET met DT=aan
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # TODO: check DT=aan

        # DT voorkeur uitzetten
        resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on', 'info_BB': 'on'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/voorkeuren-opgeslagen.dtl', 'plein/site_layout.dtl'))

        obj = SchutterBoog.objects.get(account=self.account_normaal, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)
        self.assertFalse(obj.voorkeur_dutchtarget_18m)

        self.e2e_assert_other_http_commands_not_supported(self.url_voorkeuren, post=False)


# end of file
