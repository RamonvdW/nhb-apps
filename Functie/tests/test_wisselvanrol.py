# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import Competitie, DeelCompetitie, LAAG_BK, LAAG_RK, CompetitieMatch
from Functie.models import Functie
from Functie.operations import maak_functie, account_needs_vhpg
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestFunctieWisselVanRol(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, module Wissel van Rol """

    test_after = ('Functie.tests.test_rol',)

    url_wissel_van_rol = '/functie/wissel-van-rol/'
    url_wissel_naar_sec = '/functie/wissel-van-rol/secretaris/'
    url_activeer_rol = '/functie/activeer-rol/%s/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_accountwissel = '/account/account-wissel/'
    url_bondscompetities = '/bondscompetities/'
    url_vhpg_acceptatie = '/functie/vhpg-acceptatie/'

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
        ver = NhbVereniging(
                    ver_nr="1000",
                    naam="Grote Club",
                    regio=regio_111)
        ver.save()
        self.ver1000 = ver

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
        ver2.save()

        self.functie_bko = maak_functie("BKO test", "BKO")

        self.functie_rko = maak_functie("RKO test", "RKO")
        self.functie_rko.nhb_rayon = NhbRayon.objects.get(rayon_nr=1)
        self.functie_rko.save()

        self.functie_mo = maak_functie("MO test", "MO")
        self.functie_mo.save()

        self.functie_mww = maak_functie("MWW test", "MWW")
        self.functie_mww.save()

        self.functie_mwz = maak_functie("MWZ test", "MWZ")
        self.functie_mwz.save()

        self.functie_sup = maak_functie("SUP test", "SUP")
        self.functie_sup.save()

    def _get_wissel_urls(self, resp):
        urls = self.extract_all_urls(resp)
        return [url for url in urls if url.startswith('/functie/activeer') or url == self.url_accountwissel]

    def test_admin(self):
        # controleer dat de link naar het wisselen van rol op de pagina staat
        self.account_admin.otp_is_actief = False
        self.account_admin.save()

        # zonder gekoppelde tweede factor worden we niet meteen (meer) doorgestuurd naar de QR-code pagina
        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls = [url for url in urls if url.startswith('/functie/otp-koppelen-stap1/')]
        self.assertEqual(urls, ['/functie/otp-koppelen-stap1/'])

        self.account_admin.otp_is_actief = True
        self.account_admin.save()

        # controleer dat de link naar de OTP-controle en VHPG op de pagina staan
        self.e2e_logout()
        self.e2e_login(self.account_admin)          # zonder OTP control
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'Manager Competitiezaken')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Maak afspraken over het omgaan met persoonsgegevens.')

        # accepteer VHPG en login met OTP controle
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_account_accepteert_vhpg(self.account_admin)

        # controleer dat de complete keuzemogelijkheden op de pagina staan
        self.client.session.save()      # in session aanwezige cache data (over taken) opslaan
        with self.assert_max_queries(25):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Admin site')
        self.assertContains(resp, 'Account wissel')
        self.assertContains(resp, 'Manager Competitiezaken')
        self.assertContains(resp, 'Gebruiker')

        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(self.url_wissel_van_rol)

    def test_normaal(self):
        self.account_normaal.otp_is_actief = False
        self.account_normaal.save(update_fields=['otp_is_actief'])
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

        # niet een niet- bestaande functie vanuit de RCL-functie
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_functie % self.functie_rcl.pk)
        self.assert_is_redirect(resp, self.url_bondscompetities)
        self.e2e_check_rol('RCL')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_functie % 999999)
        self.assert_is_redirect(resp, self.url_bondscompetities)

        self.e2e_check_rol('RCL')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_functie % 'getal')
        self.assert_is_redirect(resp, self.url_bondscompetities)
        self.e2e_check_rol('RCL')

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_wissel_van_rol)

    def test_it(self):
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)

        with self.assert_max_queries(25):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_rol % 'BB', urls)          # Manager Competitiezaken
        self.assertIn(self.url_activeer_rol % 'geen', urls)        # Gebruiker
        self.assertIn(self.url_accountwissel, urls)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'BB', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # response = het Plein
        with self.assert_max_queries(26):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertContains(resp, "Manager Competitiezaken")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_accountwissel, urls)

        # controleer dat een niet valide rol wissel geen effect heeft
        # dit raakt een exception in Account.rol:rol_activeer
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'huh', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager Competitiezaken")

        # controleer dat een rol wissel die met een functie moet geen effect heeft
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_activeer_rol % 'BKO', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager Competitiezaken")

        with self.assert_max_queries(31):
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

        with self.assert_max_queries(25):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertNotIn(self.url_accountwissel, urls)              # Account wissel
        self.assertIn(self.url_activeer_rol % 'BB', urls)           # Manager Competitiezaken
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

        with self.assert_max_queries(22):
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

        with self.assert_max_queries(21):
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

        with self.assert_max_queries(21):
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

    def test_mo(self):
        self.functie_mo.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mo.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_mww(self):
        self.functie_mww.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mww)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mww.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_mwz(self):
        self.functie_mwz.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mwz)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mwz.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_sup(self):
        self.functie_sup.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_sup)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_sup.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

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
        # self.assert403(resp)
        self.assert_is_redirect(resp, '/plein/')

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
        with self.assert_max_queries(28):
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
        with self.assert_max_queries(23):
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

        Sporter.objects.all().delete()
        NhbVereniging.objects.all().delete()        # om lege nhbver_cache te raken

        # log in en wordt BKO
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(bko18)
        self.e2e_check_rol('BKO')

        # wissel naar RKO rol
        self.e2e_wissel_naar_functie(rko18r2)
        self.e2e_check_rol('RKO')
        with self.assert_max_queries(27):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)       # checkt ook href's

        # wissel door naar de RCL rol
        self.e2e_wissel_naar_functie(rcl18r105)
        self.e2e_check_rol('RCL')
        with self.assert_max_queries(26):
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

        with self.assert_max_queries(26):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Wordt secretaris van een van de verenigingen")
        urls = self.extract_all_urls(resp)
        urls = [url for url in urls if url == '/functie/wissel-van-rol/secretaris/']
        self.assertEqual(len(urls), 1)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-naar-sec.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

    def test_bb_to_hwl_regio_100(self):
        # maak een test vereniging
        ver = NhbVereniging(
            naam="Bondsbureau; veel te lange naam die afgekort wordt",
            ver_nr="1001",
            regio=NhbRegio.objects.get(pk=100))
        ver.save()

        functie_hwl = maak_functie('HWL ver 1001', 'HWL')
        functie_hwl.nhb_ver = ver
        functie_hwl.save()

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(26):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % functie_hwl.pk, urls)

    def test_bb_to_mo(self):
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(26):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mo.pk, urls)

    def test_bb_naar_bad(self):
        # corner case: BB naar niet-bestaande functie
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.post(self.url_activeer_functie % 999999)
        self.assert_is_redirect(resp, '/plein/')

    def test_vhpg(self):
        # controleer doorsturen naar de VHPG acceptatie pagina
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_account_accepteert_vhpg(self.account_admin)

        # forceer verlopen VHPG
        _, vhpg = account_needs_vhpg(self.account_admin)
        vhpg.acceptatie_datum -= datetime.timedelta(days=400)
        vhpg.save(update_fields=['acceptatie_datum'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assert_is_redirect(resp, self.url_vhpg_acceptatie)

    def test_post_functie(self):
        # test de situatie nadat een gebruiker (met 2FA) nu geen functie meer heeft
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        # gaan naar de wissel-van-rol pagina
        resp = self.client.get(self.url_wissel_van_rol)
        self.assert_is_redirect(resp, '/plein/')

        # herhaal met 'staff' vlag, zonder functies
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.assertEqual(0, self.account_admin.functie_set.count())
        self.assertTrue(self.account_admin.is_staff)
        self.assertFalse(self.account_admin.is_BB)

        # gaan naar de wissel-van-rol pagina
        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

        # herhaal met 'BB' vlag, zonder functies
        self.account_admin.is_BB = True
        self.account_admin.is_staff = False
        self.account_admin.save(update_fields=['is_BB', 'is_staff'])

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.assertFalse(self.account_admin.is_staff)
        self.assertTrue(self.account_admin.is_BB)

        # gaan naar de wissel-van-rol pagina
        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

    def test_bko_to_hwl(self):
        self.functie_bko.comp_type = '18'
        self.functie_bko.save(update_fields=['comp_type'])

        comp = Competitie(
                    beschrijving='test',
                    afstand='18',
                    begin_jaar='2000',
                    uiterste_datum_lid='2000-01-01',
                    begin_aanmeldingen='2000-10-10',
                    einde_aanmeldingen='2000-10-10',
                    einde_teamvorming='2000-10-10',
                    eerste_wedstrijd='2000-10-10',
                    laatst_mogelijke_wedstrijd='2000-10-10',
                    datum_klassengrenzen_rk_bk_teams='2000-10-10',
                    rk_eerste_wedstrijd='2000-10-10',
                    rk_laatste_wedstrijd='2000-10-10',
                    bk_eerste_wedstrijd='2000-10-10',
                    bk_laatste_wedstrijd='2000-10-10')
        comp.save()

        match = CompetitieMatch(
                    competitie=comp,
                    beschrijving='Test match',
                    vereniging=self.ver1000,
                    datum_wanneer='2000-12-31',
                    tijd_begin_wedstrijd='10:00')
        match.save()

        deelcomp = DeelCompetitie(
                        competitie=comp,
                        laag=LAAG_BK,
                        functie=self.functie_bko)
        deelcomp.save()
        deelcomp.rk_bk_matches.add(match)

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')

    def test_rko_to_hwl(self):
        comp = Competitie(
                    beschrijving='test',
                    afstand='18',
                    begin_jaar='2000',
                    uiterste_datum_lid='2000-01-01',
                    begin_aanmeldingen='2000-10-10',
                    einde_aanmeldingen='2000-10-10',
                    einde_teamvorming='2000-10-10',
                    eerste_wedstrijd='2000-10-10',
                    laatst_mogelijke_wedstrijd='2000-10-10',
                    datum_klassengrenzen_rk_bk_teams='2000-10-10',
                    rk_eerste_wedstrijd='2000-10-10',
                    rk_laatste_wedstrijd='2000-10-10',
                    bk_eerste_wedstrijd='2000-10-10',
                    bk_laatste_wedstrijd='2000-10-10')
        comp.save()

        match = CompetitieMatch(
                    competitie=comp,
                    beschrijving='Test match',
                    vereniging=self.ver1000,
                    datum_wanneer='2000-12-31',
                    tijd_begin_wedstrijd='10:00')
        match.save()

        deelcomp = DeelCompetitie(
                        competitie=comp,
                        laag=LAAG_RK,
                        nhb_rayon=self.functie_rko.nhb_rayon,
                        functie=self.functie_rko)
        deelcomp.save()
        deelcomp.rk_bk_matches.add(match)

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.e2e_check_rol('RKO')

    # TODO: test maken waarbij gebruiker aan 2x rol zit met dezelfde 'volgorde' (gaf sorteerprobleem), zowel 2xBKO als 2xHWL

# end of file
