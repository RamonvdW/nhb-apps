# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRegio, NhbVereniging
from Functie.models import maak_functie
from .models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestSporterVoorkeuren(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Voorkeuren """

    url_voorkeuren = '/sporter/voorkeuren/'
    url_wijzig = '/account/nieuw-wachtwoord/'
    url_profiel = '/sporter/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_hwl = self.e2e_create_account('hwl', 'hwl@test.com', 'Secretaris')
        self.e2e_account_accepteert_vhpg(self.account_hwl)
        self.account_100003 = self.e2e_create_account('100003', 'sporterx@test.com', 'Geslacht X')

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
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_normaal
        sporter.email = sporter.account.email
        sporter.save()
        self.sporter1 = sporter

        # maak nog een test vereniging
        ver = NhbVereniging()
        ver.naam = "Nieuwe Club"
        ver.ver_nr = "1001"
        ver.regio = NhbRegio.objects.get(pk=112)
        ver.save()

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100002 = sporter

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "X"
        sporter.voornaam = "RamonX"
        sporter.achternaam = "de Xester"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_100003
        sporter.save()
        self.sporter_100003 = sporter

        self.boog_R = BoogType.objects.get(afkorting='R')

    def test_view(self):
        # zonder login
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assert403(resp)

        # met sporter-login wel toegankelijk
        self.e2e_login(self.account_normaal)

        # initieel zijn er geen voorkeuren opgeslagen
        self.assertEqual(SporterBoog.objects.count(), 0)
        self.assertEqual(SporterVoorkeuren.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/voorkeuren.dtl', 'plein/site_layout.dtl'))

        # na bekijken voorkeuren zijn ze aangemaakt
        self.assertEqual(SporterBoog.objects.count(), 17)

        # controleer dat ze niet nog een keer aangemaakt worden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(SporterBoog.objects.count(), 17)

        obj = SporterBoog.objects.get(sporter=self.sporter1, boogtype=self.boog_R)
        self.assertTrue(obj.heeft_interesse)
        self.assertFalse(obj.voor_wedstrijd)

        # maak wat wijzigingen
        with self.assert_max_queries(23):
            resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on',
                                                          'info_BB': 'on',
                                                          'voorkeur_eigen_blazoen': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel
        self.assertEqual(SporterBoog.objects.count(), 17)
        self.assertEqual(SporterVoorkeuren.objects.count(), 1)

        obj = SporterBoog.objects.get(sporter=self.sporter1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SporterVoorkeuren.objects.all()[0]
        self.assertTrue(voorkeuren.voorkeur_eigen_blazoen)
        self.assertFalse(voorkeuren.voorkeur_meedoen_competitie)
        self.assertEqual(voorkeuren.sporter, self.sporter1)

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

        obj = SporterBoog.objects.get(sporter=self.sporter1, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SporterVoorkeuren.objects.all()[0]
        self.assertFalse(voorkeuren.voorkeur_eigen_blazoen)

        # voorkeur competitie weer aan zetten
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SporterVoorkeuren.objects.all()[0]
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
        # dit maakt ook de SporterBoog records aan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + '100001/')
        self.assertEqual(resp.status_code, 200)

        # controleer de stand van zaken voordat de HWL iets wijzigt
        obj_r = SporterBoog.objects.get(sporter__lid_nr=100001, boogtype__afkorting='R')
        obj_c = SporterBoog.objects.get(sporter__lid_nr=100001, boogtype__afkorting='C')
        self.assertFalse(obj_r.voor_wedstrijd)
        self.assertFalse(obj_c.voor_wedstrijd)
        self.assertTrue(obj_r.heeft_interesse)
        self.assertTrue(obj_c.heeft_interesse)

        # post een wijziging
        with self.assert_max_queries(24):
            resp = self.client.post(self.url_voorkeuren, {'sporter_pk': '100001', 'schiet_R': 'on', 'info_C': 'on'})
        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

        # controleer dat de post werkte
        obj_r = SporterBoog.objects.get(sporter__lid_nr=100001, boogtype__afkorting='R')
        obj_c = SporterBoog.objects.get(sporter__lid_nr=100001, boogtype__afkorting='C')
        self.assertTrue(obj_r.voor_wedstrijd)
        self.assertFalse(obj_c.voor_wedstrijd)
        self.assertFalse(obj_r.heeft_interesse)
        self.assertTrue(obj_c.heeft_interesse)

    def test_hwl_bad(self):
        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal als HWL 'de' voorkeuren pagina op, zonder specifiek sporter_pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assert404(resp, 'Sporter niet gevonden')

        # haal als HWL de voorkeuren pagina op met een niet-numeriek sporter_pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + 'snuiter/')
        self.assert404(resp, 'Sporter niet gevonden')

        # haal als HWL de voorkeuren pagina op met een niet bestaand sporter_pk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + '999999/')
        self.assert404(resp, 'Sporter niet gevonden')

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
        self.assertEqual(0, SporterBoog.objects.filter(sporter=self.sporter1).count())

    def test_wijzig_wachtwoord(self):
        # zelfde test als in Account.test_wachtwoord
        # maar ivm sporter koppeling wordt 'Sporter' menu gekozen

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
        voorkeuren = SporterVoorkeuren.objects.all()[0]
        self.assertTrue(voorkeuren.voorkeur_discipline_25m1pijl)
        self.assertTrue(voorkeuren.voorkeur_discipline_outdoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_indoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_clout)
        self.assertTrue(voorkeuren.voorkeur_discipline_veld)
        self.assertTrue(voorkeuren.voorkeur_discipline_run)
        self.assertTrue(voorkeuren.voorkeur_discipline_3d)

        # alle disciplines 'uit' zetten
        with self.assert_max_queries(24):
            resp = self.client.post(self.url_voorkeuren, {})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel
        voorkeuren = SporterVoorkeuren.objects.get(pk=voorkeuren.pk)
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
        voorkeuren = SporterVoorkeuren.objects.get(pk=voorkeuren.pk)
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
        voorkeuren = SporterVoorkeuren.objects.all()[0]
        self.assertEqual(voorkeuren.opmerking_para_sporter, '')

        with self.assert_max_queries(24):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SporterVoorkeuren.objects.get(pk=voorkeuren.pk)
        self.assertEqual(voorkeuren.opmerking_para_sporter, '')

        # maak dit een para sporter
        self.sporter1.para_classificatie = 'VI1'
        self.sporter1.save()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SporterVoorkeuren.objects.get(pk=voorkeuren.pk)
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
        with self.assert_max_queries(25):
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

    def test_geslacht_anders(self):

        # begin met de sporter met geslacht man
        self.e2e_login(self.account_hwl)

        # voorkeuren worden aangemaakt bij ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # controleer de voorkeuren
        voorkeur = self.sporter_100002.sportervoorkeuren_set.all()[0]
        self.assertTrue(voorkeur.wedstrijd_geslacht_gekozen)
        self.assertEqual(self.sporter_100002.geslacht, voorkeur.wedstrijd_geslacht)

        # door een post zonder parameters worden alle bogen uitgezet
        # doe dit eenmalig zodat we de database accesses maar gehad hebben
        resp = self.client.post(self.url_voorkeuren)
        self.assert_is_redirect(resp, self.url_profiel)

        # probeer het wedstrijdgeslacht aan te passen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'wedstrijd_mv': 'V'})
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100002.sportervoorkeuren_set.all()[0]
        self.assertTrue(voorkeur.wedstrijd_geslacht_gekozen)
        self.assertEqual(self.sporter_100002.geslacht, voorkeur.wedstrijd_geslacht)


        # wissel naar de sporter met geslacht anders

        self.client.logout()
        self.e2e_login(self.account_100003)

        self.assertEqual(self.sporter_100003.geslacht, 'X')

        # voorkeuren worden aangemaakt bij ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # door een post zonder parameters worden alle bogen uitgezet
        # doe dit eenmalig zodat we de database accesses maar gehad hebben
        resp = self.client.post(self.url_voorkeuren)
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100003.sportervoorkeuren_set.all()[0]
        self.assertFalse(voorkeur.wedstrijd_geslacht_gekozen)

        # pas het wedstrijdgeslacht aan naar vrouw
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'wedstrijd_mv': 'V'})
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100003.sportervoorkeuren_set.all()[0]
        self.assertTrue(voorkeur.wedstrijd_geslacht_gekozen)
        self.assertEqual(voorkeur.wedstrijd_geslacht, 'V')

        # pas het wedstrijdgeslacht aan naar man
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'wedstrijd_mv': 'M'})
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100003.sportervoorkeuren_set.all()[0]
        self.assertTrue(voorkeur.wedstrijd_geslacht_gekozen)
        self.assertEqual(voorkeur.wedstrijd_geslacht, 'M')

        # pas het wedstrijdgeslacht aan naar 'geen keuze'
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren)
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100003.sportervoorkeuren_set.all()[0]
        self.assertFalse(voorkeur.wedstrijd_geslacht_gekozen)



# end of file
