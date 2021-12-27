# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from .models import maak_functie, Functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestFunctieOverzicht(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, functionaliteit Koppel bestuurders """

    test_after = ('Account', 'Functie.test_2fa')

    url_overzicht = '/functie/overzicht/'
    url_overzicht_lid_nrs = '/functie/overzicht/alle-lid-nrs/sec-hwl/'
    url_wijzig = '/functie/wijzig/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_activeer_rol = '/functie/activeer-rol/%s/'

    def setUp(self):
        """ initialisatie van de test case """

        # deze test is afhankelijk van de standaard globale functies
        # zoals opgezet door de migratie m0002_functies-2019:
        #   comp_type: 18/25
        #       rol: BKO, RKO (4x), RCL (16x)

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.account_beh1 = self.e2e_create_account('testbeheerder1', 'beh1@test.nhb', 'Beheerder1', accepteer_vhpg=True)
        self.account_beh2 = self.e2e_create_account('testbeheerder2', 'beh2@test.nhb', 'Beheerder2', accepteer_vhpg=True)
        self.account_ander = self.e2e_create_account('anderlid', 'anderlid@test.nhb', 'Ander')

        self.functie_bko = Functie.objects.get(comp_type='18', rol='BKO')
        self.functie_rko3 = Functie.objects.get(comp_type='18', rol='RKO', nhb_rayon=NhbRayon.objects.get(rayon_nr=3))
        self.functie_rcl111 = Functie.objects.get(comp_type='18', rol='RCL', nhb_regio=NhbRegio.objects.get(regio_nr=111))
        self.functie_rcl101 = Functie.objects.get(comp_type='18', rol='RCL', nhb_regio=NhbRegio.objects.get(regio_nr=101))

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        sporter = Sporter()
        sporter.lid_nr = 100042
        sporter.geslacht = "M"
        sporter.voornaam = "Beh"
        sporter.achternaam = "eerder"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_beh2
        sporter.email = sporter.account.email
        sporter.save()
        self.sporter_100042 = sporter

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak nog een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Extra Club"
        ver2.ver_nr = "1900"
        ver2.regio = NhbRegio.objects.get(regio_nr=112)
        # secretaris kan nog niet ingevuld worden
        ver2.save()

        self.functie_hwl2 = maak_functie("HWL test 2", "HWL")
        self.functie_hwl2.nhb_ver = ver2
        self.functie_hwl2.save()

        sporter = Sporter()
        sporter.lid_nr = 100024
        sporter.geslacht = "V"
        sporter.voornaam = "Ander"
        sporter.achternaam = "Lid"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=5)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=11)
        sporter.bij_vereniging = ver2
        sporter.account = self.account_ander
        sporter.email = sporter.account.email
        sporter.save()
        self.sporter_100024 = sporter

    def test_anon(self):
        self.e2e_logout()

        # geen rechten om dit overzicht in te zien
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        # geen rechten om beheerders te kiezen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig + '123/')
        self.assert403(resp)

    def test_schutter(self):
        # geen rechten om dit overzicht in te zien
        # zelf niet na acceptatie VHPG en OTP controle
        self.e2e_login_and_pass_otp(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht + 'vereniging/')
        self.assert403(resp)

    def test_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # neem de BB rol aan
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        with self.assert_max_queries(20):
            resp = self.client.get('/plein/')
        self.assert_html_ok(resp)
        self.assertContains(resp, "Manager competitiezaken")

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        with self.assert_max_queries(6):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        urls = [url for url in self.extract_all_urls(resp) if url.startswith('/functie/wijzig/')]
        self.assertEqual(len(urls), 2)      # BKO 18m en 25m

        # controleer de Wijzig knoppen op de functie-overzicht pagina voor verschillende rollen

        # neem de BKO 18m rol aan
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "BKO Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 4)      # 4x RKO

        # neem de RKO Rayon 3 Indoor rol aan
        self.e2e_wissel_naar_functie(self.functie_rko3)
        self.e2e_check_rol('RKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "RKO Rayon 3 Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 4)      # 4x RCL

        # neem de RCL Rayon 111 Indoor aan
        self.e2e_wissel_naar_functie(self.functie_rcl111)
        self.e2e_check_rol('RCL')

        # controleer de Wijzig knoppen op de functie-overzicht pagina
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "RCL Regio 111 Indoor")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de RCL

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht)

    def test_hwl(self):
        # de HWL krijgt niet het hele overzicht te zien
        # alleen de RCL, RKO, BKO worden getoond die aan de regio gerelateerd zijn
        self.functie_hwl.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # vraag het overzicht van competitie-bestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "HWL")
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de HWL

        # controleer inhoudelijk op 2xRCL, 2xRKO en 2xBKO (18m en 25m)
        self.assertContains(resp, "BKO", count=2)
        self.assertContains(resp, "RKO", count=2)
        self.assertContains(resp, "RCL", count=2)

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht + 'vereniging/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_overzicht + 'vereniging/')

    def test_wl(self):
        # de WL krijgt niet het hele overzicht te zien
        # alleen de RCL, RKO, BKO worden getoond die aan de regio gerelateerd zijn
        self.functie_wl.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # vraag het overzicht van competitie-bestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        urls = [url for url in self.extract_all_urls(resp) if url.startswith(self.url_wijzig)]
        self.assertEqual(len(urls), 0)      # geen wijzig knoppen voor de WL

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht + 'vereniging/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

    def test_sec(self):
        # de SEC krijgt niet het hele overzicht te zien
        # alleen de RCL, RKO, BKO worden getoond die aan de regio gerelateerd zijn
        self.functie_sec.accounts.add(self.account_beh1)
        self.e2e_login_and_pass_otp(self.account_beh1)

        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # vraag het overzicht van competitie-bestuurders op
        # de SEC heeft hier niets mee te maken en krijgt het overzicht dus niet
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        # haal het overzicht van verenigingsbestuurders op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht + 'vereniging/')
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

    def test_lid_nrs(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_lid_nrs)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/overzicht-lid-nrs.dtl', 'plein/site_layout.dtl'))

# end of file
