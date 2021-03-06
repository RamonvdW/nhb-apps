# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Overig.e2ehelpers import E2EHelpers
from Competitie.models import DeelCompetitie, competitie_aanmaken
import datetime


class TestVerenigingenLijst(E2EHelpers, TestCase):

    """ unit tests voor de Vereniging applicatie, Lijst Verenigingen """

    def _prep_beheerder_lid(self, voornaam):
        nhb_nr = self._next_nhbnr
        self._next_nhbnr += 1

        lid = NhbLid()
        lid.nhb_nr = nhb_nr
        lid.geslacht = "M"
        lid.voornaam = voornaam
        lid.achternaam = "Tester"
        lid.email = voornaam.lower() + "@nhb.test"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = self._ver
        lid.save()

        return self.e2e_create_account(nhb_nr, lid.email, E2EHelpers.WACHTWOORD, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.account_admin = self.e2e_create_account_admin()

        self._next_nhbnr = 100001

        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver
        self.nhb_ver1 = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.nhb_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_hwl = self._prep_beheerder_lid('HWL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        self.functie_bko = DeelCompetitie.objects.filter(laag='BK')[0].functie
        self.functie_rko = DeelCompetitie.objects.filter(laag='RK', nhb_rayon=self.rayon_2)[0].functie
        self.functie_rcl = DeelCompetitie.objects.filter(laag='Regio', nhb_regio=self.regio_101)[0].functie

        self.functie_bko.accounts.add(self.account_bko)
        self.functie_rko.accounts.add(self.account_rko)
        self.functie_rcl.accounts.add(self.account_rcl)
        self.functie_hwl.accounts.add(self.account_hwl)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        # stop de vereniging in clusters
        cluster = NhbCluster.objects.filter(regio=ver.regio, gebruik='18').all()[0]
        ver.clusters.add(cluster)
        cluster = NhbCluster.objects.filter(regio=ver.regio, gebruik='25').all()[2]
        ver.clusters.add(cluster)
        self.nhb_ver2 = ver

        self.url_lijst = '/vereniging/accommodaties/lijst/'

    def test_anon(self):
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assert_is_redirect(resp, '/plein/')
        self.e2e_assert_other_http_commands_not_supported(self.url_lijst)

    def test_it(self):
        # landelijke lijst + leden aantal
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_it()
        self.e2e_check_rol('IT')
        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_bb(self):
        # landelijke lijst met rayon & regio
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        with self.assert_max_queries(7):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_bko(self):
        # landelijke lijst met rayon & regio
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')
        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_rko(self):
        # rayon lijst met regio kolom (geen rayon kolom)
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.e2e_check_rol('RKO')
        with self.assert_max_queries(7):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_rcl(self):
        # regio lijst met hwls (zonder rayon/regio kolommen)
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)
        self.e2e_check_rol('RCL')
        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(self.url_lijst)

    def test_rcl_met_clusters(self):
        # test de lijst met clusters erin

        # log in als RCL
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)
        self.e2e_check_rol('RCL')

        # verenigingen 1 en 2 horen beide bij regio 101
        # stop ze een voor een in een eigen cluster

        # maak een cluster aan en stop nhb_ver1 erin
        cluster = NhbCluster()
        cluster.regio = self.nhb_ver1.regio
        cluster.letter = 'Y'
        cluster.naam = "Bovenlijns"
        cluster.gebruik = '18'
        cluster.save()
        self.nhb_ver1.cluster = cluster
        self.nhb_ver1.save()

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # stop nhb_ver2 in hetzelfde cluster
        self.nhb_ver2.cluster = cluster
        self.nhb_ver2.save()

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # stop nhb_ver2 in een apart cluster
        cluster = NhbCluster()
        cluster.regio = self.nhb_ver1.regio
        cluster.letter = 'Z'
        cluster.naam = "Onderlijns"
        cluster.gebruik = '18'
        cluster.save()
        self.nhb_ver2.cluster = cluster
        self.nhb_ver2.save()

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_hwl(self):
        # de hwl krijgt dezelfde lijst als de rcl
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')
        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-verenigingen.dtl', 'plein/site_layout.dtl'))

    def test_overzicht_anon(self):
        with self.assert_max_queries(20):
            resp = self.client.get('/bondscompetities/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

# end of file
