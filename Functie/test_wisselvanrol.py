# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie, maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestFunctieWisselVanRol(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, module Wissel van Rol """

    test_after = ('Functie.test_rol',)

    url_wissel_van_rol = '/functie/wissel-van-rol/'
    url_wissel_naar_sec = '/functie/wissel-van-rol/secretaris/'
    url_activeer_rol = '/functie/activeer-rol/%s/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_accountwissel = '/account/account-wissel/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin(accepteer_vhpg=False)
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geenlid = self.e2e_create_account('geenlid', 'geenlid@test.com', 'Geen')

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        self.functie_rcl = maak_functie("RCL test", "RCL")
        self.functie_rcl.nhb_regio = regio_111
        self.functie_rcl.save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

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

        # maak een test vereniging zonder HWL rol
        ver2 = NhbVereniging()
        ver2.naam = "Grote Club"
        ver2.ver_nr = "1001"
        ver2.regio = regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()

        self.functie_bko = maak_functie("BKO test", "BKO")

        self.functie_rko = maak_functie("RKO test", "RKO")
        self.functie_rko.nhb_rayon = NhbRayon.objects.get(rayon_nr=1)
        self.functie_rko.save()

    def _get_wissel_urls(self, resp):
        return [url for url in self.extract_all_urls(resp) if url.startswith('/functie/activeer') or url == self.url_accountwissel]

    def test_admin(self):
        # controleer dat de link naar het wisselen van rol op de pagina staat
        self.account_admin.otp_is_actief = False
        self.account_admin.save()

        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assert_is_redirect_not_plein(resp)

        self.account_admin.otp_is_actief = True
        self.account_admin.save()

        # controleer dat de link naar de OTP controle en VHPG op de pagina staan
        self.e2e_logout()
        self.e2e_login(self.account_admin)          # zonder OTP control
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'IT beheerder')
        self.assertNotContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Voordat je aan de slag kan moeten we eerst een paar afspraken maken over het omgaan met persoonsgegevens.')
        # print(str(resp.content).replace('>', '>\n'))
        self.assertContains(resp, 'Een aantal rollen komt beschikbaar nadat de controle van de tweede factor uitgevoerd is.')

        # accepteer VHPG en login met OTP controle
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_account_accepteert_vhpg(self.account_admin)

        # controleer dat de complete keuzemogelijkheden op de pagina staan
        self.client.session.save()      # in session aanwezige cache data (over taken) opslaan
        with self.assert_max_queries(11):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Admin site')
        self.assertContains(resp, 'Account wissel')
        self.assertContains(resp, 'Manager competitiezaken')
        self.assertContains(resp, 'Gebruiker')

        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(self.url_wissel_van_rol)

    def test_normaal(self):
        self.e2e_login(self.account_normaal)
        # controleer dat de wissel-van-rol pagina niet aanwezig is voor deze normale gebruiker
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assert403(resp)

        self.assertTrue(str(self.functie_hwl) == "HWL test")

    def test_normaal_met_rol(self):
        # voeg de gebruiker toe aan twee functies waardoor wissel-van-rol actief wordt
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.functie_rcl.accounts.add(self.account_normaal)
        self.functie_hwl.accounts.add(self.account_normaal)

        self.e2e_login_and_pass_otp(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertNotContains(resp, "BKO test")
        self.assertNotContains(resp, "RKO test")
        self.assertContains(resp, "RCL test")
        self.assertContains(resp, "HWL test")
        self.assertContains(resp, "Grote Club")

        # niet een niet- bestaande functie vanuit de RCL functie
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_functie % self.functie_rcl.pk)
        self.assert_is_redirect(resp, self.url_wissel_van_rol)
        self.e2e_check_rol('RCL')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_functie % 999999)
        self.assert_is_redirect(resp, self.url_wissel_van_rol)

        self.e2e_check_rol('RCL')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_functie % 'getal')
        self.assert_is_redirect(resp, self.url_wissel_van_rol)
        self.e2e_check_rol('RCL')

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_wissel_van_rol)

    def test_it(self):
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_rol % 'BB', urls)          # Manager competitiezaken
        self.assertIn(self.url_activeer_rol % 'geen', urls)        # Gebruiker
        self.assertIn(self.url_accountwissel, urls)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'BB', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager competitiezaken")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_accountwissel, urls)

        # controleer dat een niet valide rol wissel geen effect heeft
        # dit raakt een exception in Account.rol:rol_activeer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'huh', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager competitiezaken")

        # controleer dat een rol wissel die met een functie moet geen effect heeft
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'BKO', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager competitiezaken")

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'geen', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_accountwissel, urls)

    def test_bb(self):
        # maak een BB die geen NHB lid is
        self.account_geenlid.is_BB = True
        self.account_geenlid.save()
        self.e2e_account_accepteert_vhpg(self.account_geenlid)
        self.e2e_login_and_pass_otp(self.account_geenlid)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertNotIn(self.url_accountwissel, urls)              # Account wissel
        self.assertIn(self.url_activeer_rol % 'BB', urls)           # Manager competitiezaken
        # self.assertIn(self.url_activeer_rol % 'geen', urls)         # Gebruiker

        with self.assertRaises(ValueError):
            self.e2e_check_rol('deze-rol-is-het-niet')

    def test_bko(self):
        self.functie_bko.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_bko.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

        self.e2e_wisselnaarrol_sporter()
        self.e2e_check_rol('sporter')

    def test_rko(self):
        self.functie_rko.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_rko.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

    def test_rcl(self):
        self.functie_rcl.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertNotIn(self.url_activeer_functie % self.functie_sec.pk, urls)
        self.assertIn(self.url_activeer_functie % self.functie_rcl.pk, urls)
        self.assertIn(self.url_activeer_functie % self.functie_hwl.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

    def test_sec(self):
        self.functie_sec.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)

        self.assertNotIn(self.url_activeer_functie % self.functie_rcl.pk, urls)
        self.assertIn(self.url_activeer_functie % self.functie_sec.pk, urls)
        self.assertIn(self.url_activeer_functie % self.functie_hwl.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_hwl(self):
        self.functie_hwl.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertNotIn(self.url_activeer_functie % self.functie_sec.pk, urls)
        self.assertIn(self.url_activeer_functie % self.functie_hwl.pk, urls)
        self.assertIn(self.url_activeer_functie % self.functie_wl.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

    def test_wl(self):
        self.functie_wl.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_wl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertNotIn(self.url_activeer_functie % self.functie_sec.pk, urls)
        self.assertNotIn(self.url_activeer_functie % self.functie_hwl.pk, urls)
        self.assertIn(self.url_activeer_functie % self.functie_wl.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

    def test_functie_geen_rol(self):
        # test van een functie die niet resulteert in een rol
        functie = maak_functie('Haha', 'HAHA')
        functie.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")

    def test_geen_rolwissel(self):
        # dit raakt de exceptie in Account.rol:rol_mag_wisselen
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assert403(resp)

        # probeer van rol te wisselen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'IT')
        self.assert403(resp)

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

    def test_delete_functie(self):
        # corner case: activeer functie, verwijder functie, get_huidige_functie
        self.functie_hwl.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        # wordt hwl
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # verwijder hwl
        self.functie_hwl.delete()

        # wat is de huidige functie?
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assert403(resp)

    def test_dubbele_rol_rko(self):
        # voorkom dat dit probleem terug komt:
        # je hebt een rol en je erft deze
        # voorbeeld: BKO Indoor --> RKO Rayon2 Indoor (welke je ook expliciet hebt)
        # hierdoor krijg je dubbele rollen: 2x alle RCL in Rayon2

        bko18 = maak_functie("BKO Indoor", "BKO")
        rko18r2 = maak_functie("RKO Rayon 2 Indoor", "RKO")

        bko18.accounts.add(self.account_normaal)
        rko18r2.accounts.add(self.account_normaal)

        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        self.e2e_wissel_naar_functie(rko18r2)

        # nu krijg je 2x alle RCL in rayon 2
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self._get_wissel_urls(resp)

        urls_no_dupes = list(set(urls))
        for url in urls_no_dupes:
            urls.remove(url)
        # for
        if len(urls) > 0:       # pragma: no cover
            msg = "Dubbele mogelijkheden gevonden in WisselVanRol:\n  "
            msg += "\n  ".join(urls)
            self.fail(msg)

    def test_dubbele_rol_rcl(self):
        # voorkom dat dit probleem terug komt:
        # je hebt een rol en je erft deze
        # voorbeeld: RKO Rayon3 Indoor --> RCL Regio 111 (welke je ook expliciet hebt)
        # hierdoor krijg je dubbele rollen: 2x alle HWL in je regio

        rko18r3 = maak_functie("RKO Rayon 3 Indoor", "RKO")
        rcl18r111 = maak_functie("RCL Regio 111 Indoor", "RCL")     # omdat 2x NhbVereniging in regio 111

        rko18r3.accounts.add(self.account_normaal)
        rcl18r111.accounts.add(self.account_normaal)

        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        self.e2e_wissel_naar_functie(rcl18r111)

        # nu krijg je 2x alle HWL in regio 111
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self._get_wissel_urls(resp)

        urls_no_dupes = list(set(urls))
        for url in urls_no_dupes:
            urls.remove(url)
        # for
        if len(urls) > 0:       # pragma: no cover
            msg = "Dubbele mogelijkheden gevonden in WisselVanRol:\n  "
            msg += "\n  ".join(urls)
            self.fail(msg)

    def test_help_anderen(self):
        # probeer het helpen van andere rollen
        # hiervoor moeten we de ingebouwde rollen gebruiken, met herkende hierarchy
        bko18 = Functie.objects.get(beschrijving="BKO Indoor")
        rko18r2 = Functie.objects.get(beschrijving="RKO Rayon 2 Indoor")
        rcl18r105 = Functie.objects.get(beschrijving="RCL Regio 105 Indoor")

        bko18.accounts.add(self.account_normaal)

        # log in en wordt BKO
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(bko18)
        self.e2e_check_rol('BKO')

        # wissel naar RKO rol
        self.e2e_wissel_naar_functie(rko18r2)
        self.e2e_check_rol('RKO')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)       # checkt ook href's

        # wissel door naar de RCL rol
        self.e2e_wissel_naar_functie(rcl18r105)
        self.e2e_check_rol('RCL')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)       # checkt ook href's

    def test_bb_naar_sec(self):
        # maak een BB die geen NHB lid is
        self.account_geenlid.is_BB = True
        self.account_geenlid.save()
        self.e2e_account_accepteert_vhpg(self.account_geenlid)
        self.e2e_login_and_pass_otp(self.account_geenlid)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "(extra keuzescherm)")
        self.assertContains(resp, "Secretaris")

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-naar-sec.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')


# end of file
