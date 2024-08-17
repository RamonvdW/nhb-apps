# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from Locatie.definities import BAAN_TYPE_EXTERN
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging, Secretaris
import datetime


class TestLocatieExterneLocatie(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, functie Externe Locatie """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie')

    url_locaties = '/vereniging/locatie/%s/'                              # ver_nr
    url_externe_locaties = '/vereniging/locatie/%s/extern/'               # ver_nr
    url_externe_locatie_details = '/vereniging/locatie/%s/extern/%s/'     # ver_nr, locatie_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        rayon_3 = Rayon.objects.get(rayon_nr=3)
        regio_111 = Regio.objects.get(regio_nr=111)
        regio_101 = Regio.objects.get(regio_nr=101)

        # RKO rol
        self.account_rko = self.e2e_create_account('rko', 'rko@test.com', 'RKO', accepteer_vhpg=True)
        self.functie_rko3 = Functie.objects.filter(rol="RKO", rayon=rayon_3)[0]
        self.functie_rko3.accounts.add(self.account_rko)

        # RCL rol
        self.account_rcl = self.e2e_create_account('rcl', 'rcl@test.com', 'RCL', accepteer_vhpg=True)
        self.functie_rcl111 = Functie.objects.filter(rol="RCL", regio=regio_111)[0]
        self.functie_rcl111.accounts.add(self.account_rcl)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Noordelijke Club",
                    ver_nr=1000,
                    regio=regio_101)
        ver.save()
        self.ver1 = ver

        # maak een locatie aan
        loc = WedstrijdLocatie(
                    adres='Grote baan')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc1 = loc

        # maak de SEC, HWL en WL functies aan voor deze vereniging
        for rol in ('SEC', 'HWL', 'WL'):
            tmp_func = maak_functie(rol + " ver1", rol)
            tmp_func.vereniging = ver
            tmp_func.save()
        # for

        # maak de HWL functie
        self.functie_hwl1 = maak_functie("HWL test 1", "HWL")
        self.functie_hwl1.vereniging = self.ver1
        self.functie_hwl1.save()

        self.account_hwl1 = self.e2e_create_account('hwl1', 'hwl1@test.not', 'HWL', accepteer_vhpg=True)
        self.functie_hwl1.accounts.add(self.account_hwl1)

        # maak de WL functie
        self.functie_wl1 = maak_functie("WL test 1", "WL")
        self.functie_wl1.vereniging = self.ver1
        self.functie_wl1.save()

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1001,
                    regio=regio_111)
        ver.save()
        self.ver2 = ver

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = self.ver2
        self.functie_sec.save()

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = self.ver2
        self.functie_hwl.save()

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = self.ver2
        self.functie_wl.save()

        # maak een locatie aan
        loc = WedstrijdLocatie(
                    adres='Kleine baan')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc2 = loc

        # maak het lid aan dat HWL wordt
        sporter = Sporter(
                        lid_nr=100001,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Tester",
                        email="rdetester@gmail.not",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver)
        sporter.save()

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100001 = sporter

        # maak het lid aan dat SEC wordt
        sporter = Sporter(
                        lid_nr=100002,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Secretaris",
                        email="rdesecretaris@gmail.not",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver)
        sporter.save()

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        sporter.account = self.account_sec
        sporter.save()
        self.sporter_100002 = sporter

        sec = Secretaris(vereniging=ver)
        sec.save()
        sec.sporters.add(sporter)
        self.sec = sec

    def test_externe_locatie(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        url = self.url_externe_locaties % self.ver2.ver_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/externe-locaties.dtl', 'plein/site_layout.dtl'))
        # controleer dat er geen knop is om een nieuwe locatie toe te voegen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])

        # niet bestaande vereniging
        resp = self.client.get(self.url_externe_locaties % 999999)
        self.assert404(resp, 'Vereniging niet gevonden')

        # probeer een locatie toe te voegen
        resp = self.client.post(url)
        self.assert403(resp)

        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_externe_locaties % self.ver2.ver_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/externe-locaties.dtl', 'plein/site_layout.dtl'))
        # controleer dat er een knop is om een nieuwe locatie toe te voegen
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [url])

        # voeg een locatie toe
        self.assertEqual(2, WedstrijdLocatie.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(3, WedstrijdLocatie.objects.count())
        locatie = WedstrijdLocatie.objects.get(baan_type=BAAN_TYPE_EXTERN)
        self.assertEqual(locatie.naam, '')

        # haal de niet-lege lijst met locaties op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/externe-locaties.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(len(urls), 2)      # wijzig-knop is erbij gekomen

        # haal de lijst met locaties op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/externe-locaties.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(len(urls), 2)      # wijzig-knop is erbij gekomen

        # probeer een locatie toe te voegen van een andere vereniging
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_externe_locaties % self.ver1.ver_nr)
        self.assert403(resp)

    def test_wijzig_externe_locatie(self):
        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maak een externe locatie aan
        url = self.url_externe_locaties % self.ver2.ver_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        locatie = WedstrijdLocatie.objects.get(baan_type=BAAN_TYPE_EXTERN)
        url = self.url_externe_locatie_details % (self.ver2.ver_nr, locatie.pk)

        # haal de locatie details op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/externe-locatie-details.dtl', 'plein/site_layout.dtl'))

        # HWL mag de externe locatie details aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # HWL mag de externe locatie details aanpassen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'plaats': 'Boogstad',
                                          'disc_clout': 'on',
                                          'disc_veld': 'on',
                                          'disc_run': 1,
                                          'disc_3d': True,
                                          # indoor velden die niet meegenomen zullen worden
                                          'banen_18m': 1,
                                          'banen_25m': 1,
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
        self.assertEqual(locatie.buiten_max_afstand, 99)
        self.assertEqual(locatie.buiten_banen, 42)
        self.assertIn('Langeboog 5\nBoogstad', locatie.adres)
        self.assertEqual(locatie.plaats, 'Boogstad')
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
                                          'max_sporters_18m': 18,
                                          'max_sporters_25m': 25,
                                          'banen_18m': 17,
                                          'banen_25m': 24})
        self.assert_is_redirect_not_plein(resp)

        locatie = WedstrijdLocatie.objects.get(pk=locatie.pk)
        self.assertFalse(locatie.discipline_outdoor)
        self.assertTrue(locatie.discipline_indoor)
        self.assertEqual(locatie.banen_18m, 17)
        self.assertEqual(locatie.banen_25m, 24)
        self.assertEqual(locatie.max_sporters_18m, 18)
        self.assertEqual(locatie.max_sporters_25m, 25)

        # no change
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_indoor': 'on',
                                          'banen_18m': 17,
                                          'banen_25m': 24})
        self.assert_is_redirect_not_plein(resp)

        # bad values
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'naam': 'test naam',
                                          'adres': 'Langeboog 5\r\nBoogstad',
                                          'disc_indoor': 'on',
                                          'max_sporters_18m': 'xxx',
                                          'max_sporters_25m': 'xxx',
                                          'banen_18m': 'xxx',
                                          'banen_25m': 'xxx'})
        self.assert_is_redirect_not_plein(resp)

        # niet bestaande locatie
        resp = self.client.get(self.url_externe_locatie_details % (self.ver2.ver_nr, 999999))
        self.assert404(resp, 'Locatie bestaat niet')

        # niet externe locatie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_externe_locatie_details % (self.ver2.ver_nr, self.loc2.pk))
        self.assert404(resp, 'Locatie bestaat niet')

        # niet bestaande vereniging
        resp = self.client.get(self.url_externe_locatie_details % (999999, locatie.pk))
        self.assert404(resp, 'Vereniging niet gevonden')

        # locatie van een andere vereniging
        self.loc1.baan_type = BAAN_TYPE_EXTERN
        self.loc1.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_externe_locatie_details % (self.ver2.ver_nr, self.loc1.pk))
        self.assert404(resp, 'Locatie hoort niet bij de vereniging')

        # login als HWL van ver1
        self.e2e_login_and_pass_otp(self.account_hwl1)
        self.e2e_wissel_naar_functie(self.functie_hwl1)
        self.e2e_check_rol('HWL')

        # iedereen mag de locatie details ook ophalen, dus ook deze 'verkeerde HWL'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/externe-locatie-details.dtl', 'plein/site_layout.dtl'))

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
        self.assert404(resp, 'Locatie hoort niet bij de vereniging')

    def test_verwijder(self):
        # login als HWL van ver2 op loc2
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maak een externe locatie aan
        url = self.url_externe_locaties % self.ver2.ver_nr
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        locatie = WedstrijdLocatie.objects.get(baan_type=BAAN_TYPE_EXTERN)
        self.assertTrue(locatie.zichtbaar)

        # verwijder de externe locatie
        url2 = self.url_externe_locatie_details % (self.ver2.ver_nr, locatie.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url2, {'verwijder': 'ja'})
        self.assert_is_redirect(resp, url)

        locatie.refresh_from_db()
        self.assertFalse(locatie.zichtbaar)

        # haal de lijst met locaties op
        url = self.url_locaties % self.ver2.ver_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))

# end of file
