# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from Functie.models import Functie
from Functie.operations import maak_functie
from Locatie.models import Locatie
from NhbStructuur.models import Rayon, Regio, Cluster
from Sporter.models import Sporter
from Vereniging.models2 import Secretaris
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestVerenigingAccommodatie(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, functie Accommodaties """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie')

    url_locatie = '/vereniging/locatie/%s/'   # ver_nr

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # rayon_3 = Rayon.objects.get(rayon_nr=3)
        # regio_111 = Regio.objects.get(regio_nr=111)
        regio_101 = Regio.objects.get(regio_nr=101)
        #
        # # RKO rol
        # self.account_rko = self.e2e_create_account('rko', 'rko@test.com', 'RKO', accepteer_vhpg=True)
        # self.functie_rko3 = Functie.objects.filter(rol="RKO", rayon=rayon_3)[0]
        # self.functie_rko3.accounts.add(self.account_rko)
        #
        # # RCL rol
        # self.account_rcl = self.e2e_create_account('rcl', 'rcl@test.com', 'RCL', accepteer_vhpg=True)
        # self.functie_rcl111 = Functie.objects.filter(rol="RCL", regio=regio_111)[0]
        # self.functie_rcl111.accounts.add(self.account_rcl)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Noordelijke Club",
                    ver_nr=1000,
                    regio=regio_101)
        ver.save()
        self.ver1 = ver

        # maak de SEC, HWL en WL functies aan voor deze vereniging
        for rol in ('SEC', 'HWL', 'WL'):
            tmp_func = maak_functie(rol + " ver1", rol)
            tmp_func.vereniging = ver
            tmp_func.save()
        # for

        # # maak een locatie aan
        # loc = Locatie(
        #             adres='Grote baan')
        # loc.save()
        # loc.verenigingen.add(ver)
        # self.loc1 = loc
        #
        #
        # # maak de HWL functie
        # self.functie_hwl1 = maak_functie("HWL test 1", "HWL")
        # self.functie_hwl1.vereniging = self.ver1
        # self.functie_hwl1.save()
        #
        # self.account_hwl1 = self.e2e_create_account('hwl1', 'hwl1@test.not', 'HWL', accepteer_vhpg=True)
        # self.functie_hwl1.accounts.add(self.account_hwl1)
        #
        # # maak de WL functie
        # self.functie_wl1 = maak_functie("WL test 1", "WL")
        # self.functie_wl1.vereniging = self.ver1
        # self.functie_wl1.save()
        #
        # # maak een test vereniging
        # ver = Vereniging(
        #             naam="Grote Club",
        #             ver_nr=1001,
        #             regio=regio_111)
        # ver.save()
        # self.ver2 = ver
        #
        # # maak de SEC functie
        # self.functie_sec = maak_functie("SEC test", "SEC")
        # self.functie_sec.vereniging = self.ver2
        # self.functie_sec.save()
        #
        # # maak de HWL functie
        # self.functie_hwl = maak_functie("HWL test", "HWL")
        # self.functie_hwl.vereniging = self.ver2
        # self.functie_hwl.save()
        #
        # # maak de WL functie
        # self.functie_wl = maak_functie("WL test", "WL")
        # self.functie_wl.vereniging = self.ver2
        # self.functie_wl.save()
        #
        # # maak een locatie aan
        # loc = Locatie(
        #             adres='Kleine baan')
        # loc.save()
        # loc.verenigingen.add(ver)
        # self.loc2 = loc
        #
        # # maak het lid aan dat HWL wordt
        # sporter = Sporter(
        #                 lid_nr=100001,
        #                 geslacht="M",
        #                 voornaam="Ramon",
        #                 achternaam="de Tester",
        #                 email="rdetester@gmail.not",
        #                 geboorte_datum=datetime.date(year=1972, month=3, day=4),
        #                 sinds_datum=datetime.date(year=2010, month=11, day=12),
        #                 bij_vereniging=ver)
        # sporter.save()
        #
        # self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        # self.functie_hwl.accounts.add(self.account_hwl)
        #
        # sporter.account = self.account_hwl
        # sporter.save()
        # self.sporter_100001 = sporter
        #
        # # maak het lid aan dat SEC wordt
        # sporter = Sporter(
        #                 lid_nr=100002,
        #                 geslacht="M",
        #                 voornaam="Ramon",
        #                 achternaam="de Secretaris",
        #                 email="rdesecretaris@gmail.not",
        #                 geboorte_datum=datetime.date(year=1972, month=3, day=4),
        #                 sinds_datum=datetime.date(year=2010, month=11, day=12),
        #                 bij_vereniging=ver)
        # sporter.save()
        #
        # self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        # self.functie_sec.accounts.add(self.account_sec)
        #
        # sporter.account = self.account_sec
        # sporter.save()
        # self.sporter_100002 = sporter
        #
        # sec = Secretaris(vereniging=ver)
        # sec.save()
        # sec.sporters.add(sporter)
        # self.sec = sec
        pass

    def test_geen_toegang(self):
        # anon
        self.e2e_logout()

        url = self.url_locatie % self.ver1.ver_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # specifieke locatie
        url = self.url_locatie % self.ver1.ver_nr
        resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

    def _not_later(self):

        # vereniging die niet bij de locatie hoort
        url = self.url_locatie % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Geen valide vereniging')

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    # def test_rko(self):
    #     # login als RKO
    #     self.e2e_login_and_pass_otp(self.account_rko)
    #     self.e2e_wissel_naar_functie(self.functie_rko3)
    #     self.e2e_check_rol('RKO')
    #
    #     # grote lijst - alleen binnen het rayon
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)     # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/lijst.dtl', 'plein/site_layout.dtl'))
    #     # TODO: check alleen rayon
    #
    #     # details van een vereniging binnen het rayon
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    # def test_rcl(self):
    #     # login als RCL
    #     self.e2e_login_and_pass_otp(self.account_rcl)
    #     self.e2e_wissel_naar_functie(self.functie_rcl111)
    #     self.e2e_check_rol('RCL')
    #
    #     # grote lijst - alleen binnen de regio
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/lijst.dtl', 'plein/site_layout.dtl'))
    #     self.assertContains(resp, '[1001]')         # in regio 111
    #     self.assertNotContains(resp, '[1000]')      # in regio 101
    #
    #     # details van een vereniging binnen de regio
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    #     # details van een vereniging buiten de regio
    #     url = self.url_locatie % self.ver1.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    #     # wijziging aanbrengen
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    #     # probeer een wijziging te doen
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'X',
    #                                       'banen_18m': 1,
    #                                       'banen_25m': 0,
    #                                       'notities': 'hoi'})
    #     self.assert_is_redirect(resp, self.url_lijst)
    #     loc2 = Locatie.objects.get(pk=self.loc2.pk)
    #     self.assertEqual(loc2.baan_type, 'X')
    #     self.assertEqual(loc2.banen_18m, 1)
    #     self.assertEqual(loc2.banen_25m, 0)
    #     self.assertEqual(loc2.notities, 'hoi')
    #
    #     # doe een niet-wijziging voor de coverage
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'X',
    #                                       'banen_18m': 1,
    #                                       'banen_25m': 0,
    #                                       'max_sporters_18m': 4,
    #                                       'max_sporters_25m': 0,
    #                                       'notities': 'hoi'})
    #     self.assert_is_redirect(resp, self.url_lijst)
    #     loc2 = Locatie.objects.get(pk=self.loc2.pk)
    #     self.assertEqual(loc2.baan_type, 'X')
    #     self.assertEqual(loc2.banen_18m, 1)
    #     self.assertEqual(loc2.banen_25m, 0)
    #     self.assertEqual(loc2.max_sporters_18m, 4)
    #     self.assertEqual(loc2.max_sporters_25m, 0)
    #     self.assertEqual(loc2.notities, 'hoi')
    #
    # def test_hwl(self):
    #     # login als HWL van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     self.e2e_check_rol('HWL')
    #
    #     # HWL krijgt dezelfde lijst als de RCL
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/lijst.dtl', 'plein/site_layout.dtl'))
    #     self.assertContains(resp, '[1001]')         # in regio 111
    #     self.assertNotContains(resp, '[1000]')      # in regio 101
    #
    #     # check accommodatie detail pagina
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #     # check dat de HWL de opslaan-knop aangeboden krijgt
    #     self.assertContains(resp, 'Wijzigingen opslaan')
    #
    #     # check the specifieke accommodatie pagina voor de HWL, met andere terug url
    #     url = self.url_accommodatie_vereniging % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #     # check dat de HWL de opslaan-knop aangeboden krijgt
    #     urls = self.extract_all_urls(resp, skip_menu=True)
    #     self.assertTrue(url in urls)                # opslaan url
    #
    #     # probeer een wijziging te doen
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'O',
    #                                       'banen_18m': 5,
    #                                       'banen_25m': 6,
    #                                       'max_sporters_18m': 18,
    #                                       'max_sporters_25m': 25,
    #                                       'notities': 'dit is een test'})
    #     self.assert_is_redirect(resp, '/vereniging/')       # stuur HWL terug naar vereniging pagina
    #     loc2 = Locatie.objects.get(pk=self.loc2.pk)
    #     self.assertEqual(loc2.baan_type, 'O')
    #     self.assertEqual(loc2.banen_18m, 5)
    #     self.assertEqual(loc2.banen_25m, 6)
    #     self.assertEqual(loc2.max_sporters_18m, 18)
    #     self.assertEqual(loc2.max_sporters_25m, 25)
    #     self.assertEqual(loc2.notities, 'dit is een test')
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertContains(resp, 'Volledig overdekt')
    #
    #     lange_tekst = "Dit is een heel verhaal van minimaal 200 tekens zodat we de limiet van 500 tekens bereiken " + \
    #                   "bij het schrijven naar het logboek. Het is namelijk een keer voorgekomen dat de notitie " + \
    #                   "niet opgeslagen kon worden omdat deze te lang is. In het logboek schrijven we de oude en " + \
    #                   "de nieuwe tekst."
    #
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'H',
    #                                       'banen_18m': 0,
    #                                       'banen_25m': 0,
    #                                       'max_sporters_18m': 18,       # no change
    #                                       'max_sporters_25m': 25,       # no change
    #                                       'notities': lange_tekst})
    #     self.assert_is_redirect(resp, '/vereniging/')       # stuur HWL terug naar vereniging pagina
    #     loc2 = Locatie.objects.get(pk=self.loc2.pk)
    #     self.assertEqual(loc2.baan_type, 'H')
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertContains(resp, 'Half overdekt')
    #
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'X',
    #                                       'banen_18m': 5,
    #                                       'banen_25m': 6,
    #                                       'notities': lange_tekst + " en nog wat meer"})
    #     self.assertEqual(resp.status_code, 302)     # 302 = redirect = success
    #     loc2 = Locatie.objects.get(pk=self.loc2.pk)
    #     self.assertEqual(loc2.baan_type, 'X')
    #
    #     # probeer met illegale waarden
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'O',
    #                                       'banen_18m': 40,
    #                                       'banen_25m': 6})
    #     self.assert404(resp, 'Geen valide invoer')
    #
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'O',
    #                                       'banen_18m': 4,
    #                                       'banen_25m': 40})
    #     self.assert404(resp, 'Geen valide invoer')
    #
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'y',
    #                                       'banen_18m': 4,
    #                                       'banen_25m': 4})
    #     self.assert404(resp, 'Geen valide invoer')
    #
    #     # verwijder de binnenlocatie
    #     # gebruik de alternatieve url
    #     loc2.delete()
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(self.url_locatie % self.ver2.ver_nr,
    #                                 {'maak_buiten_locatie': 'graag'})
    #     self.assertEqual(resp.status_code, 302)     # 302 = redirect = success
    #
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(self.url_locatie % self.ver2.ver_nr,
    #                                 {'baan_type': 'X'})
    #     self.assertEqual(resp.status_code, 302)     # 302 = redirect = success
    #
    #     # illegale location_pk
    #     url = self.url_accommodatie_vereniging % 888888
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'O',
    #                                       'banen_18m': 4,
    #                                       'banen_25m': 4})
    #     self.assert404(resp, 'Geen valide vereniging')
    #
    # def test_wl(self):
    #     # login als HWL van ver2 op loc2
    #     # en wordt daarna WL
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_wl)
    #     self.e2e_check_rol('WL')
    #
    #     # WL mag de hele lijst met verenigingen niet ophalen
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assert403(resp)
    #
    #     # haal de SEC uit zijn functie zodat deze direct uit de vereniging gehaald wordt
    #     self.functie_sec.accounts.clear()
    #
    #     # check accommodatie detail pagina
    #     url = self.url_accommodatie_vereniging % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    #     # check dat de WL de opslaan-knop NIET aangeboden krijgt
    #     self.assertNotContains(resp, 'Wijzigingen opslaan')
    #
    #     # nog een keer, voor een vereniging zonder secretaris
    #     self.ver2.secretaris_lid = None
    #     self.ver2.save()
    #
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    #     # probeer een wijziging te doen
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'O',
    #                                       'banen_18m': 5,
    #                                       'banen_25m': 6,
    #                                       'notities': 'dit is een test'})
    #     self.assert403(resp)
    #
    #     # zet het aantal banen op 0,0
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     with self.assert_max_queries(20):
    #         self.client.post(url, {'baan_type': 'H',
    #                                'banen_18m': 1,
    #                                'banen_25m': 0,
    #                                'notities': 'dit is een test'})
    #     # haal op als WL, dan krijg je read-only zonder DT
    #     self.e2e_wissel_naar_functie(self.functie_wl)
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    # def test_sec(self):
    #     # login als SEC van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_sec)
    #     self.e2e_wissel_naar_functie(self.functie_sec)
    #     self.e2e_check_rol('SEC')
    #
    #     # SEC krijgt dezelfde lijst als de RCL?
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/lijst.dtl', 'plein/site_layout.dtl'))
    #
    #     # check accommodatie detail pagina
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #     # check dat de HWL de opslaan-knop aangeboden krijgt
    #     urls = self.extract_all_urls(resp, skip_menu=True)
    #     self.assertTrue(url in urls)                                    # opslaan url
    #
    # def test_geen_hwl_wl(self):
    #     # vereniging 'extern' heeft geen HWL en WL
    #
    #     # haal de speciale vereniging en functie op
    #     ver = Vereniging.objects.get(ver_nr=settings.EXTERN_VER_NR)
    #     self.assertTrue(ver.is_extern)
    #     functie_sec = Functie.objects.get(rol='SEC', vereniging=ver)
    #
    #     # maak het lid aan dat SEC wordt
    #     sporter = Sporter(
    #                     lid_nr=108001,
    #                     geslacht="M",
    #                     voornaam="Ramon",
    #                     achternaam="de Secretaris",
    #                     email="sec8000@test.not",
    #                     geboorte_datum=datetime.date(year=1972, month=3, day=5),
    #                     sinds_datum=datetime.date(year=2010, month=11, day=12),
    #                     bij_vereniging=ver)
    #     sporter.save()
    #
    #     account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
    #     functie_sec.accounts.add(account)
    #
    #     self.e2e_login_and_pass_otp(account)
    #     self.e2e_wissel_naar_functie(functie_sec)
    #     self.e2e_check_rol('SEC')
    #
    #     # check accommodatie detail pagina
    #     url = self.url_locatie % ver.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    # def test_bad(self):
    #     # login als SEC van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_sec)
    #     self.e2e_wissel_naar_functie(self.functie_sec)
    #     self.e2e_check_rol('SEC')
    #
    #     # probeer van andere vereniging te wijzigen
    #     url = self.url_locatie % self.ver1.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'H',
    #                                       'banen_18m': 5,
    #                                       'banen_25m': 6,
    #                                       'notities': 'dit is een test'})
    #     self.assert403(resp)
    #
    # def test_gedeelde_locatie(self):
    #     # login als BB
    #     self.e2e_login_and_pass_otp(self.testdata.account_bb)
    #     self.e2e_wisselnaarrol_bb()
    #     self.e2e_check_rol('BB')
    #
    #     # maak een locatie aan die door twee verenigingen gedeeld wordt
    #     loc = Locatie()
    #     loc.save()
    #     loc.verenigingen.add(self.ver1)
    #     loc.verenigingen.add(self.ver2)
    #
    #     # haal de details op
    #     url = self.url_locatie % self.ver1.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    #     # haal de details op
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    # def test_cluster(self):
    #     # stop de vereniging in een cluster
    #     cluster = Cluster.objects.filter(regio=self.ver2.regio, gebruik='18').first()
    #     self.ver2.clusters.add(cluster)
    #     cluster = Cluster.objects.filter(regio=self.ver2.regio, gebruik='25').all()[2]
    #     self.ver2.clusters.add(cluster)
    #
    #     # login als HWL van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     self.e2e_check_rol('HWL')
    #
    #     # accommodaties lijst
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/lijst.dtl', 'plein/site_layout.dtl'))
    #
    #     # accommodatie details
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/accommodatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #     # check dat de HWL de opslaan-knop aangeboden krijgt
    #     urls = self.extract_all_urls(resp, skip_menu=True)
    #     self.assertTrue(url in urls)                                    # opslaan url
    #
    #     # accommodaties lijst corner case
    #     self.e2e_login_and_pass_otp(self.testdata.account_bb)
    #     self.e2e_wisselnaarrol_bb()
    #     self.e2e_check_rol('BB')
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #
    # def test_binnen_en_buiten_locatie(self):
    #     # login als HWL van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     self.e2e_check_rol('HWL')
    #
    #     url = self.url_accommodatie_vereniging % self.ver2.ver_nr
    #
    #     # verwijder de buitenlocatie terwijl deze niet bestaat
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'verwijder_buitenbaan': 'ja'})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     # maak de buitenlocatie aan
    #     self.assertEqual(1, self.ver2.locatie_set.count())
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'maak_buiten_locatie': 'on'})
    #     self.assert_is_redirect(resp, url)
    #     self.assertEqual(2, self.ver2.locatie_set.count())
    #     buiten_locatie = self.ver2.locatie_set.filter(baan_type='B').first()
    #
    #     # maak de buiten locatie nog een keer aan
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'maak_buiten_locatie': 'on'})
    #     # is geen probleem - dan wordt de al bestaande buiten locatie op zichtbaar=True gezet
    #     self.assert_is_redirect(resp, url)
    #     self.assertEqual(2, self.ver2.locatie_set.count())
    #
    #     # haal het scherm op met de buiten locatie erin
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    #     # pas wat parameters aan
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'H',
    #                                       'banen_18m': 5,
    #                                       'banen_25m': 6,
    #                                       'notities': 'dit is een test',
    #                                       'disc_outdoor': 'on',
    #                                       'disc_clout': 'on',
    #                                       'buiten_banen': 50,
    #                                       'buiten_max_afstand': 90,
    #                                       'buiten_notities': 'dit is een buiten test'})
    #     self.assert_is_redirect(resp, '/vereniging/')
    #
    #     buiten_locatie = Locatie.objects.get(pk=buiten_locatie.pk)
    #     self.assertEqual(buiten_locatie.adres, 'Kleine baan')       # overgenomen van de binnenlocatie
    #     self.assertEqual(buiten_locatie.buiten_banen, 50)
    #     self.assertEqual(buiten_locatie.buiten_max_afstand, 90)
    #     self.assertEqual(buiten_locatie.notities, 'dit is een buiten test')
    #     self.assertTrue(buiten_locatie.discipline_outdoor)
    #     self.assertTrue(buiten_locatie.discipline_clout)
    #
    #     # nog een keer opslaan zodat er geen wijzigingen zijn
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'baan_type': 'H',
    #                                       'banen_18m': 5,
    #                                       'banen_25m': 6,
    #                                       'notities': 'dit is een test',
    #                                       'disc_outdoor': 'on',
    #                                       'disc_clout': 'on',
    #                                       'buiten_banen': 50,
    #                                       'buiten_max_afstand': 90,
    #                                       'buiten_notities': 'dit is een buiten test'})
    #     self.assert_is_redirect(resp, '/vereniging/')
    #
    #     # haal de lijst op, zodat we daar ook een buitenlocatie in hebben
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    #     self.assertTrue(buiten_locatie.zichtbaar)
    #
    #     # verwijder de buitenlocatie
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'verwijder_buitenbaan': 'ja'})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     # nog een keer, via de alternatieve url
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(self.url_locatie % self.ver2.ver_nr,
    #                                 {'verwijder_buitenbaan': 'ja'})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     buiten_locatie = Locatie.objects.get(pk=buiten_locatie.pk)
    #     self.assertFalse(buiten_locatie.zichtbaar)
    #
    #     # haal het scherm op zonder de buitenlocatie erin
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    #     # herstel buitenlocatie
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'maak_buiten_locatie': 'ja'})
    #     self.assert_is_redirect_not_plein(resp)
    #
    # def test_externe_locatie(self):
    #     # login als BB
    #     self.e2e_login_and_pass_otp(self.testdata.account_bb)
    #     self.e2e_wisselnaarrol_bb()
    #     self.e2e_check_rol('BB')
    #
    #     url = self.url_externe_locaties % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     # controleer dat er geen knop is om een nieuwe locatie toe te voegen
    #     urls = self.extract_all_urls(resp, skip_menu=True)
    #     self.assertEqual(urls, [])
    #
    #     # niet bestaande vereniging
    #     resp = self.client.get(self.url_externe_locaties % 999999)
    #     self.assert404(resp, 'Vereniging niet gevonden')
    #
    #     # probeer een locatie toe te voegen
    #     resp = self.client.post(url)
    #     self.assert403(resp)
    #
    #     # login als HWL van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     self.e2e_check_rol('HWL')
    #
    #     url = self.url_externe_locaties % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/externe-locaties.dtl', 'plein/site_layout.dtl'))
    #     # controleer dat er een knop is om een nieuwe locatie toe te voegen
    #     urls = self.extract_all_urls(resp, skip_menu=True)
    #     self.assertEqual(urls, [url])
    #
    #     # voeg een locatie toe
    #     self.assertEqual(2, Locatie.objects.count())
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url)
    #     self.assert_is_redirect_not_plein(resp)
    #     self.assertEqual(3, Locatie.objects.count())
    #     locatie = Locatie.objects.get(baan_type='E')
    #     self.assertEqual(locatie.naam, '')
    #
    #     # haal de niet-lege lijst met locaties op
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     urls = self.extract_all_urls(resp, skip_menu=True)
    #     self.assertEqual(len(urls), 2)      # wijzig-knop is erbij gekomen
    #
    #     # probeer een locatie toe te voegen van een andere vereniging
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(self.url_externe_locaties % self.ver1.ver_nr)
    #     self.assert403(resp)
    #
    #     # hanteer de externe locatie in de lijst van alle verenigingen
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_lijst)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    # def test_wijzig_externe_locatie(self):
    #     # login als HWL van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     self.e2e_check_rol('HWL')
    #
    #     # maak een externe locatie aan
    #     url = self.url_externe_locaties % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url)
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     locatie = Locatie.objects.get(baan_type='E')
    #     url = self.url_externe_locatie_details % (self.ver2.ver_nr, locatie.pk)
    #
    #     # haal de locatie details op
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/externe-locatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    #     # HWL mag de externe locatie details aanpassen
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url)
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     # HWL mag de externe locatie details aanpassen
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'naam': 'test naam',
    #                                       'adres': 'Langeboog 5\r\nBoogstad',
    #                                       'plaats': 'Boogstad',
    #                                       'disc_clout': 'on',
    #                                       'disc_veld': 'on',
    #                                       'disc_run': 1,
    #                                       'disc_3d': True,
    #                                       # indoor velden die niet meegenomen zullen worden
    #                                       'banen_18m': 1,
    #                                       'banen_25m': 1,
    #                                       # outdoor velden die niet meegenomen zullen worden
    #                                       'buiten_max_afstand': 99,
    #                                       'buiten_banen': 42,
    #                                       'notities': 'hoi\ntest\r\nmeer testen'})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     locatie = Locatie.objects.get(pk=locatie.pk)
    #     self.assertEqual(locatie.naam, 'test naam')
    #     self.assertFalse(locatie.discipline_outdoor)
    #     self.assertFalse(locatie.discipline_indoor)
    #     self.assertTrue(locatie.discipline_clout)
    #     self.assertTrue(locatie.discipline_veld)
    #     self.assertTrue(locatie.discipline_run)
    #     self.assertTrue(locatie.discipline_3d)
    #     self.assertEqual(locatie.banen_18m, 0)
    #     self.assertEqual(locatie.banen_25m, 0)
    #     self.assertEqual(locatie.buiten_max_afstand, 99)
    #     self.assertEqual(locatie.buiten_banen, 42)
    #     self.assertIn('Langeboog 5\nBoogstad', locatie.adres)
    #     self.assertEqual(locatie.plaats, 'Boogstad')
    #     self.assertFalse(locatie.adres_uit_crm)
    #     self.assertIn('hoi\ntest\nmeer testen', locatie.notities)
    #
    #     # maak er een outdoor locatie van
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'naam': 'test naam',
    #                                       'adres': 'Langeboog 5\r\nBoogstad',
    #                                       'disc_outdoor': 'on',
    #                                       'buiten_max_afstand': 190,
    #                                       'buiten_banen': 0})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     locatie = Locatie.objects.get(pk=locatie.pk)
    #     self.assertTrue(locatie.discipline_outdoor)
    #     self.assertFalse(locatie.discipline_indoor)
    #     self.assertFalse(locatie.discipline_clout)
    #     self.assertFalse(locatie.discipline_veld)
    #     self.assertFalse(locatie.discipline_run)
    #     self.assertFalse(locatie.discipline_3d)
    #     self.assertEqual(locatie.buiten_max_afstand, 100)
    #     self.assertEqual(locatie.buiten_banen, 1)
    #
    #     # no-change
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'naam': 'test naam',
    #                                       'adres': 'Langeboog 5\r\nBoogstad',
    #                                       'disc_outdoor': 'on',
    #                                       'buiten_max_afstand': 190,
    #                                       'buiten_banen': 0})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     # bad values
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'naam': 'test naam',
    #                                       'adres': 'Langeboog 5\r\nBoogstad',
    #                                       'disc_outdoor': 'on',
    #                                       'buiten_max_afstand': 'xxx',
    #                                       'buiten_banen': 'xxx'})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     # maak er een indoor locatie van
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'naam': 'test naam',
    #                                       'adres': 'Langeboog 5\r\nBoogstad',
    #                                       'disc_indoor': 'on',
    #                                       'max_sporters_18m': 18,
    #                                       'max_sporters_25m': 25,
    #                                       'banen_18m': 17,
    #                                       'banen_25m': 24})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     locatie = Locatie.objects.get(pk=locatie.pk)
    #     self.assertFalse(locatie.discipline_outdoor)
    #     self.assertTrue(locatie.discipline_indoor)
    #     self.assertEqual(locatie.banen_18m, 17)
    #     self.assertEqual(locatie.banen_25m, 24)
    #     self.assertEqual(locatie.max_sporters_18m, 18)
    #     self.assertEqual(locatie.max_sporters_25m, 25)
    #
    #     # no change
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'naam': 'test naam',
    #                                       'adres': 'Langeboog 5\r\nBoogstad',
    #                                       'disc_indoor': 'on',
    #                                       'banen_18m': 17,
    #                                       'banen_25m': 24})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     # bad values
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'naam': 'test naam',
    #                                       'adres': 'Langeboog 5\r\nBoogstad',
    #                                       'disc_indoor': 'on',
    #                                       'max_sporters_18m': 'xxx',
    #                                       'max_sporters_25m': 'xxx',
    #                                       'banen_18m': 'xxx',
    #                                       'banen_25m': 'xxx'})
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     # niet bestaande locatie
    #     resp = self.client.get(self.url_externe_locatie_details % (self.ver2.ver_nr, 999999))
    #     self.assert404(resp, 'Locatie bestaat niet')
    #
    #     # niet externe locatie
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_externe_locatie_details % (self.ver2.ver_nr, self.loc2.pk))
    #     self.assert404(resp, 'Locatie bestaat niet')
    #
    #     # niet bestaande vereniging
    #     resp = self.client.get(self.url_externe_locatie_details % (999999, locatie.pk))
    #     self.assert404(resp, 'Vereniging niet gevonden')
    #
    #     # locatie van een andere vereniging
    #     self.loc1.baan_type = 'E'
    #     self.loc1.save()
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(self.url_externe_locatie_details % (self.ver2.ver_nr, self.loc1.pk))
    #     self.assert404(resp, 'Locatie hoort niet bij de vereniging')
    #
    #     # login als HWL van ver1
    #     self.e2e_login_and_pass_otp(self.account_hwl1)
    #     self.e2e_wissel_naar_functie(self.functie_hwl1)
    #     self.e2e_check_rol('HWL')
    #
    #     # iedereen mag de locatie details ook ophalen, dus ook deze 'verkeerde HWL'
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #     self.assert_template_used(resp, ('vereniging/externe-locatie-accommodatie-details.dtl', 'plein/site_layout.dtl'))
    #
    #     # verkeerde HWL mag de externe locatie details niet aanpassen
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url)
    #     self.assert403(resp)
    #
    #     # nog een poging met een niet-HWL functie
    #     self.e2e_wissel_naar_functie(self.functie_wl1)
    #     self.e2e_check_rol('WL')
    #
    #     # WL mag de externe locatie details niet aanpassen
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url)
    #     self.assert403(resp)
    #
    #     # login als HWL van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     self.e2e_check_rol('HWL')
    #
    #     # koppel de locatie los
    #     locatie.verenigingen.clear()
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url)
    #     self.assert404(resp, 'Locatie hoort niet bij de vereniging')
    #
    # def test_externe_accommodatie(self):
    #     # accommodatie bestaat niet of heeft geen banen
    #     # functie wordt overgenomen door externe locatie
    #     loc = self.ver2.locatie_set.first()
    #     loc.plaats = "Wil je niet zien!"
    #     loc.save()
    #
    #     # verwijder de accommodatie van de vereniging
    #     self.ver2.locatie_set.clear()
    #
    #     # login als HWL van ver2 op loc2
    #     self.e2e_login_and_pass_otp(self.account_hwl)
    #     self.e2e_wissel_naar_functie(self.functie_hwl)
    #     self.e2e_check_rol('HWL')
    #
    #     # maak een externe locatie aan
    #     url = self.url_externe_locaties % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url)
    #     self.assert_is_redirect_not_plein(resp)
    #
    #     loc = self.ver2.locatie_set.first()
    #     loc.plaats = "Dit moet je bekijken!"
    #     loc.save()
    #
    #     # bekijk de accommodatie details
    #     url = self.url_locatie % self.ver2.ver_nr
    #     with self.assert_max_queries(20):
    #         resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)  # 200 = OK
    #     self.assert_html_ok(resp)
    #
    #     self.assertContains(resp, "Dit moet je bekijken!")
    #     self.assertNotContains(resp, "Wil je niet zien!")
    #
    #     # verwijder de externe locatie
    #     self.assertTrue(loc.zichtbaar, True)
    #     url = self.url_externe_locatie_details % (self.ver2.ver_nr, loc.pk)
    #     with self.assert_max_queries(20):
    #         resp = self.client.post(url, {'verwijder': 'zekers'})
    #     self.assert_is_redirect_not_plein(resp)
    #     loc = Locatie.objects.get(pk=loc.pk)
    #     self.assertFalse(loc.zichtbaar, False)
    #
# end of file
