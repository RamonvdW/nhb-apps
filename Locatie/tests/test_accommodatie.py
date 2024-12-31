# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Cluster
from Locatie.definities import (BAAN_TYPE_ONBEKEND, BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT, BAAN_TYPE_BINNEN_BUITEN,
                                BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN)
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging, Secretaris
import datetime


class TestLocatieAccommodatie(E2EHelpers, TestCase):

    """ tests voor de Locatie applicatie, functie Accommodaties """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie')

    url_ver_overzicht = '/vereniging/'
    url_locaties = '/vereniging/locatie/%s/'   # ver_nr
    url_login = '/account/login/'

    lange_tekst = "Dit is een heel verhaal van minimaal 200 tekens zodat we de limiet van 500 tekens bereiken " + \
                  "bij het schrijven naar het logboek. Het is namelijk een keer voorgekomen dat de notitie " + \
                  "niet opgeslagen kon worden omdat deze te lang is. In het logboek schrijven we de oude en " + \
                  "de nieuwe tekst."

    testdata = None
    regio = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.regio = Regio.objects.get(regio_nr=101)

    def _maak_vereniging_en_functies(self, ver_nr, naam):
        # maak een test vereniging
        ver = Vereniging(
                    ver_nr=ver_nr,
                    naam=naam,
                    regio=self.regio)
        ver.save()

        # maak de SEC, HWL en WL functies aan voor deze vereniging
        for rol in ('SEC', 'HWL', 'WL'):
            tmp_func = maak_functie("%s %s" % (rol, ver_nr), rol)
            tmp_func.vereniging = ver
            tmp_func.save()
        # for

        return ver

    @staticmethod
    def _maak_accommodatie(ver, baan_type=BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT):
        # maak een locatie aan
        loc = WedstrijdLocatie(adres='Grote baan', baan_type=baan_type)
        loc.save()
        loc.verenigingen.add(ver)
        return loc

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        self.ver1 = self._maak_vereniging_en_functies(1000, "Noordelijke club")

        self.functie_sec = Functie.objects.get(beschrijving='SEC 1000')
        self.account_sec = self.e2e_create_account('sec_ver1', 'sec_ver1@test.not', 'SEC', accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        self.functie_hwl = Functie.objects.get(beschrijving='HWL 1000')
        self.account_hwl = self.e2e_create_account('hwl_ver1', 'hwl_ver1@test.not', 'HWL', accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        self.functie_wl = Functie.objects.get(beschrijving='WL 1000')
        self.account_wl = self.e2e_create_account('wl_ver1', 'wl_ver1@test.not', 'WL', accepteer_vhpg=True)
        self.functie_wl.accounts.add(self.account_wl)

        # maak een cluster aan
        self.cluster = Cluster(
                            regio=self.ver1.regio,
                            letter='Y',
                            naam="Overdekte locaties",
                            gebruik='18')
        self.cluster.save()

        # maak het lid aan dat SEC wordt volgens het CRM
        self.sec = Secretaris(vereniging=self.ver1)
        self.sec.save()
        sporter = Sporter(
                        lid_nr=100002,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Secretaris",
                        email="rdesecretaris@gmail.not",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=self.ver1)
        sporter.save()
        self.sec.sporters.add(sporter)

    def test_geen_toegang(self):
        # anon
        self.e2e_logout()

        url = self.url_locaties % self.ver1.ver_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # specifieke locatie
        url = self.url_locaties % self.ver1.ver_nr
        resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

    def test_hwl(self):
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol("HWL")

        url = self.url_locaties % self.ver1.ver_nr

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # stop de vereniging in een cluster
        self.ver1.clusters.add(self.cluster)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])      # geen wijzig knop omdat er geen binnen- of buitenbaan is

        # maak de accommodatie aan
        loc1 = self._maak_accommodatie(self.ver1)
        loc1.adres = 'Adres 123\r\n1234XX Plaats'
        loc1.plaats = 'Grote plas'
        loc1.adres_uit_crm = True
        loc1.save(update_fields=['adres', 'plaats', 'adres_uit_crm'])

        self.assertEqual(loc1.adres_oneliner(), 'Adres 123, 1234XX Plaats')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [url, url])      # nu wel een opslaan knop + maak buitenbaan knop

        # maak de buitenbaan aan
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'maak_buiten_locatie': 'graag'})
        self.assert_is_redirect(resp, url)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [url, url])      # nu wel een opslaan knop + verwijder buitenbaan knop

        loc1.zichtbaar = False
        loc1.save(update_fields=['zichtbaar'])

        loc2 = self.ver1.wedstrijdlocatie_set.filter(baan_type=BAAN_TYPE_BUITEN).first()
        self.assertEqual(loc2.naam, '')
        self.assertTrue(loc2.zichtbaar)
        self.assertFalse(loc2.adres_uit_crm)        # vrijheid om te wijzigen

        # verwijder de buitenbaan (eigenlijk: maak onzichtbaar)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_buitenbaan': 'graag'})
        self.assert_is_redirect(resp, url)

        loc2 = WedstrijdLocatie.objects.get(pk=loc2.pk)
        self.assertFalse(loc2.zichtbaar)
        loc2.discipline_25m1pijl = True     # voor de str
        self.assertTrue(str(loc2) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [url, url])      # nu wel een opslaan knop + maak buitenbaan knop

        # maak de buitenbaan opnieuw aan (eigenlijk: maak weer zichtbaar)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'maak_buiten_locatie': 'graag'})
        self.assert_is_redirect(resp, url)
        loc2 = WedstrijdLocatie.objects.get(pk=loc2.pk)
        self.assertTrue(loc2.zichtbaar)

        # nog een keer (geen effect)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'maak_buiten_locatie': 'graag'})
        self.assert_is_redirect(resp, url)
        loc2 = WedstrijdLocatie.objects.get(pk=loc2.pk)
        self.assertTrue(loc2.zichtbaar)

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_sec(self):
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol("SEC")

        url = self.url_locaties % self.ver1.ver_nr

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # verwijder de buitenbaan, zonder dat deze bestaat
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_buitenbaan': 'graag'})
        self.assert_is_redirect(resp, url)

        # maak de buitenbaan aan, zonder dat er een binnen locatie is
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'maak_buiten_locatie': 'graag'})
        self.assert_is_redirect(resp, url)

        # post een wijziging zonder dat er een binnen- of buitenbaan is
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT})
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        # maak nog een vereniging
        ver2 = self._maak_vereniging_en_functies(1001, "Grote Club")
        url = self.url_locaties % ver2.ver_nr
        loc2 = self._maak_accommodatie(ver2)

        # "verkeerde" SEC mag wel inzien, maar niet wijzigen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertEqual(urls, [])      # geen wijzig knop, want verkeerde SEC

        # corner cases
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp, "Wijzigen niet toegestaan")

    def test_wl(self):
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol("WL")

        url = self.url_locaties % self.ver1.ver_nr

        # maak een externe locatie ana
        loc1 = self._maak_accommodatie(self.ver1, BAAN_TYPE_EXTERN)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # geen gekoppelde sec --> toont SEC uit CRM
        self.functie_sec.accounts.clear()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))

        # corner cases
        resp = self.client.get(self.url_locaties % 999999)
        self.assert404(resp, 'Geen valide vereniging')

        self.functie_hwl.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, "Rol ontbreekt")

        self.functie_sec.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, "Rol ontbreekt")

    def test_extern(self):
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol("SEC")

        # maak dit de vereniging voor gast-accounts
        self.ver1.is_extern = True
        self.ver1.save()
        url = self.url_locaties % self.ver1.ver_nr

        self.functie_hwl.delete()
        self.functie_wl.delete()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))

    def test_sporter(self):
        url = self.url_locaties % self.ver1.ver_nr

        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert_is_redirect(resp, self.url_login)

        self.e2e_login(self.account_wl)
        self.e2e_check_rol("sporter")
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, "Geen toegang")

    def test_wijzig_binnenbaan(self):
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol("HWL")

        url = self.url_locaties % self.ver1.ver_nr

        # maak de binnenbaan aan
        loc1 = self._maak_accommodatie(self.ver1)
        loc1.adres_uit_crm = True
        loc1.save(update_fields=['adres_uit_crm'])

        self.assertEqual(loc1.naam, '')
        self.assertTrue(loc1.zichtbaar)
        self.assertTrue(loc1.adres_uit_crm)
        self.assertFalse(loc1.discipline_25m1pijl)
        self.assertFalse(loc1.discipline_outdoor)
        self.assertFalse(loc1.discipline_indoor)
        self.assertFalse(loc1.discipline_clout)
        self.assertFalse(loc1.discipline_clout)
        self.assertFalse(loc1.discipline_veld)
        self.assertFalse(loc1.discipline_run)
        self.assertFalse(loc1.discipline_3d)

        # formulier niet compleet
        resp = self.client.post(url)
        self.assert404(resp, "Geen valide invoer")

        resp = self.client.post(url, {'baan_type': BAAN_TYPE_ONBEKEND})    # verplicht: type binnenbaan
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        # probeer een wijziging te doen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT,
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          'max_sporters_18m': 18,
                                          'max_sporters_25m': 25,
                                          'notities': 'dit is een test'})
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        loc1 = WedstrijdLocatie.objects.get(pk=loc1.pk)
        self.assertEqual(loc1.baan_type, 'O')
        self.assertEqual(loc1.banen_18m, 5)
        self.assertEqual(loc1.banen_25m, 6)
        self.assertEqual(loc1.max_sporters_18m, 18)
        self.assertEqual(loc1.max_sporters_25m, 25)
        self.assertEqual(loc1.notities, 'dit is een test')
        self.assertFalse(loc1.discipline_25m1pijl)
        self.assertFalse(loc1.discipline_outdoor)
        self.assertTrue(loc1.discipline_indoor)     # de enige in gebruik voor de indoor locatie
        self.assertFalse(loc1.discipline_clout)
        self.assertFalse(loc1.discipline_clout)
        self.assertFalse(loc1.discipline_veld)
        self.assertFalse(loc1.discipline_run)
        self.assertFalse(loc1.discipline_3d)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('locatie/accommodatie-details.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Volledig overdekt')

        # opslaan zonder wijzigingen (voor extra coverage)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT,
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          'max_sporters_18m': 18,
                                          'max_sporters_25m': 25,
                                          'notities': 'dit is een test'})
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': BAAN_TYPE_BINNEN_BUITEN,
                                          'banen_18m': 0,
                                          'banen_25m': 0,
                                          'max_sporters_18m': 18,       # no change
                                          'max_sporters_25m': 25,       # no change
                                          'notities': self.lange_tekst})
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        loc1 = WedstrijdLocatie.objects.get(pk=loc1.pk)
        self.assertEqual(loc1.baan_type, BAAN_TYPE_BINNEN_BUITEN)
        self.assertTrue(str(loc1) != '')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertContains(resp, 'Half overdekt')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': BAAN_TYPE_ONBEKEND,
                                          'banen_18m': 5,
                                          'banen_25m': 6,
                                          'notities': self.lange_tekst + " en nog wat meer"})
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        loc1 = WedstrijdLocatie.objects.get(pk=loc1.pk)
        self.assertEqual(loc1.baan_type, BAAN_TYPE_ONBEKEND)

        # probeer met illegale waarden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT,
                                          'banen_18m': 40,
                                          'banen_25m': 6})
        self.assert404(resp, 'Geen valide invoer')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT,
                                          'banen_18m': 4,
                                          'banen_25m': 40})
        self.assert404(resp, 'Geen valide invoer')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': 'y',
                                          'banen_18m': 4,
                                          'banen_25m': 4})
        self.assert404(resp, 'Geen valide invoer')

    def test_wijzig_buitenbaan(self):
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol("HWL")

        url = self.url_locaties % self.ver1.ver_nr

        # maak de (binnen-)accommodatie aan (verplicht voor een buitenbaan)
        loc1 = self._maak_accommodatie(self.ver1)
        loc2 = self._maak_accommodatie(self.ver1, BAAN_TYPE_BUITEN)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': loc1.baan_type,      # verplicht veld
                                          'disc_outdoor': 'on',
                                          'disc_clout': 'on',
                                          'disc_run': 'on',
                                          'buiten_banen': 50,
                                          'buiten_max_afstand': 90,
                                          'buiten_notities': 'dit is een buiten test'})
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        loc2 = WedstrijdLocatie.objects.get(pk=loc2.pk)
        self.assertTrue(loc2.zichtbaar)
        self.assertEqual(loc2.buiten_banen, 50)
        self.assertEqual(loc2.buiten_max_afstand, 90)
        self.assertEqual(loc2.notities, 'dit is een buiten test')
        self.assertFalse(loc2.discipline_25m1pijl)
        self.assertTrue(loc2.discipline_outdoor)
        self.assertFalse(loc2.discipline_indoor)
        self.assertFalse(loc2.discipline_veld)
        self.assertTrue(loc2.discipline_clout)
        self.assertTrue(loc2.discipline_run)
        self.assertFalse(loc2.discipline_3d)

        # andere disciplines
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': loc1.baan_type,      # verplicht veld
                                          'disc_indoor': 'on',      # fake
                                          'disc_25m1p': 'on',
                                          'disc_veld': 'on',
                                          'disc_3d': 'on',
                                          'buiten_banen': 50,
                                          'buiten_max_afstand': 90,
                                          'buiten_notities': 'dit is een buiten test'})
        self.assert_is_redirect(resp, self.url_ver_overzicht)

        loc2 = WedstrijdLocatie.objects.get(pk=loc2.pk)
        self.assertTrue(loc2.discipline_25m1pijl)
        self.assertFalse(loc2.discipline_outdoor)
        self.assertFalse(loc2.discipline_indoor)
        self.assertTrue(loc2.discipline_veld)
        self.assertFalse(loc2.discipline_clout)
        self.assertFalse(loc2.discipline_run)
        self.assertTrue(loc2.discipline_3d)

        # geen wijziging
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'baan_type': loc1.baan_type,      # verplicht veld
                                          'disc_indoor': 'on',      # fake
                                          'disc_25m1p': 'on',
                                          'disc_veld': 'on',
                                          'disc_3d': 'on',
                                          'buiten_banen': 50,
                                          'buiten_max_afstand': 90,
                                          'buiten_notities': 'dit is een buiten test'})
        self.assert_is_redirect(resp, self.url_ver_overzicht)


# end of file
