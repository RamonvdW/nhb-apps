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
from .models import SchutterBoog, SchutterVoorkeuren
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
        self.assertEqual(SchutterVoorkeuren.objects.count(), 0)
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

        # maak wat wijzigingen
        resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on',
                                                      'info_BB': 'on',
                                                      'voorkeur_dt': 'on'})
        self.assert_is_redirect(resp, '/schutter/')     # naar profiel
        self.assertEqual(SchutterBoog.objects.count(), 5)
        self.assertEqual(SchutterVoorkeuren.objects.count(), 1)

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertTrue(voorkeuren.voorkeur_dutchtarget_18m)
        self.assertFalse(voorkeuren.voorkeur_meedoen_competitie)
        self.assertEqual(voorkeuren.nhblid, self.nhblid1)

        # coverage
        self.assertTrue(str(obj) != "")
        self.assertTrue(str(voorkeuren) != "")

        # GET met DT=aan
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # check DT=aan
        checked, unchecked = self.extract_checkboxes(resp)
        self.assertTrue("voorkeur_dt" in checked)
        self.assertTrue("voorkeur_meedoen_competitie" in unchecked)

        # DT voorkeur uitzetten
        resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on', 'info_BB': 'on'})
        self.assert_is_redirect(resp, '/schutter/')     # naar profiel

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertFalse(voorkeuren.voorkeur_dutchtarget_18m)

        # voorkeur competitie weer aan zetten
        resp = self.client.post(self.url_voorkeuren, {'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, '/schutter/')     # naar profiel

        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertTrue(voorkeuren.voorkeur_meedoen_competitie)

        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        checked, unchecked = self.extract_checkboxes(resp)
        self.assertTrue("voorkeur_meedoen_competitie" in checked)

        # does een post zonder wijzigingen (voor de coverage)
        resp = self.client.post(self.url_voorkeuren, {'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, '/schutter/')     # naar profiel

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

    def test_geen_wedstrijden(self):
        # self.account_normaal is lid bij self.nhbver1
        # zet deze in de administratieve regio
        self.nhbver1.geen_wedstrijden = True
        self.nhbver1.save()

        self.e2e_login(self.account_normaal)

        # mag geen bogen instellen
        # helemaal geen voorkeuren, om precies te zijn
        resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

# end of file
