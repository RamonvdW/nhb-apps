# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Functie.models import maak_functie
from Score.models import aanvangsgemiddelde_opslaan
from .models import SchutterBoog
import datetime


class TestSchutterVoorkeuren(E2EHelpers, TestCase):
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
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()

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

        # maak nog een test vereniging
        ver = NhbVereniging()
        ver.naam = "Nieuwe Club"
        ver.nhb_nr = "1001"
        ver.regio = NhbRegio.objects.get(pk=112)
        ver.save()

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
        self.assertEqual(SchutterBoog.objects.count(), 0)
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/voorkeuren.dtl', 'plein/site_layout.dtl'))

        # na bekijken voorkeuren zijn ze aangemaakt
        self.assertEqual(SchutterBoog.objects.count(), 5)

        # controleer dat ze niet nog een keer aangemaakt worden
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(SchutterBoog.objects.count(), 5)

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertTrue(obj.heeft_interesse)
        self.assertFalse(obj.voor_wedstrijd)
        self.assertFalse(obj.voorkeur_dutchtarget_18m)

        # maak wat wijzigingen
        resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on', 'info_BB': 'on', 'voorkeur_DT_18m': 'on'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/voorkeuren-opgeslagen.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(SchutterBoog.objects.count(), 5)

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)
        self.assertTrue(obj.voorkeur_dutchtarget_18m)

        # coverage
        self.assertTrue(str(obj) != "")

        # GET met DT=aan
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # check DT=aan
        checked, unchecked = self.extract_checkboxes(resp)
        self.assertTrue("voorkeur_DT_18m" in checked)

        # DT voorkeur uitzetten
        resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on', 'info_BB': 'on'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/voorkeuren-opgeslagen.dtl', 'plein/site_layout.dtl'))

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)
        self.assertFalse(obj.voorkeur_dutchtarget_18m)

        # zet aanvangsgemiddelden voor 18m en 25m
        datum = datetime.date(year=2020, month=5, day=2)
        datum_str = "2 mei 2020"
        aanvangsgemiddelde_opslaan(obj, 18, 9.018, datum, None, 'Test opmerking A')
        aanvangsgemiddelde_opslaan(obj, 25, 2.5, datum, None, 'Test opmerking B')

        resp = self.client.get(self.url_voorkeuren)
        self.assertContains(resp, "2,500")
        self.assertContains(resp, "9,018")
        self.assertContains(resp, "Test opmerking A")
        self.assertContains(resp, "Test opmerking B")
        self.assertContains(resp, datum_str)

        self.e2e_assert_other_http_commands_not_supported(self.url_voorkeuren, post=False)

    def test_hwl(self):
        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SchutterBoog records aan
        resp = self.client.get(self.url_voorkeuren + '100001/')
        self.assertEqual(resp.status_code, 200)

        # controleer de stand van zaken voordat de HWL iets wijzigt
        obj_r = SchutterBoog.objects.get(nhblid__pk=100001, boogtype__afkorting='R')
        obj_c = SchutterBoog.objects.get(nhblid__pk=100001, boogtype__afkorting='C')
        self.assertFalse(obj_r.voor_wedstrijd)
        self.assertFalse(obj_c.voor_wedstrijd)
        self.assertTrue(obj_r.heeft_interesse)
        self.assertTrue(obj_c.heeft_interesse)

        # post een wijziging
        resp = self.client.post(self.url_voorkeuren, {'nhblid_pk': '100001', 'schiet_R': 'on', 'info_C': 'on'})
        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

        # controleer dat de post werkte
        obj_r = SchutterBoog.objects.get(nhblid__pk=100001, boogtype__afkorting='R')
        obj_c = SchutterBoog.objects.get(nhblid__pk=100001, boogtype__afkorting='C')
        self.assertTrue(obj_r.voor_wedstrijd)
        self.assertFalse(obj_c.voor_wedstrijd)
        self.assertFalse(obj_r.heeft_interesse)
        self.assertTrue(obj_c.heeft_interesse)

    def test_hwl_bad(self):
        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal als HWL 'de' voorkeuren pagina op, zonder specifiek nhblid_pk
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # haal als HWL de voorkeuren pagina op met een niet-numeriek nhblid_pk
        resp = self.client.get(self.url_voorkeuren + 'snuiter/')
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # haal als HWL de voorkeuren pagina op met een niet bestaand nhblid_pk
        resp = self.client.get(self.url_voorkeuren + '999999/')
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

        # haal als HWL de voorkeuren pagina op van een lid van een andere vereniging
        resp = self.client.get(self.url_voorkeuren + '100002/')
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

# end of file
