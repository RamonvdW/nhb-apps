# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie, maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Wedstrijden.models import WedstrijdLocatie
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestVerenigingAccommodatie(E2EHelpers, TestCase):

    """ Tests voor de Verenigingen applicatie, ondersteuning WedstrijdLocatie """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BB aan, nodig om de competitie aan te maken
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

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
        ver.nhb_nr = 1000
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
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = 1001
        ver.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver2 = ver

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak een locatie aan
        loc = WedstrijdLocatie()
        loc.adres = 'Kleine baan'
        loc.save()
        loc.verenigingen.add(ver)
        self.loc2 = loc

        # maak het lid aan dat HWL wordt
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

        self.account_hwl = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        lid.account = self.account_hwl
        lid.save()
        self.nhblid_100001 = lid

        # maak het lid aan dat SEC wordt
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Secretaris"
        lid.email = "rdesecretaris@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        self.account_sec = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        lid.account = self.account_sec
        lid.save()
        self.nhblid_100002 = lid

        self.url_lijst = '/vereniging/accommodaties/lijst/'
        self.url_accommodatie_details = '/vereniging/accommodaties/details/%s/%s/'       # <locatie_pk>, <vereniging_pk>
        self.url_accommodatie_vereniging = '/vereniging/accommodatie-details/%s/%s/'     # <locatie_pk>, <vereniging_pk>

    def test_anon(self):
        # anon
        self.e2e_logout()
        resp = self.client.get(self.url_lijst)
        self.assert_is_redirect(resp, '/plein/')

        url = self.url_accommodatie_details % (self.loc1.pk, self.nhbver1.pk)
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_bb(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # grote lijst - alle locaties
        resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_lijst)

        # specifieke locatie
        url = self.url_accommodatie_details % (self.loc1.pk, self.nhbver1.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # niet bestaande locatie
        url = self.url_accommodatie_details % (999999, self.nhbver1.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # vereniging die niet bij de locatie hoort
        url = self.url_accommodatie_details % (self.loc1.pk, 999999)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

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
        resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))
        # TODO: check alleen rayon

        # details van een vereniging binnen de rayon
        url = self.url_accommodatie_details % (self.loc2.pk, self.nhbver2.pk)
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
        resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))
        # TODO: check alleen regio

        # details van een vereniging binnen de regio
        url = self.url_accommodatie_details % (self.loc2.pk, self.nhbver2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # details van een vereniging buiten de regio
        url = self.url_accommodatie_details % (self.loc1.pk, self.nhbver1.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # wijziging aanbrengen
        url = self.url_accommodatie_details % (self.loc2.pk, self.nhbver2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # probeer een wijziging te doen
        resp = self.client.post(url, {'baan_type': 'X',
                                      'banen_18m': 1,
                                      'banen_25m': 0,
                                      'max_dt': 3,
                                      'notities': 'hoi'})
        self.assert_is_redirect(resp, self.url_lijst)
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'X')
        self.assertEqual(loc2.banen_18m, 1)
        self.assertEqual(loc2.banen_25m, 0)
        self.assertEqual(loc2.max_dt_per_baan, 3)
        self.assertEqual(loc2.notities, 'hoi')

        # doe een niet-wijziging voor de coverage
        resp = self.client.post(url, {'baan_type': 'X',
                                      'banen_18m': 1,
                                      'banen_25m': 0,
                                      'max_dt': 3,
                                      'notities': 'hoi'})
        self.assert_is_redirect(resp, self.url_lijst)
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'X')
        self.assertEqual(loc2.banen_18m, 1)
        self.assertEqual(loc2.banen_25m, 0)
        self.assertEqual(loc2.max_dt_per_baan, 3)
        self.assertEqual(loc2.notities, 'hoi')

    def test_hwl(self):
        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # HWL krijgt dezelfde lijst als de RCL
        resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))
        # TODO: check alleen regio

        # check accommodatie detail pagina
        url = self.url_accommodatie_details % (self.loc2.pk, self.nhbver2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        # check dat de HWL de opslaan-knop aangeboden krijgt
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(url in urls)                                    # opslaan url
        self.assertTrue('/vereniging/accommodaties/lijst/' in urls)     # terug url

        # check the specifieke accommodatie pagina voor de HWL, met andere terug url
        url = self.url_accommodatie_vereniging % (self.loc2.pk, self.nhbver2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        # check dat de HWL de opslaan-knop aangeboden krijgt
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(url in urls)                # opslaan url
        self.assertTrue('/vereniging/' in urls)     # terug url

        # probeer een wijziging te doen
        resp = self.client.post(url, {'baan_type': 'O',
                                      'banen_18m': 5,
                                      'banen_25m': 6,
                                      'max_dt': 3,
                                      'notities': 'dit is een test'})
        self.assert_is_redirect(resp, '/vereniging/')       # stuur HWL terug naar vereniging pagina
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'O')
        self.assertEqual(loc2.banen_18m, 5)
        self.assertEqual(loc2.banen_25m, 6)
        self.assertEqual(loc2.max_dt_per_baan, 3)
        self.assertEqual(loc2.notities, 'dit is een test')
        resp = self.client.get(url)
        self.assertContains(resp, 'Volledig overdekt')

        resp = self.client.post(url, {'baan_type': 'H',
                                      'banen_18m': 5,
                                      'banen_25m': 6,
                                      'max_dt': 3,
                                      'notities': 'dit is een test'})
        self.assert_is_redirect(resp, '/vereniging/')       # stuur HWL terug naar vereniging pagina
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'H')
        resp = self.client.get(url)
        self.assertContains(resp, 'Half overdekt')

        resp = self.client.post(url, {'baan_type': 'X',
                                      'banen_18m': 5,
                                      'banen_25m': 6,
                                      'max_dt': 3,
                                      'notities': 'dit is een test'})
        loc2 = WedstrijdLocatie.objects.get(pk=self.loc2.pk)
        self.assertEqual(loc2.baan_type, 'X')

        # probeer met illegale waarden
        resp = self.client.post(url, {'baan_type': 'O',
                                      'banen_18m': 40,
                                      'banen_25m': 6,
                                      'max_dt': 3})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(url, {'baan_type': 'O',
                                      'banen_18m': 4,
                                      'banen_25m': 40,
                                      'max_dt': 3})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(url, {'baan_type': 'O',
                                      'banen_18m': 4,
                                      'banen_25m': 4,
                                      'max_dt': 2})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(url, {'baan_type': 'O',
                                      'banen_18m': 4,
                                      'banen_25m': 4,
                                      'max_dt': 5})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        resp = self.client.post(url, {'baan_type': 'y',
                                      'banen_18m': 4,
                                      'banen_25m': 4,
                                      'max_dt': 4})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # illegale location_pk
        url = self.url_accommodatie_vereniging % (999999, 888888)
        resp = self.client.post(url, {'baan_type': 'O',
                                      'banen_18m': 4,
                                      'banen_25m': 4,
                                      'max_dt': 4})
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_wl(self):
        # login als HWL van ver2 op loc2
        # en wordt daarna WL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # WL mag de hele lijst met verenigingen niet ophalen
        resp = self.client.get(self.url_lijst)
        self.assert_is_redirect(resp, '/plein/')

        # check accommodatie detail pagina
        url = self.url_accommodatie_details % (self.loc2.pk, self.nhbver2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        # check dat de WL de opslaan-knop NIET aangeboden krijgt
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(url not in urls)        # opslaan url moet ontbreken

    def test_sec(self):
        # login als SEC van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # SEC krijgt dezelfde lijst als de RCL?
        resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

        # check accommodatie detail pagina
        url = self.url_accommodatie_details % (self.loc2.pk, self.nhbver2.pk)
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
        url = self.url_accommodatie_details % (self.loc1.pk, self.nhbver1.pk)
        resp = self.client.post(url, {'baan_type': 'H',
                                      'banen_18m': 5,
                                      'banen_25m': 6,
                                      'max_dt': 3,
                                      'notities': 'dit is een test'})
        self.assertEqual(resp.status_code, 404)

        # geef een inconsistente locatie - vereniging
        url = self.url_accommodatie_details % (self.loc1.pk, self.nhbver2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_gedeelde_locatie(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak een locatie aan die door twee verenigingen gedeeld wordt
        loc = WedstrijdLocatie()
        loc.save()
        loc.verenigingen.add(self.nhbver1)
        loc.verenigingen.add(self.nhbver2)

        # haal de details op
        url = self.url_accommodatie_details % (loc.pk, self.nhbver1.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # haal de details op
        url = self.url_accommodatie_details % (loc.pk, self.nhbver2.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/accommodatie-details.dtl', 'plein/site_layout.dtl'))

# end of file
