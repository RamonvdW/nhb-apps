# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import Account
from BasisTypen.definities import ORGANISATIE_WA
from BasisTypen.models import BoogType
from Geo.models import Regio
from Functie.tests.helpers import maak_functie
from Scheidsrechter.definities import SCHEIDS_BOND
from Score.models import Aanvangsgemiddelde
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from Sporter.operations import get_sporter_voorkeuren, get_sporter_voorkeuren_wedstrijdbogen, get_sporterboog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
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
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_hwl = self.e2e_create_account('hwl', 'hwl@test.com', 'Secretaris')
        self.e2e_account_accepteert_vhpg(self.account_hwl)
        self.account_100003 = self.e2e_create_account('100003', 'sporterx@test.com', 'Geslacht X')

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

        self.functie_hwl = maak_functie('HWL 1000', 'HWL')
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_hwl)

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100001,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Tester",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_normaal,
                        email=self.account_normaal.bevestigde_email)
        sporter.save()
        self.sporter_100001 = sporter

        # maak nog een test vereniging
        ver = Vereniging(
                    naam="Nieuwe Club",
                    ver_nr=1001,
                    regio=Regio.objects.get(pk=112))
        ver.save()

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100002,
                        geslacht="V",
                        voornaam="Ramona",
                        achternaam="de Testerin",       # noqa
                        email="",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_hwl)
        sporter.save()
        self.sporter_100002 = sporter

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100003,
                        geslacht="X",
                        voornaam="RamonX",
                        achternaam="de Xester",     # noqa
                        email="",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_100003)
        sporter.save()
        self.sporter_100003 = sporter

        self.boog_R = BoogType.objects.get(afkorting='R')

    def test_view(self):
        # zonder login
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assert_is_redirect_login(resp, self.url_voorkeuren)

        # met sporter-login wel toegankelijk
        self.e2e_login(self.account_normaal)

        # initieel zijn er geen voorkeuren opgeslagen
        self.assertEqual(SporterBoog.objects.count(), 0)
        self.assertEqual(SporterVoorkeuren.objects.count(), 0)

        with self.assert_max_queries(20, ):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/voorkeuren.dtl', 'plein/site_layout.dtl'))

        # bekijken voorkeuren maakt ze niet aan
        self.assertEqual(SporterBoog.objects.count(), 0)

        # gebruik een POST om de voorkeuren aan te maken
        resp = self.client.post(self.url_voorkeuren, {'info_R': 'on'})
        self.assert_is_redirect(resp, self.url_profiel)

        # ophalen als de voorkeuren sportersboog wel aangemaakt zijn
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(SporterBoog.objects.count(), 17)
        self.assertNotContains(resp, 'Voorkeuren voor scheidsrechters')

        obj = SporterBoog.objects.get(sporter=self.sporter_100001, boogtype=self.boog_R)
        self.assertTrue(obj.heeft_interesse)
        self.assertFalse(obj.voor_wedstrijd)

        # maak wat wijzigingen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on',
                                                          'info_BB': 'on',
                                                          'voorkeur_eigen_blazoen': 'on'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(SporterBoog.objects.count(), 17)
        self.assertEqual(SporterVoorkeuren.objects.count(), 1)

        obj = SporterBoog.objects.get(sporter=self.sporter_100001, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SporterVoorkeuren.objects.select_related('sporter').first()
        self.assertEqual(voorkeuren.sporter, self.sporter_100001)
        self.assertTrue(voorkeuren.voorkeur_eigen_blazoen)
        self.assertFalse(voorkeuren.voorkeur_meedoen_competitie)

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

        obj = SporterBoog.objects.get(sporter=self.sporter_100001, boogtype=self.boog_R)
        self.assertFalse(obj.heeft_interesse)
        self.assertTrue(obj.voor_wedstrijd)

        voorkeuren = SporterVoorkeuren.objects.first()
        self.assertFalse(voorkeuren.voorkeur_eigen_blazoen)

        # voorkeur competitie weer aan zetten
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'voorkeur_meedoen_competitie': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SporterVoorkeuren.objects.first()
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

    def test_getters(self):
        get_sporter_voorkeuren(self.sporter_100001, mag_database_wijzigen=True)

        # bestaat niet
        sporter, voorkeuren, boog_pks = get_sporter_voorkeuren_wedstrijdbogen(lid_nr=999999)
        self.assertIsNone(sporter)
        self.assertIsNone(voorkeuren)
        self.assertEqual(len(boog_pks), 0)

        # initieel zijn er geen bogen
        sporter, voorkeuren, boog_pks = get_sporter_voorkeuren_wedstrijdbogen(self.sporter_100001.lid_nr)
        self.assertIsNotNone(sporter)
        self.assertIsNotNone(voorkeuren)
        self.assertEqual(len(boog_pks), 0)

        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maakt ook de SporterBoog aan met de juiste instellingen
        resp = self.client.post(self.url_voorkeuren, {'sporter_pk': self.sporter_100001.lid_nr,
                                                      'schiet_R': 'on',
                                                      'schiet_C': 'on'})
        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

        sporter, voorkeuren, boog_pks = get_sporter_voorkeuren_wedstrijdbogen(self.sporter_100001.lid_nr)
        self.assertIsNotNone(sporter)
        self.assertIsNotNone(voorkeuren)
        self.assertEqual(len(boog_pks), 2)

    def test_hwl(self):
        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # voorkom veel queries tijdens eigenlijke test
        get_sporterboog(self.sporter_100001, mag_database_wijzigen=True)

        # haal als HWL de voorkeuren pagina op van een lid
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + '100001/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('sporter/voorkeuren.dtl', 'plein/site_layout.dtl'))

        # controleer de stand van zaken voordat de HWL iets wijzigt
        obj_r = SporterBoog.objects.get(sporter__lid_nr=100001, boogtype__afkorting='R')
        obj_c = SporterBoog.objects.get(sporter__lid_nr=100001, boogtype__afkorting='C')
        self.assertFalse(obj_r.voor_wedstrijd)
        self.assertFalse(obj_c.voor_wedstrijd)
        self.assertTrue(obj_r.heeft_interesse)
        self.assertTrue(obj_c.heeft_interesse)

        # post een wijziging
        with self.assert_max_queries(28):
            resp = self.client.post(self.url_voorkeuren, {'sporter_pk': '100001', 'schiet_R': 'on', 'info_C': 'on'})
        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

        # controleer dat de post werkt
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
        resp = self.client.get(self.url_voorkeuren + '999999/')
        self.assert404(resp, 'Sporter niet gevonden')

        # haal als HWL de voorkeuren pagina op van een lid van een andere vereniging
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + '100002/')
        self.assert403(resp)

    def test_geen_wedstrijden(self):
        # self.account_normaal is lid bij self.ver1
        # zet deze in de administratieve regio
        self.ver1.geen_wedstrijden = True
        self.ver1.save()

        self.e2e_login(self.account_normaal)

        # mag geen bogen instellen
        # helemaal geen voorkeuren, om precies te zijn
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertEqual(0, SporterBoog.objects.filter(sporter=self.sporter_100001).count())

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
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'plein/site_layout.dtl'))

        nieuw_ww = 'GratisNieuwGheim'       # noqa

        # foutief huidige wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'huidige': nieuw_ww, 'nieuwe': nieuw_ww})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Huidige wachtwoord komt niet overeen')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'nieuwe': '123412341234'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/wachtwoord-wijzigen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'wachtwoord bevat te veel gelijke tekens')

        # wijzig het wachtwoord
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig, {'huidige': self.WACHTWOORD, 'nieuwe': nieuw_ww})
        self.assert_is_redirect(resp, '/plein/')

        # controleer dat het nieuwe wachtwoord gebruikt kan worden
        self.client.logout()
        self.e2e_login(self.account_hwl, wachtwoord=nieuw_ww)

    def test_discipline(self):
        self.e2e_login(self.account_normaal)

        # voorkeuren aanmaken
        get_sporter_voorkeuren(self.sporter_100001, mag_database_wijzigen=True)

        # check the initiële voorkeuren: alle disciplines actief
        voorkeuren = SporterVoorkeuren.objects.first()
        self.assertTrue(voorkeuren.voorkeur_discipline_25m1pijl)
        self.assertTrue(voorkeuren.voorkeur_discipline_outdoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_indoor)
        self.assertTrue(voorkeuren.voorkeur_discipline_clout)
        self.assertTrue(voorkeuren.voorkeur_discipline_veld)
        self.assertTrue(voorkeuren.voorkeur_discipline_run)
        self.assertTrue(voorkeuren.voorkeur_discipline_3d)

        # alle disciplines 'uit' zetten
        with self.assert_max_queries(29):
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

        get_sporter_voorkeuren(self.sporter_100001, mag_database_wijzigen=True)

        # niet-para sporter mag ook een opmerking invoeren
        voorkeuren = SporterVoorkeuren.objects.filter(sporter__account=self.account_normaal).first()
        self.assertEqual(voorkeuren.opmerking_para_sporter, '')
        self.assertFalse(voorkeuren.para_voorwerpen)

        with self.assert_max_queries(30):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test 1',
                                                          'para_voorwerpen': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SporterVoorkeuren.objects.get(pk=voorkeuren.pk)
        self.assertEqual(voorkeuren.opmerking_para_sporter, 'Hallo test 1')
        self.assertTrue(voorkeuren.para_voorwerpen)

        # maak dit een para sporter
        self.sporter_100001.para_classificatie = 'VI1'
        self.sporter_100001.save()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test 2'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        voorkeuren = SporterVoorkeuren.objects.get(pk=voorkeuren.pk)
        self.assertEqual(voorkeuren.opmerking_para_sporter, 'Hallo test 2')
        self.assertFalse(voorkeuren.para_voorwerpen)

        # coverage: opslaan zonder wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'para_notitie': 'Hallo test 2'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

    def test_email_optout(self):
        # log in als beheerder, maar blijf sporter
        self.e2e_login(self.account_hwl)
        self.e2e_wisselnaarrol_sporter()

        # check de defaults
        account = self.account_hwl
        self.assertFalse(account.optout_nieuwe_taak)
        self.assertFalse(account.optout_herinnering_taken)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/voorkeuren.dtl', 'plein/site_layout.dtl'))

        # wijzig zonder opt-out te doen
        with self.assert_max_queries(33):
            resp = self.client.post(self.url_voorkeuren, {})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        account = Account.objects.get(pk=account.pk)
        self.assertFalse(account.optout_nieuwe_taak)
        self.assertFalse(account.optout_herinnering_taken)

        # wijzig met opt-out
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'optout_nieuwe_taak': 'ja'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        account = Account.objects.get(pk=account.pk)
        self.assertTrue(account.optout_nieuwe_taak)
        self.assertFalse(account.optout_herinnering_taken)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'optout_herinnering_taken': 'on'})
        self.assert_is_redirect(resp, '/sporter/')     # naar profiel

        account = Account.objects.get(pk=account.pk)
        self.assertFalse(account.optout_nieuwe_taak)
        self.assertTrue(account.optout_herinnering_taken)

    def test_geslacht_anders(self):
        # begin met de sporter met geslacht man
        self.e2e_login(self.account_hwl)

        # voorkeuren aanmaken
        get_sporter_voorkeuren(self.sporter_100002, mag_database_wijzigen=True)

        # controleer de voorkeuren
        voorkeur = self.sporter_100002.sportervoorkeuren_set.first()
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

        voorkeur = self.sporter_100002.sportervoorkeuren_set.first()
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

        voorkeur = self.sporter_100003.sportervoorkeuren_set.first()
        self.assertFalse(voorkeur.wedstrijd_geslacht_gekozen)

        # pas het wedstrijdgeslacht aan naar vrouw
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'wedstrijd_mv': 'V'})
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100003.sportervoorkeuren_set.first()
        self.assertTrue(voorkeur.wedstrijd_geslacht_gekozen)
        self.assertEqual(voorkeur.wedstrijd_geslacht, 'V')

        # pas het wedstrijdgeslacht aan naar man
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren, {'wedstrijd_mv': 'M'})
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100003.sportervoorkeuren_set.first()
        self.assertTrue(voorkeur.wedstrijd_geslacht_gekozen)
        self.assertEqual(voorkeur.wedstrijd_geslacht, 'M')

        # pas het wedstrijdgeslacht aan naar 'geen keuze'
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_voorkeuren)
        self.assert_is_redirect(resp, self.url_profiel)

        voorkeur = self.sporter_100003.sportervoorkeuren_set.first()
        self.assertFalse(voorkeur.wedstrijd_geslacht_gekozen)

    def test_get_sporterboog(self):
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 0)

        objs = get_sporterboog(self.sporter_100001, mag_database_wijzigen=False, geen_wedstrijden=False)
        self.assertEqual(len(objs), 17)     # 5x WA + 12x IFAA
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 0)

        objs = get_sporterboog(self.sporter_100001, mag_database_wijzigen=True, geen_wedstrijden=False)
        self.assertEqual(len(objs), 17)     # 5x WA + 12x IFAA
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 17)

        # geen actie
        objs = get_sporterboog(self.sporter_100001, mag_database_wijzigen=True, geen_wedstrijden=False)
        self.assertEqual(len(objs), 17)     # 5x WA + 12x IFAA
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 17)

        # controleer aanvullen bij te weinig bogen
        SporterBoog.objects.filter(boogtype__organisatie=ORGANISATIE_WA).delete()
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 12)
        objs = get_sporterboog(self.sporter_100001, mag_database_wijzigen=True, geen_wedstrijden=False)
        self.assertEqual(len(objs), 17)     # 5x WA + 12x IFAA
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 17)

        # gebruik een SporterBoog in een record met on_delete=models.PROTECT
        sb = SporterBoog.objects.get(sporter=self.sporter_100001, boogtype=self.boog_R)
        ag = Aanvangsgemiddelde(
                    sporterboog=sb,
                    boogtype=self.boog_R,
                    waarde=1,
                    afstand_meter=1)
        ag.save()

        objs = get_sporterboog(self.sporter_100001, mag_database_wijzigen=False, geen_wedstrijden=True)
        self.assertEqual(len(objs), 0)
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 17)

        objs = get_sporterboog(self.sporter_100001, mag_database_wijzigen=True, geen_wedstrijden=True)
        self.assertEqual(len(objs), 0)
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 17)

        ag.delete()
        objs = get_sporterboog(self.sporter_100001, mag_database_wijzigen=True, geen_wedstrijden=True)
        self.assertEqual(len(objs), 0)
        self.assertEqual(SporterBoog.objects.filter(sporter=self.sporter_100001).count(), 0)

    def test_sr(self):
        self.account_normaal.scheids = SCHEIDS_BOND
        self.account_normaal.save(update_fields=['scheids'])
        self.sporter_100001.scheids = SCHEIDS_BOND
        self.sporter_100001.save(update_fields=['scheids'])
        self.e2e_login(self.account_normaal)

        # voorkom veel queries tijdens eigenlijke test
        # get_sporterboog(self.sporter_100001, mag_database_wijzigen=True)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Voorkeuren voor scheidsrechters')

        with self.assert_max_queries(32):
            resp = self.client.post(self.url_voorkeuren, {'sr_wed_email': True,
                                                          'sr_wed_tel': True})

        voorkeuren = get_sporter_voorkeuren(self.sporter_100001)
        self.assertFalse(voorkeuren.scheids_opt_in_korps_email)
        self.assertFalse(voorkeuren.scheids_opt_in_korps_tel_nr)
        self.assertTrue(voorkeuren.scheids_opt_in_ver_email)
        self.assertTrue(voorkeuren.scheids_opt_in_ver_tel_nr)

        resp = self.client.post(self.url_voorkeuren, {'sr_korps_email': True,
                                                      'sr_korps_tel': True})

        voorkeuren.refresh_from_db()
        self.assertTrue(voorkeuren.scheids_opt_in_korps_email)
        self.assertTrue(voorkeuren.scheids_opt_in_korps_tel_nr)
        self.assertFalse(voorkeuren.scheids_opt_in_ver_email)
        self.assertFalse(voorkeuren.scheids_opt_in_ver_tel_nr)

    def test_hwl_sr(self):
        # controleer dat de HWL niet de voorkeuren voor delen contactgegevens van een scheidsrechters-lid aan kan passen
        self.account_normaal.scheids = SCHEIDS_BOND
        self.account_normaal.save(update_fields=['scheids'])
        self.sporter_100001.scheids = SCHEIDS_BOND
        self.sporter_100001.save(update_fields=['scheids'])

        # login as HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal als HWL de voorkeuren pagina op van een lid
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_voorkeuren + '100001/')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('sporter/voorkeuren.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Voorkeuren voor scheidsrechters')


# end of file
