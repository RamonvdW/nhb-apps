# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from Account.models import Account, account_zet_sessionvars_na_login
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Plein.test_helpers import assert_html_ok, assert_template_used, \
                               assert_other_http_commands_not_supported
from Functie.rol import Rollen, rol_zet_sessionvars_na_login, rol_get_huidige
from .models import SchutterBoog
from .leeftijdsklassen import leeftijdsklassen_zet_sessionvars_na_login, \
                              get_sessionvars_leeftijdsklassen
import datetime


class TestSchutterVoorkeuren(TestCase):
    """ unit tests voor de Schutter applicatie, module Voorkeuren """

    def setUp(self):
        """ initialisatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')
        self.account_admin = Account.objects.get(username='admin')
        self.account_normaal = Account.objects.get(username='normaal')

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
        lid.save()
        self.nhblid1 = lid
        self.account_normaal.nhblid = lid
        self.account_normaal.save()

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

    def test_view(self):
        # zonder login --> terug naar het plein
        resp = self.client.get('/schutter/voorkeuren/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_template_used(self, resp, ('plein/plein-bezoeker.dtl', 'plein/site_layout.dtl'))

        # met schutter-login wel toegankelijk
        account = self.account_normaal
        self.client.login(username=account.username, password='wachtwoord')
        account_zet_sessionvars_na_login(self.client).save()
        rol_zet_sessionvars_na_login(account, self.client).save()
        leeftijdsklassen_zet_sessionvars_na_login(account, self.client).save()
        self.assertEqual(rol_get_huidige(self.client), Rollen.ROL_SCHUTTER)

        self.assertEqual(len(SchutterBoog.objects.all()), 0)
        resp = self.client.get('/schutter/voorkeuren/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('schutter/voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(SchutterBoog.objects.all()), 5)

        # bij tweede keer de view ophalen zijn alle SchutterBoog records al aangemaakt
        resp = self.client.get('/schutter/voorkeuren/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(len(SchutterBoog.objects.all()), 5)

        obj = SchutterBoog.objects.get(account=self.account_normaal, boogtype=self.boog_R)
        self.assertTrue(obj.heeft_interesse)
        self.assertFalse(obj.voor_wedstrijd)
        self.assertFalse(obj.voorkeur_dutchtarget_18m)

        # maak wat wijzigingen
        resp = self.client.post('/schutter/voorkeuren/', {'schiet_R': 'on', 'info_BB': 'on', 'voorkeur_DT_18m': 'on'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('schutter/voorkeuren-opgeslagen.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(len(SchutterBoog.objects.all()), 5)

        obj = SchutterBoog.objects.get(account=self.account_normaal, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)
        self.assertTrue(obj.voorkeur_dutchtarget_18m)

        # coverage
        self.assertTrue(str(obj) != "")

        # GET met DT=aan
        resp = self.client.get('/schutter/voorkeuren/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # TODO: check DT=aan

        # DT voorkeur uitzetten
        resp = self.client.post('/schutter/voorkeuren/', {'schiet_R': 'on', 'info_BB': 'on'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('schutter/voorkeuren-opgeslagen.dtl', 'plein/site_layout.dtl'))

        obj = SchutterBoog.objects.get(account=self.account_normaal, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)
        self.assertFalse(obj.voorkeur_dutchtarget_18m)

        assert_other_http_commands_not_supported(self, '/schutter/voorkeuren/', post=False)


# end of file
