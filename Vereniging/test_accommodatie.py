# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie, maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Sporter.models import Sporter, Secretaris
from Wedstrijden.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingAccommodatie(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, functie Accommodaties """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie')

    url_lijst = '/vereniging/accommodaties/lijst/'
    url_accommodatie_details = '/vereniging/accommodaties/details/%s/'           # vereniging_pk
    url_accommodatie_vereniging = '/vereniging/accommodatie-details/%s/'         # vereniging_pk
    url_externe_locaties = '/vereniging/externe-locaties/%s/'                    # vereniging_pk
    url_externe_locatie_details = '/vereniging/externe-locaties/%s/details/%s/'  # vereniging_pk, locatie_pk
    url_geen_beheerders = '/vereniging/contact-geen-beheerders/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        rayon_3 = NhbRayon.objects.get(rayon_nr=3)
        regio_111 = NhbRegio.objects.get(regio_nr=111)
        regio_101 = NhbRegio.objects.get(regio_nr=101)

        # RKO rol
        self.account_rko = self.e2e_create_account('rko', 'rko@test.com', 'RKO', accepteer_vhpg=True)
        self.functie_rko3 = Functie.objects.filter(rol="RKO", nhb_rayon=rayon_3)[0]
        self.functie_rko3.accounts.add(self.account_rko)

        # RCL rol
        self.account_rcl = self.e2e_create_account('rcl', 'rcl@test.com', 'RCL', accepteer_vhpg=True)
        self.functie_rcl111 = Functie.objects.filter(rol="RCL", nhb_regio=regio_111)[0]
        self.functie_rcl111.accounts.add(self.account_rcl)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Noordelijke Club"
        ver.ver_nr = 1000
        ver.regio = regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        # maak een locatie aan
        loc = WedstrijdLocatie()
        loc.adres = 'Grote baan'
        loc.save()
        loc.verenigingen.add(ver)
        self.loc1 = loc

        # maak de SEC, HWL en WL functies aan voor deze vereniging
        for rol in ('SEC', 'HWL', 'WL'):
            tmp_func = maak_functie(rol + " nhbver1", rol)
            tmp_func.nhb_ver = ver
            tmp_func.save()
        # for

        # maak de HWL functie
        self.functie_hwl1 = maak_functie("HWL test 1", "HWL")
        self.functie_hwl1.nhb_ver = self.nhbver1
        self.functie_hwl1.save()

        self.account_hwl1 = self.e2e_create_account('hwl1', 'hwl1@nhb.test', 'HWL', accepteer_vhpg=True)
        self.functie_hwl1.accounts.add(self.account_hwl1)

        # maak de WL functie
        self.functie_wl1 = maak_functie("WL test 1", "WL")
        self.functie_wl1.nhb_ver = self.nhbver1
        self.functie_wl1.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = 1001
        ver.regio = regio_111
        ver.save()
        self.nhbver2 = ver

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = self.nhbver2
        self.functie_sec.save()

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = self.nhbver2
        self.functie_hwl.save()

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = self.nhbver2
        self.functie_wl.save()

        # maak een locatie aan
        loc = WedstrijdLocatie()
        loc.adres = 'Kleine baan'
        loc.save()
        loc.verenigingen.add(ver)
        self.loc2 = loc

        # maak het lid aan dat HWL wordt
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100001 = sporter

        # maak het lid aan dat SEC wordt
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Secretaris"
        sporter.email = "rdesecretaris@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        sporter.account = self.account_sec
        sporter.save()
        self.sporter_100002 = sporter

        Secretaris(vereniging=ver, sporter=sporter).save()

    def test_anon(self):
        # anon
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assert403(resp)

        url = self.url_accommodatie_details % self.nhbver1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_bb(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # grote lijst - alle locaties
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_lijst)

        # specifieke locatie
        url = self.url_accommodatie_details % self.nhbver1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # vereniging die niet bij de locatie hoort
        url = self.url_accommodatie_details % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # coverage
        self.assertTrue(str(self.loc1) != "")
        self.loc2.zichtbaar = False
        self.assertTrue(str(self.loc2) != "")

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_rko(self):
        # login als RKO
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(self.functie_rko3)
        self.e2e_check_rol('RKO')

        # grote lijst - alleen binnen het rayon
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))
        # TODO: check alleen rayon

        # details van een vereniging binnen de rayon
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

    def test_rcl(self):
        # login als RCL
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl111)
        self.e2e_check_rol('RCL')

        # grote lijst - alleen binnen de regio
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, '[1001]')         # in regio 111
        self.assertNotContains(resp, '[1000]')      # in regio 101

        # details van een vereniging binnen de regio
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # details van een vereniging buiten de regio
        url = self.url_accommodatie_details % self.nhbver1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # wijziging aanbrengen
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # probeer een wijziging te doen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'X',
                                          'banen_18m': 1,
                                          'banen_25m': 0,
                                          #'max_dt': 3,     # FUTURE: clean out all max_dt
                                          'notities': 'hoi'})
        self.assert_is_redirect(resp, self.url_lijst)
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'X')
        self.assertEqual(loc2.banen_18m, 1)
        self.assertEqual(loc2.banen_25m, 0)
        #self.assertEqual(loc2.max_dt_per_baan, 3)
        self.assertEqual(loc2.notities, 'hoi')

        # doe een niet-wijziging voor de coverage
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'X',
                                          'banen_18m': 1,
                                          'banen_25m': 0,
                                          'max_sporters_18m': 4,
                                          'max_sporters_25m': 0,
                                          #'max_dt': 3,
                                          'notities': 'hoi'})
        self.assert_is_redirect(resp, self.url_lijst)
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'X')
        self.assertEqual(loc2.banen_18m, 1)
        self.assertEqual(loc2.banen_25m, 0)
        #self.assertEqual(loc2.max_dt_per_baan, 3)
        self.assertEqual(loc2.max_sporters_18m, 4)
        self.assertEqual(loc2.max_sporters_25m, 0)
        self.assertEqual(loc2.notities, 'hoi')

    def test_hwl(self):
        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # HWL krijgt dezelfde lijst als de RCL
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, '[1001]')         # in regio 111
        self.assertNotContains(resp, '[1000]')      # in regio 101

        # check accommodatie detail pagina
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        # check dat de HWL de opslaan-knop aangeboden krijgt
        self.assertContains(resp, 'Wijzigingen opslaan')

        # check the specifieke accommodatie pagina voor de HWL, met andere terug url
        url = self.url_accommodatie_vereniging % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        # check dat de HWL de opslaan-knop aangeboden krijgt
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(url in urls)                # opslaan url
        self.assertTrue('/vereniging/' in urls)     # terug url

        # probeer een wijziging te doen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'O',
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          'max_sporters_18m': 18,
                                          'max_sporters_25m': 25,
                                          'max_dt': 3,
                                          'notities': 'dit is een test'})
        self.assert_is_redirect(resp, '/vereniging/')       # stuur HWL terug naar vereniging pagina
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'O')
        self.assertEqual(loc2.banen_18m, 5)
        self.assertEqual(loc2.banen_25m, 6)
        self.assertEqual(loc2.max_sporters_18m, 18)
        self.assertEqual(loc2.max_sporters_25m, 25)
        #self.assertEqual(loc2.max_dt_per_baan, 3)
        self.assertEqual(loc2.notities, 'dit is een test')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertContains(resp, 'Volledig overdekt')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'H',
                                          'banen_18m': 0,
                                          'banen_25m': 0,
                                          #'max_dt': 3,
                                          'notities': 'dit is een test'})
        self.assert_is_redirect(resp, '/vereniging/')       # stuur HWL terug naar vereniging pagina
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'H')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertContains(resp, 'Half overdekt')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'X',
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          #'max_dt': 3,
                                          'notities': 'dit is een test'})
        self.assertEqual(resp.status_code, 302)     # 302 = redirect = success
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'X')

        # probeer met illegale waarden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'O',
                                          'banen_18m': 40,
                                          'banen_25m': 6,
                                          #'max_dt': 3
                                          })
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'O',
                                          'banen_18m': 4,
                                          'banen_25m': 40,
                                          #'max_dt': 3
                                          })
        self.assert404(resp)     # 404 = Not found

        #with self.assert_max_queries(20):
        #    resp = self.client.post(url, {'baan_type': 'O',
        #                                  'banen_18m': 4,
        #                                  'banen_25m': 4,
        #                                  'max_dt': 2})
        #self.assert404(resp)     # 404 = Not found

        #with self.assert_max_queries(20):
        #    resp = self.client.post(url, {'baan_type': 'O',
        #                                  'banen_18m': 4,
        #                                  'banen_25m': 4,
        #                                  'max_dt': 5
        #                                  })
        #self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'y',
                                          'banen_18m': 4,
                                          'banen_25m': 4,
                                          #'max_dt': 4
                                          })
        self.assert404(resp)     # 404 = Not found

        # illegale location_pk
        url = self.url_accommodatie_vereniging % 888888
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'O',
                                          'banen_18m': 4,
                                          'banen_25m': 4,
                                          #'max_dt': 4
                                          })
        self.assert404(resp)     # 404 = Not found

    def test_wl(self):
        # login als HWL van ver2 op loc2
        # en wordt daarna WL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # WL mag de hele lijst met verenigingen niet ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assert403(resp)

        # haal de SEC uit zijn functie zodat deze direct uit de vereniging gehaald wordt
        self.functie_sec.accounts.clear()

        # check accommodatie detail pagina
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # check dat de WL de opslaan-knop NIET aangeboden krijgt
        self.assertNotContains(resp, 'Wijzigingen opslaan')

        # nog een keer, voor een vereniging zonder secretaris
        self.nhbver2.secretaris_lid = None
        self.nhbver2.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # probeer een wijziging te doen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'O',
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          #'max_dt': 3,
                                          'notities': 'dit is een test'})
        self.assert403(resp)

        # zet het aantal banen op 0,0
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'H',
                                          'banen_18m': 1,
                                          'banen_25m': 0,
                                          #'max_dt': 3,
                                          'notities': 'dit is een test'})
        # haal op als WL, dan krijg je read-only zonder DT
        self.e2e_wissel_naar_functie(self.functie_wl)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

    def test_sec(self):
        # login als SEC van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # SEC krijgt dezelfde lijst als de RCL?
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

        # check accommodatie detail pagina
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        # check dat de HWL de opslaan-knop aangeboden krijgt
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(url in urls)                                    # opslaan url
        self.assertTrue('/vereniging/accommodaties/lijst/' in urls)     # terug url

    def test_bad(self):
        # login als SEC van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # probeer van andere vereniging te wijzigen
        url = self.url_accommodatie_details % self.nhbver1.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'H',
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          #'max_dt': 3,
                                          'notities': 'dit is een test'})
        self.assert403(resp)

    def test_gedeelde_locatie(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak een locatie aan die door twee verenigingen gedeeld wordt
        loc = WedstrijdLocatie()
        loc.save()
        loc.verenigingen.add(self.nhbver1)
        loc.verenigingen.add(self.nhbver2)

        # haal de details op
        url = self.url_accommodatie_details % self.nhbver1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # haal de details op
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

    def test_cluster(self):
        # stop de vereniging in een cluster
        cluster = NhbCluster.objects.filter(regio=self.nhbver2.regio, gebruik='18').all()[0]
        self.nhbver2.clusters.add(cluster)
        cluster = NhbCluster.objects.filter(regio=self.nhbver2.regio, gebruik='25').all()[2]
        self.nhbver2.clusters.add(cluster)

        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # accommodaties lijst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

        # accommodatie details
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        # check dat de HWL de opslaan-knop aangeboden krijgt
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(url in urls)                                    # opslaan url
        self.assertTrue('/vereniging/accommodaties/lijst/' in urls)     # terug url

        # accommodaties lijst corner case
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

    def test_binnen_en_buiten_locatie(self):
        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_accommodatie_vereniging % self.nhbver2.pk

        # maak de buitenlocatie aan
        self.assertEqual(1, self.nhbver2.wedstrijdlocatie_set.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'maak_buiten_locatie': 'on'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(2, self.nhbver2.wedstrijdlocatie_set.count())
        buiten_locatie = self.nhbver2.wedstrijdlocatie_set.filter(baan_type='B').all()[0]

        # maak de buiten locatie nog een keer aan
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'maak_buiten_locatie': 'on'})
        # is geen probleem - dan wordt de al bestaande buiten locatie op zichtbaar=True gezet
        self.assert_is_redirect(resp, url)
        self.assertEqual(2, self.nhbver2.wedstrijdlocatie_set.count())

        # haal het scherm op met de buiten locatie erin
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # pas wat parameters aan
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'H',
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          #'max_dt': 3,
                                          'notities': 'dit is een test',
                                          'buiten_banen': 50,
                                          'buiten_max_afstand': 90,
                                          'buiten_notities': 'dit is een buiten test'})
        self.assert_is_redirect(resp, '/vereniging/')

        buiten_locatie = WedstrijdLocatie.objects.get(pk=buiten_locatie.pk)
        self.assertEqual(buiten_locatie.adres, 'Kleine baan')       # overgenomen van de binnenlocatie
        self.assertEqual(buiten_locatie.buiten_banen, 50)
        self.assertEqual(buiten_locatie.buiten_max_afstand, 90)
        self.assertEqual(buiten_locatie.notities, 'dit is een buiten test')

        # nog een keer opslaan zodat er geen wijzigingen zijn
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'H',
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          #'max_dt': 3,
                                          'notities': 'dit is een test',
                                          'buiten_banen': 50,
                                          'buiten_max_afstand': 90,
                                          'buiten_notities': 'dit is een buiten test'})
        self.assert_is_redirect(resp, '/vereniging/')

        # haal de lijst op, zodat we daar ook een buitenlocatie in hebben
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        self.assertTrue(buiten_locatie.zichtbaar)

        # verwijder de buitenlocatie
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_buitenbaan': 'ja'})
        self.assert_is_redirect_not_plein(resp)

        # nog een keer, via de alternatieve url
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_accommodatie_details % self.nhbver2.pk,
                                    {'verwijder_buitenbaan': 'ja'})
        self.assert_is_redirect_not_plein(resp)

        buiten_locatie = WedstrijdLocatie.objects.get(pk=buiten_locatie.pk)
        self.assertFalse(buiten_locatie.zichtbaar)

        # haal het scherm op zonder de buitenlocatie erin
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        # herstel buitenlocatie
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'maak_buiten_locatie': 'ja'})
        self.assert_is_redirect_not_plein(resp)

    def test_externe_locatie(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        url = self.url_externe_locaties % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        # controleer dat er geen knop is om een nieuwe locatie toe te voegen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

        # niet bestaande vereniging
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_externe_locaties % 999999)
        self.assert404(resp)

        # probeer een locatie toe te voegen
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_externe_locaties % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/externe-locaties.dtl', 'plein/site_layout.dtl'))
        # controleer dat er een knop is om een nieuwe locatie toe te voegen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [url])

        # voeg een locatie toe
        self.assertEqual(2, WedstrijdLocatie.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(3, WedstrijdLocatie.objects.count())
        locatie = WedstrijdLocatie.objects.get(baan_type='E')
        self.assertEqual(locatie.naam, '')

        # haal de niet-lege lijst met locaties op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(len(urls), 2)      # wijzig knop is erbij gekomen

        # probeer een locatie toe te voegen van een andere vereniging
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_externe_locaties % self.nhbver1.pk)
        self.assert403(resp)

        # hanteer de externe locatie in de lijst van alle verenigingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

    def test_wijzig_externe_locatie(self):
        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maak een externe locatie aan
        url = self.url_externe_locaties % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        locatie = WedstrijdLocatie.objects.get(baan_type='E')
        url = self.url_externe_locatie_details % (self.nhbver2.pk, locatie.pk)

        # haal de locatie details op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/externe-locatie-details.dtl', 'plein/site_layout.dtl'))

        # HWL mag de externe locatie details aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # HWL mag de externe locatie details aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_clout': 'on',
                                          'disc_veld': 'on',
                                          'disc_run': 1,
                                          'disc_3d': True,
                                          # indoor velden die niet meegenomen zullen worden
                                          'banen_18m': 1,
                                          'banen_25m': 1,
                                          #'max_dt': 3,
                                          # outdoor velden die niet meegenomen zullen worden
                                          'buiten_max_afstand': 99,
                                          'buiten_banen': 42,
                                          'notities': 'hoi\ntest\r\nmeer testen'})
        self.assert_is_redirect_not_plein(resp)

        locatie = WedstrijdLocatie.objects.get(pk=locatie.pk)
        self.assertEqual(locatie.naam, 'test naam')
        self.assertFalse(locatie.discipline_outdoor)
        self.assertFalse(locatie.discipline_indoor)
        self.assertTrue(locatie.discipline_clout)
        self.assertTrue(locatie.discipline_veld)
        self.assertTrue(locatie.discipline_run)
        self.assertTrue(locatie.discipline_3d)
        self.assertEqual(locatie.banen_18m, 0)
        self.assertEqual(locatie.banen_25m, 0)
        #self.assertEqual(locatie.max_dt_per_baan, 4)
        self.assertEqual(locatie.buiten_max_afstand, 99)
        self.assertEqual(locatie.buiten_banen, 42)
        self.assertIn('Langeboog 5\nBoogstad', locatie.adres)
        self.assertFalse(locatie.adres_uit_crm)
        self.assertIn('hoi\ntest\nmeer testen', locatie.notities)

        # maak er een outdoor locatie van
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_outdoor': 'on',
                                          'buiten_max_afstand': 190,
                                          'buiten_banen': 0})
        self.assert_is_redirect_not_plein(resp)

        locatie = WedstrijdLocatie.objects.get(pk=locatie.pk)
        self.assertTrue(locatie.discipline_outdoor)
        self.assertFalse(locatie.discipline_indoor)
        self.assertFalse(locatie.discipline_clout)
        self.assertFalse(locatie.discipline_veld)
        self.assertFalse(locatie.discipline_run)
        self.assertFalse(locatie.discipline_3d)
        self.assertEqual(locatie.buiten_max_afstand, 100)
        self.assertEqual(locatie.buiten_banen, 1)

        # no-change
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_outdoor': 'on',
                                          'buiten_max_afstand': 190,
                                          'buiten_banen': 0})
        self.assert_is_redirect_not_plein(resp)

        # bad values
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_outdoor': 'on',
                                          'buiten_max_afstand': 'xxx',
                                          'buiten_banen': 'xxx'})
        self.assert_is_redirect_not_plein(resp)

        # maak er een indoor locatie van
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_indoor': 'on',
                                          'banen_18m': 17,
                                          'banen_25m': 24,
                                          #'max_dt': '4'
                                          })
        self.assert_is_redirect_not_plein(resp)

        locatie = WedstrijdLocatie.objects.get(pk=locatie.pk)
        self.assertFalse(locatie.discipline_outdoor)
        self.assertTrue(locatie.discipline_indoor)
        self.assertEqual(locatie.banen_18m, 17)
        self.assertEqual(locatie.banen_25m, 24)

        # no change
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_indoor': 'on',
                                          'banen_18m': 17,
                                          'banen_25m': 24,
                                          #'max_dt': '4'
                                          })
        self.assert_is_redirect_not_plein(resp)

        # bad values
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_indoor': 'on',
                                          'banen_18m': 'xxx',
                                          'banen_25m': 'xxx',
                                          #'max_dt': 3
                                          })
        self.assert_is_redirect_not_plein(resp)

        # niet bestaande locatie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_externe_locatie_details % (self.nhbver2.pk, 999999))
        self.assert404(resp)

        # niet externe locatie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_externe_locatie_details % (self.nhbver2.pk, self.loc2.pk))
        self.assert404(resp)

        # niet bestaande vereniging
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_externe_locatie_details % (999999, locatie.pk))
        self.assert404(resp)

        # locatie van een andere vereniging
        self.loc1.baan_type = 'E'
        self.loc1.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_externe_locatie_details % (self.nhbver2.pk, self.loc1.pk))
        self.assert404(resp)

        # login als HWL van nhbver1
        self.e2e_login_and_pass_otp(self.account_hwl1)
        self.e2e_wissel_naar_functie(self.functie_hwl1)
        self.e2e_check_rol('HWL')

        # iedereen mag de locatie details ook ophalen, dus ook deze 'verkeerde HWL'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/externe-locatie-details.dtl', 'plein/site_layout.dtl'))

        # verkeerde HWL mag de externe locatie details niet aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # nog een poging met een niet-HWL functie
        self.e2e_wissel_naar_functie(self.functie_wl1)
        self.e2e_check_rol('WL')

        # WL mag de externe locatie details niet aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # koppel de locatie los
        locatie.verenigingen.clear()
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp)

    def test_externe_accommodatie(self):
        # accommodatie bestaat niet of heeft geen banen
        # functie wordt overgenomen door externe locatie
        loc = self.nhbver2.wedstrijdlocatie_set.all()[0]
        loc.plaats = "Wil je niet zien!"
        loc.save()

        # verwijder de accommodatie van de vereniging
        self.nhbver2.wedstrijdlocatie_set.clear()

        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maak een externe locatie aan
        url = self.url_externe_locaties % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        loc = self.nhbver2.wedstrijdlocatie_set.all()[0]
        loc.plaats = "Dit moet je bekijken!"
        loc.save()

        # bekijk de accommodatie details
        url = self.url_accommodatie_details % self.nhbver2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)

        self.assertContains(resp, "Dit moet je bekijken!")
        self.assertNotContains(resp, "Wil je niet zien!")

        # verwijder de externe locatie
        self.assertTrue(loc.zichtbaar, True)
        url = self.url_externe_locatie_details % (self.nhbver2.pk, loc.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder': 'zekers'})
        self.assert_is_redirect_not_plein(resp)
        loc = WedstrijdLocatie.objects.get(pk=loc.pk)
        self.assertFalse(loc.zichtbaar, False)

    def test_geen_beheerders(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak een extra vereniging aan zonder beheerders
        ver = NhbVereniging()
        ver.naam = "Extra Club"
        ver.ver_nr = 1099
        ver.regio = NhbRegio.objects.get(regio_nr=101)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak de SEC, HWL en WL functies aan voor deze vereniging
        for rol in ('SEC', 'HWL', 'WL'):
            tmp_func = maak_functie(rol + " nhbver 1099", rol)
            tmp_func.nhb_ver = ver
            tmp_func.save()
        # for

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_geen_beheerders)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/contact-geen-beheerders.dtl', 'plein/site_layout.dtl'))

        # probeer het met een andere rol
        self.e2e_wisselnaarrol_gebruiker()
        resp = self.client.get(self.url_geen_beheerders)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_geen_beheerders)

# end of file
