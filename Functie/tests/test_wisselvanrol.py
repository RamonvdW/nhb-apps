# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import Competitie, CompetitieMatch, Kampioenschap
from Functie.definities import Rollen
from Functie.models import Functie
from Functie.operations import account_needs_vhpg
from Functie.tests.helpers import maak_functie
from Functie.rol import rol_get_huidige_functie
from Geo.models import Rayon, Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestFunctieWisselVanRol(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, module Wissel van Rol """

    test_after = ('Functie.tests.test_rol',)

    url_wissel_van_rol = '/functie/wissel-van-rol/'
    url_wissel_naar_sec = '/functie/wissel-van-rol/secretaris/'
    url_activeer_rol = '/functie/activeer-rol/%s/'
    url_activeer_functie = '/functie/activeer-functie/%s/'
    url_activeer_functie_hwl = '/functie/activeer-functie-hwl/'     # POST parameter: 'ver_nr'
    url_accountwissel = '/account/account-wissel/'
    url_bondscompetities = '/bondscompetities/'
    url_vhpg_acceptatie = '/functie/vhpg-acceptatie/'
    url_code_prefix = '/tijdelijke-codes/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin(accepteer_vhpg=False)
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geen_lid = self.e2e_create_account('geen_lid', 'geen_lid@test.com', 'Geen')

        regio_111 = Regio.objects.get(regio_nr=111)

        self.functie_rcl = maak_functie("RCL test", "RCL")
        self.functie_rcl.regio = regio_111
        self.functie_rcl.save()

        # maak een test vereniging
        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    plaats='Pijlstad',
                    regio=regio_111)
        ver.save()
        self.ver1000 = ver

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        self.functie_cs = maak_functie("CS test", "CS")
        self.functie_cs.save()

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
                        email=self.account_normaal.email)
        sporter.save()

        # maak een test vereniging zonder HWL rol
        ver2 = Vereniging(
                    naam="Grote Club",
                    plaats='',
                    ver_nr=1001,
                    regio=regio_111)
        ver2.save()

        self.functie_sec2 = maak_functie("SEC test 2", "SEC")
        self.functie_sec2.vereniging = ver2
        self.functie_sec2.save()

        self.functie_bko = maak_functie("BKO test", "BKO")

        self.functie_rko = maak_functie("RKO test", "RKO")
        self.functie_rko.rayon = Rayon.objects.get(rayon_nr=1)
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

    def test_links(self):
        # controleer dat de link naar het wisselen van rol op de pagina staat
        self.account_admin.otp_is_actief = False
        self.account_admin.save()

        # zonder gekoppelde tweede factor worden we niet meteen (meer) doorgestuurd naar de QR-code pagina
        self.e2e_login(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls = [url for url in urls if url.startswith('/account/otp-koppelen-stap1/')]
        self.assertEqual(urls, ['/account/otp-koppelen-stap1/'])

        self.account_admin.otp_is_actief = True
        self.account_admin.save()

        # controleer dat de link naar de OTP-controle en VHPG op de pagina staan
        self.e2e_logout()
        self.e2e_login(self.account_admin)          # zonder OTP control
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Manager MH')
        self.assertContains(resp, 'Gebruiker')
        self.assertContains(resp, 'Maak afspraken over het omgaan met persoonsgegevens.')

        # accepteer VHPG en login met OTP controle
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_account_accepteert_vhpg(self.account_admin)

        # controleer dat de complete keuzemogelijkheden op de pagina staan
        self.client.session.save()      # in session aanwezige cache data (over taken) opslaan
        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Admin site')
        self.assertContains(resp, 'Account wissel')
        self.assertContains(resp, 'Manager MH')
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

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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

        resp = self.client.post(self.url_activeer_functie % 999999)
        self.assert404(resp, 'Foute parameter (functie)')
        self.e2e_check_rol('RCL')

        resp = self.client.post(self.url_activeer_functie % 'getal')
        self.assert404(resp, 'Foute parameter (functie)')
        self.e2e_check_rol('RCL')

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_wissel_van_rol)

    def test_it(self):
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_rol % 'BB', urls)          # Manager MH
        self.assertIn(self.url_accountwissel, urls)

        resp = self.client.post(self.url_activeer_rol % 'BB', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        resp = self.client.get(self.url_wissel_van_rol)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Manager MH")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_accountwissel, urls)

        # controleer dat een niet valide rol wissel geen effect heeft
        # dit raakt een exception in Account.rol:rol_activeer
        resp = self.client.post(self.url_activeer_rol % 'huh', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager MH")

        # controleer dat een rol wissel die met een functie moet geen effect heeft
        resp = self.client.post(self.url_activeer_rol % 'BKO', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Manager MH")

        resp = self.client.post(self.url_activeer_rol % 'geen', follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_accountwissel, urls)

    def test_bb(self):
        # maak een BB die geen lid is
        self.account_geen_lid.is_BB = True
        self.account_geen_lid.save()
        self.e2e_account_accepteert_vhpg(self.account_geen_lid)
        self.e2e_login_and_pass_otp(self.account_geen_lid)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Gebruiker")
        urls = self._get_wissel_urls(resp)
        self.assertNotIn(self.url_accountwissel, urls)              # Account wissel
        self.assertIn(self.url_activeer_rol % 'BB', urls)           # Manager MH
        # self.assertIn(self.url_activeer_rol % 'geen', urls)         # Gebruiker

        with self.assertRaises(ValueError):
            self.e2e_check_rol('deze-rol-is-het-niet')

    def test_bko(self):
        self.functie_bko.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_bko.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')

        # controleer dat wisselen naar SEC niet werkt als BKO
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

        # dit geeft extra coverage in rol.py:rol_activeer_functie
        resp = self.client.post('/functie/activeer-functie/%s/' % self.functie_sec.pk)
        self.assert_is_redirect(resp, '/bondscompetities/')     # omdat we nog steeds BKO zijn
        self.e2e_check_rol('BKO')

        self.e2e_wisselnaarrol_sporter()
        self.e2e_check_rol('sporter')

    def test_rko(self):
        self.functie_rko.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_rko.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

        # probeer te wisselen naar secretaris
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wissel_naar_sec)
        self.assert403(resp)

    def test_rcl(self):
        self.functie_hwl.vereniging.plaats = ''
        self.functie_hwl.vereniging.save(update_fields=['plaats'])

        self.functie_rcl.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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
        self.functie_sec2.accounts.add(self.account_normaal)        # ver.plaats is leeg

        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mo.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_mww(self):
        self.functie_mww.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mww)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mww.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_mwz(self):
        self.functie_mwz.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mwz)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mwz.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_sup(self):
        self.functie_sup.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_sup)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_sup.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_cs(self):
        # CS = Commissie Scheidsrechters
        self.functie_cs.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_cs)

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_cs.pk, urls)
        self.assertIn(self.url_activeer_rol % 'sporter', urls)

    def test_functie_geen_rol(self):
        # test van een functie die niet resulteert in een rol
        functie = maak_functie('Haha', 'HAHA')
        functie.accounts.add(self.account_normaal)
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        with self.assert_max_queries(24):
            resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Sporter")

    def test_geen_rol(self):
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
        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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
        rcl18r111 = maak_functie("RCL Regio 111 Indoor", "RCL")     # omdat 2x Vereniging in regio 111

        rko18r3.accounts.add(self.account_normaal)
        rcl18r111.accounts.add(self.account_normaal)

        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)

        self.e2e_wissel_naar_functie(rcl18r111)

        # nu krijg je 2x alle HWL in regio 111
        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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
        Vereniging.objects.all().delete()        # om lege ver_cache te raken

        # log in en wordt BKO
        self.e2e_account_accepteert_vhpg(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(bko18)
        self.e2e_check_rol('BKO')

        # wissel naar RKO rol
        self.e2e_wissel_naar_functie(rko18r2)
        self.e2e_check_rol('RKO')
        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)       # checkt ook href's

        # wissel door naar de RCL rol
        self.e2e_wissel_naar_functie(rcl18r105)
        self.e2e_check_rol('RCL')
        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)       # checkt ook href's

    def test_bb_naar_sec(self):
        # maak een BB die geen lid is
        self.account_geen_lid.is_BB = True
        self.account_geen_lid.save()
        self.e2e_account_accepteert_vhpg(self.account_geen_lid)
        self.e2e_login_and_pass_otp(self.account_geen_lid)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
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
        ver = Vereniging(
                    naam="Bondsbureau; veel te lange naam die afgekort wordt",
                    ver_nr=1001,
                    regio=Regio.objects.get(pk=100))
        ver.save()

        functie_hwl = maak_functie('HWL ver 1001', 'HWL')
        functie_hwl.vereniging = ver
        functie_hwl.save()

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % functie_hwl.pk, urls)

    def test_bb_to_mo(self):
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.get(self.url_wissel_van_rol)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        urls = self._get_wissel_urls(resp)
        self.assertIn(self.url_activeer_functie % self.functie_mo.pk, urls)

    def test_bb_naar_bad(self):
        # corner case: BB naar niet-bestaande functie
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.post(self.url_activeer_functie % 999999)
        self.assert404(resp, 'Foute parameter (functie)')

    def test_inconsistent(self):
        # corner case: BB naar niet-bestaande functie
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_bko)

        resp = self.client.get('/plein/')
        request = resp.wsgi_request

        rol, functie = rol_get_huidige_functie(request)
        self.assertEqual(rol, Rollen.ROL_BKO)
        self.assertEqual(functie, self.functie_bko)

        self.functie_bko.rol = 'RCL'
        self.functie_bko.save(update_fields=['rol'])
        self.e2e_wissel_naar_functie(self.functie_bko)

        rol, functie = rol_get_huidige_functie(request)
        self.assertEqual(rol, Rollen.ROL_BKO)
        self.assertEqual(functie, self.functie_bko)

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
        self.assert_html_ok(resp)
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
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))

    def test_bko_to_hwl(self):
        self.functie_bko.comp_type = '18'
        self.functie_bko.save(update_fields=['comp_type'])

        comp = Competitie(
                    beschrijving='test',
                    afstand='18',
                    begin_jaar='2000')
        comp.save()

        match = CompetitieMatch(
                    competitie=comp,
                    beschrijving='Test match',
                    vereniging=self.ver1000,
                    datum_wanneer='2000-12-31',
                    tijd_begin_wedstrijd='10:00')
        match.save()

        deelkamp = Kampioenschap(
                        competitie=comp,
                        deel=DEEL_BK,
                        functie=self.functie_bko)
        deelkamp.save()
        deelkamp.rk_bk_matches.add(match)

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')

    def test_rko_to_hwl(self):
        comp = Competitie(
                    beschrijving='test',
                    afstand='18',
                    begin_jaar='2000')
        comp.save()

        match = CompetitieMatch(
                    competitie=comp,
                    beschrijving='Test match',
                    vereniging=self.ver1000,
                    datum_wanneer='2000-12-31',
                    tijd_begin_wedstrijd='10:00')
        match.save()

        deelkamp = Kampioenschap(
                        competitie=comp,
                        deel=DEEL_RK,
                        rayon=self.functie_rko.rayon,
                        functie=self.functie_rko)
        deelkamp.save()
        deelkamp.rk_bk_matches.add(match)

        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.e2e_check_rol('RKO')

    def test_hwl_nr_keuze(self):
        # IT en BB mogen naar een HWL naar keuze wisselen
        self.e2e_account_accepteert_vhpg(self.account_admin)
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        resp = self.client.post(self.url_activeer_functie_hwl, {'ver_nr': 9999})
        self.assert_is_redirect(resp, self.url_wissel_van_rol)

        resp = self.client.post(self.url_activeer_functie_hwl, {'ver_nr': self.ver1000.ver_nr})
        self.assert_is_redirect(resp, '/vereniging/')

    def test_kort(self):
        self.assertTrue(self.functie_rko.kort() != '')
        self.assertTrue(self.functie_rcl.kort() != '')
        self.assertTrue(self.functie_hwl.kort() != '')
        self.assertTrue(self.functie_mwz.kort() != '')

    def test_wissel_met_otp(self):
        # login als admin
        self.e2e_login_and_pass_otp(self.account_admin)

        # activeer een rol + vhpg voor de beheerder
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.e2e_assert_other_http_commands_not_supported(self.url_accountwissel, post=False)

        # selecteer de andere gebruiker
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_accountwissel, {'selecteer': self.account_normaal.pk})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('account/login-as-go.dtl', 'plein/site_layout.dtl'))

        # pik de tijdelijke URL op
        urls = [url for url in self.extract_all_urls(resp) if self.url_code_prefix in url]
        # hak het https deel eraf
        tijdelijke_url = urls[0][urls[0].find(self.url_code_prefix):]
        # volg de tijdelijke url om ingelogd te raken
        with self.assert_max_queries(20):
            resp = self.client.get(tijdelijke_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        resp = self.client.post(post_url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('plein/plein-sporter.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wissel van rol')

        # controleer dat OTP controle niet nodig is
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Sporter')
        self.assertContains(resp, 'Manager MH')

# FUTURE: test maken met gebruiker in 2x rol met dezelfde 'volgorde' (gaf sorteerprobleem), zowel 2xBKO als 2xHWL

# end of file
