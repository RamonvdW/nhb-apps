# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from NhbStructuur.migrations.m0002_nhbstructuur_2018 import maak_rayons_2018, maak_regios_2018
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestFunctieWisselVanRol(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie, module Wissel van Rol """

    test_after = ('Functie.test_rol',)

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin(accepteer_vhpg=False)
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@test.com', 'Geen')

        # maak de standard rayon/regio structuur aan
        maak_rayons_2018(NhbRayon)
        maak_regios_2018(NhbRayon, NhbRegio)

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        self.functie_rcl = maak_functie("RCL test", "RCL")
        self.functie_rcl.nhb_regio = regio_111
        self.functie_rcl.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_normaal
        lid.save()
        self.nhblid1 = lid

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

        # maak een test vereniging zonder CWZ rol
        ver2 = NhbVereniging()
        ver2.naam = "Grote Club"
        ver2.nhb_nr = "1001"
        ver2.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver2.save()

        self.url_wisselvanrol = '/functie/wissel-van-rol/'

    def test_admin(self):
        # controleer dat de link naar het wisselen van rol op de pagina staat
        self.account_admin.otp_is_actief = False
        self.account_admin.save()
        self.e2e_login(self.account_admin)
        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'IT beheerder')
        self.assertNotContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Controle met een tweede factor is verplicht voor gebruikers met toegang tot persoonsgegevens')
        self.account_admin.otp_is_actief = True
        self.account_admin.save()

        # controleer dat de link naar de OTP controle en VHPG op de pagina staan
        self.e2e_logout()        # TODO: onnodig?
        self.e2e_login(self.account_admin)          # zonder OTP control
        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'IT beheerder')
        self.assertNotContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Voordat je aan de slag kan moeten we eerst een paar afspraken maken over het omgaan met persoonsgegevens.')
        #print(str(resp.content).replace('>', '>\n'))
        self.assertContains(resp, 'Een aantal rollen komt beschikbaar nadat de controle van de tweede factor uitgevoerd is.')

        # accepteer VHPG en login met OTP controle
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_account_accepteert_vhpg(self.account_admin)

        # controleer dat de complete keuzemogelijkheden op de pagina staan
        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertContains(resp, 'IT beheerder')
        self.assertContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')

        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(self.url_wisselvanrol)

    def test_normaal(self):
        self.e2e_login(self.account_normaal)
        # controleer dat de wissel-van-rol pagina niet aanwezig is voor deze normale gebruiker
        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to plein)

        self.assertTrue(str(self.functie_cwz) == "CWZ test")

    def test_normaal_met_rol(self):
        # voeg de gebruiker toe aan twee functies waardoor wissel-van-rol actief wordt
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.functie_rcl.accounts.add(self.account_normaal)
        self.functie_cwz.accounts.add(self.account_normaal)

        self.e2e_login_and_pass_otp(self.account_normaal)

        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "BKO test")
        self.assertNotContains(resp, "RKO test")
        self.assertContains(resp, "RCL test")
        self.assertContains(resp, "CWZ test")
        self.assertContains(resp, "Grote Club")

        # activeer nu de rol van RCL
        # dan komen de CWZ rollen te voorschijn
        resp = self.client.get(self.url_wisselvanrol + 'functie/%s/' % self.functie_rcl.pk)
        self.assert_is_redirect(resp, self.url_wisselvanrol)

        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "BKO test")
        self.assertNotContains(resp, "RKO test")
        self.assertContains(resp, "RCL test")
        self.assertContains(resp, "CWZ test")

        # niet bestaande functie
        resp = self.client.get(self.url_wisselvanrol + 'functie/999999/')
        self.assert_is_redirect(resp, self.url_wisselvanrol)
        # TODO: check functie ongewijzigd

        resp = self.client.get(self.url_wisselvanrol + 'functie/getal/')
        self.assert_is_redirect(resp, self.url_wisselvanrol)
        # TODO: check functie ongewijzigd

        self.e2e_assert_other_http_commands_not_supported(self.url_wisselvanrol)

    def test_rolwissel_it(self):
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)

        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = [url for url in self.extract_all_href_urls(resp) if url.startswith(self.url_wisselvanrol)]
        self.assertIn(self.url_wisselvanrol + 'beheerder/', urls)   # IT beheerder
        self.assertIn(self.url_wisselvanrol + 'BB/', urls)          # Manager competitiezaken
        self.assertIn(self.url_wisselvanrol + 'geen/', urls)        # Gebruiker
        self.assertNotIn('/account/account-wissel/', urls)

        resp = self.client.get(self.url_wisselvanrol + 'BB/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager competitiezaken")
        urls = [url for url in self.extract_all_href_urls(resp) if url.startswith(self.url_wisselvanrol)]
        self.assertNotIn('/account/account-wissel/', urls)

        resp = self.client.get(self.url_wisselvanrol + 'beheerder/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "IT beheerder")
        urls = [url for url in self.extract_all_href_urls(resp) if url.startswith('/account/')]
        self.assertIn('/account/account-wissel/', urls)

        # controleer dat een niet valide rol wissel geen effect heeft
        # dit raakt een exception in Account.rol:rol_activeer
        resp = self.client.get(self.url_wisselvanrol + 'huh/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "IT beheerder")

        # controleer dat een rol wissel die met een functie moet geen effect heeft
        resp = self.client.get(self.url_wisselvanrol + 'BKO/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "IT beheerder")

        resp = self.client.get(self.url_wisselvanrol + 'geen/', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = [url for url in self.extract_all_href_urls(resp) if url.startswith(self.url_wisselvanrol)]
        self.assertNotIn('/account/account-wissel', urls)

    def test_rolwissel_bb(self):
        # maak een BB die geen NHB lid is
        self.account_geenlid.is_BB = True
        self.account_geenlid.save()
        self.e2e_account_accepteert_vhpg(self.account_geenlid)
        self.e2e_login_and_pass_otp(self.account_geenlid)

        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = [url for url in self.extract_all_href_urls(resp) if url.startswith(self.url_wisselvanrol)]
        self.assertNotIn('/account/account-wissel', urls)           # Account wissel
        self.assertIn(self.url_wisselvanrol + 'BB/', urls)          # Manager competitiezaken
        self.assertIn(self.url_wisselvanrol + 'geen/', urls)        # Gebruiker

    def test_geen_rolwissel(self):
        # dit raakt de exceptie in Account.rol:rol_mag_wisselen
        self.e2e_logout()
        resp = self.client.get(self.url_wisselvanrol)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

        # probeer van rol te wisselen
        resp = self.client.get(self.url_wisselvanrol + 'beheerder/')
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect (to login)

# TODO: gebruik assert_other_http_commands_not_supported

# end of file
