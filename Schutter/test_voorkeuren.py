# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Functie.models import maak_functie
from Score.operations import score_indiv_ag_opslaan
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
        ver.ver_nr = "1000"
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
        ver.ver_nr = "1001"
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
        lid.account = self.account_hwl
        lid.save()

        self.boog_R = BoogType.objects.get(afkorting='R')

        self.url_voorkeuren = '/sporter/voorkeuren/'
        self.url_wijzig = '/account/nieuw-wachtwoord/'

    def test_view(self):
        # zonder login --> terug naar het plein
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren, follow=True)
        self.assert403(resp)

        # met schutter-login wel toegankelijk
        self.e2e_login(self.account_normaal)

        # initieel zijn er geen voorkeuren opgeslagen
        self.assertEqual(SchutterBoog.objects.count(), 0)
        self.assertEqual(SchutterVoorkeuren.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/voorkeuren.dtl', 'plein/site_layout.dtl'))

        # na bekijken voorkeuren zijn ze aangemaakt
        self.assertEqual(SchutterBoog.objects.count(), 5)

        # controleer dat ze niet nog een keer aangemaakt worden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(SchutterBoog.objects.count(), 5)

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertTrue(obj.heeft_interesse)
        self.assertFalse(obj.voor_wedstrijd)

        # maak wat wijzigingen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on',
                                                          'info_BB': 'on',
                                                          'voorkeur_eigen_blazoen': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel
        self.assertEqual(SchutterBoog.objects.count(), 5)
        self.assertEqual(SchutterVoorkeuren.objects.count(), 1)

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertTrue(voorkeuren.voorkeur_eigen_blazoen)
        self.assertFalse(voorkeuren.voorkeur_meedoen_competitie)
        self.assertEqual(voorkeuren.nhblid, self.nhblid1)

        # coverage
        self.assertTrue(str(obj) != "")
        self.assertTrue(str(voorkeuren) != "")

        # GET met DT=aan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # check DT=aan
        checked, unchecked = self.extract_checkboxes(resp)
        self.assertTrue("voorkeur_eigen_blazoen" in checked)
        self.assertTrue("voorkeur_meedoen_competitie" in unchecked)

        # DT voorkeur uitzetten
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on', 'info_BB': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        obj = SchutterBoog.objects.get(nhblid=self.nhblid1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertFalse(voorkeuren.voorkeur_eigen_blazoen)

        # voorkeur competitie weer aan zetten
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertTrue(voorkeuren.voorkeur_meedoen_competitie)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        checked, unchecked = self.extract_checkboxes(resp)
        self.assertTrue("voorkeur_meedoen_competitie" in checked)

        # does een post zonder wijzigingen (voor de coverage)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        self.e2e_assert_other_http_commands_not_supported(self.url_voorkeuren, post=False)

    def test_hwl(self):
        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SchutterBoog records aan
        with self.assert_max_queries(20):
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
        with self.assert_max_queries(20):
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
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assert404(resp)     # 404 = Not allowed

        # haal als HWL de voorkeuren pagina op met een niet-numeriek nhblid_pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + 'snuiter/')
        self.assert404(resp)     # 404 = Not allowed

        # haal als HWL de voorkeuren pagina op met een niet bestaand nhblid_pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + '999999/')
        self.assert404(resp)     # 404 = Not allowed

        # haal als HWL de voorkeuren pagina op van een lid van een andere vereniging
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + '100002/')
        self.assert403(resp)

    def test_geen_wedstrijden(self):
        # self.account_normaal is lid bij self.nhbver1
        # zet deze in de administratieve regio
        self.nhbver1.geen_wedstrijden = True
        self.nhbver1.save()

        self.e2e_login(self.account_normaal)

        # mag geen bogen instellen
        # helemaal geen voorkeuren, om precies te zijn
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(0, SchutterBoog.objects.filter(nhblid=self.nhblid1).count())

    def test_wijzig_wachtwoord(self):
        # zelfde test als in Account.test_wachtwoord
        # maar ivm nhblid koppeling wordt 'Sporter' menu gekozen

        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))

        nieuw_ww = 'GratisNieuwGheim'

        # foutief huidige wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'huidige': nieuw_ww, 'nieuwe': nieuw_ww})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Huidige wachtwoord komt niet overeen')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'nieuwe': '123412341234'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/nieuw-wachtwoord.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wachtwoord bevat te veel gelijke tekens')

        # wijzig het wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'huidige': self.WACHTWOORD, 'nieuwe': nieuw_ww})
        self.assert_is_redirect(resp, '/plein/')

        # controleer dat het nieuwe wachtwoord gebruikt kan worden
        self.client.logout()
        self.e2e_login(self.account_hwl, wachtwoord=nieuw_ww)

    def test_discipline(self):
        # met schutter-login wel toegankelijk
        self.e2e_login(self.account_normaal)

        # voorkeuren worden aangemaakt bij ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # check the initiële voorkeuren: alle disciplines actief
        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertTrue(voorkeuren.voorkeur_discipline_25m1pijl)
        self.assertTrue(voorkeuren.voorkeur_discipline_outdoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_indoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_clout)
        self.assertTrue(voorkeuren.voorkeur_discipline_veld)
        self.assertTrue(voorkeuren.voorkeur_discipline_run)
        self.assertTrue(voorkeuren.voorkeur_discipline_3d)

        # alle disciplines 'uit' zetten
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel
        voorkeuren = SchutterVoorkeuren.objects.get(pk=voorkeuren.pk)
        self.assertFalse(voorkeuren.voorkeur_discipline_25m1pijl)
        self.assertFalse(voorkeuren.voorkeur_discipline_outdoor)
        self.assertFalse(voorkeuren.voorkeur_discipline_indoor)
        self.assertFalse(voorkeuren.voorkeur_discipline_clout)
        self.assertFalse(voorkeuren.voorkeur_discipline_veld)
        self.assertFalse(voorkeuren.voorkeur_discipline_run)
        self.assertFalse(voorkeuren.voorkeur_discipline_3d)

        # alle disciplines 'aan'
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'voorkeur_disc_25m1p': '1',
                                                          'voorkeur_disc_outdoor': '2',
                                                          'voorkeur_disc_indoor': 'ja',
                                                          'voorkeur_disc_clout': '?',
                                                          'voorkeur_disc_veld': 'x',
                                                          'voorkeur_disc_run': 'on',
                                                          'voorkeur_disc_3d': 'whatever'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel
        voorkeuren = SchutterVoorkeuren.objects.get(pk=voorkeuren.pk)
        self.assertTrue(voorkeuren.voorkeur_discipline_25m1pijl)
        self.assertTrue(voorkeuren.voorkeur_discipline_outdoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_indoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_clout)
        self.assertTrue(voorkeuren.voorkeur_discipline_veld)
        self.assertTrue(voorkeuren.voorkeur_discipline_run)
        self.assertTrue(voorkeuren.voorkeur_discipline_3d)

    def test_para_opmerking(self):
        # met schutter-login wel toegankelijk
        self.e2e_login(self.account_normaal)

        # voorkeuren worden aangemaakt bij ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # niet-para sporter mag geen opmerking invoeren
        voorkeuren = SchutterVoorkeuren.objects.all()[0]
        self.assertEqual(voorkeuren.opmerking_para_sporter, '')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SchutterVoorkeuren.objects.get(pk=voorkeuren.pk)
        self.assertEqual(voorkeuren.opmerking_para_sporter, '')

        # maak dit een para sporter
        self.nhblid1.para_classificatie = 'VI1'
        self.nhblid1.save()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SchutterVoorkeuren.objects.get(pk=voorkeuren.pk)
        self.assertEqual(voorkeuren.opmerking_para_sporter, 'Hallo test')

        # coverage: opslaan zonder wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

    def test_email_optout(self):
        # log in als beheerder, maar blijf sporter
        self.e2e_login(self.account_hwl)
        self.e2e_wisselnaarrol_sporter()

        # voorkeuren worden aangemaakt bij ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # check de defaults
        email = self.account_hwl.accountemail_set.all()[0]
        self.assertFalse(email.optout_nieuwe_taak)
        self.assertFalse(email.optout_herinnering_taken)

        # wijzig zonder opt-out te doen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        email = self.account_hwl.accountemail_set.all()[0]
        self.assertFalse(email.optout_nieuwe_taak)
        self.assertFalse(email.optout_herinnering_taken)

        # wijzig met opt-out
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'optout_nieuwe_taak': 'ja'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        email = self.account_hwl.accountemail_set.all()[0]
        self.assertTrue(email.optout_nieuwe_taak)
        self.assertFalse(email.optout_herinnering_taken)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'optout_herinnering_taken': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        email = self.account_hwl.accountemail_set.all()[0]
        self.assertFalse(email.optout_nieuwe_taak)
        self.assertTrue(email.optout_herinnering_taken)

# end of file
