# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import Regiocompetitie, Kampioenschap
from Competitie.operations import competities_aanmaken
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio, Cluster
from Locatie.definities import BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN, BAAN_TYPE_ONBEKEND
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging, Secretaris
import datetime


class TestVerenigingenLijst(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, Lijst Verenigingen """

    url_lijst = '/vereniging/lijst/'
    url_lijst_details = '/vereniging/lijst/%s/'                     # ver_nr
    url_geen_beheerders = '/vereniging/contact-geen-beheerders/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        lid = Sporter(
                    lid_nr=lid_nr,
                    geslacht="M",
                    voornaam=voornaam,
                    achternaam="Tester",
                    email=voornaam.lower() + "@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self._ver)
        lid.save()

        return self.e2e_create_account(lid_nr, lid.email, E2EHelpers.WACHTWOORD, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_2 = Rayon.objects.get(rayon_nr=2)
        self.regio_101 = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_101)
        ver.save()
        self._ver = ver     # wordt gebruikt door _prep_beheerder_lid
        self.ver1 = ver

        # maak de beheerders aan van deze vereniging
        self.functie_sec = maak_functie("SEC Vereniging %s" % ver.ver_nr, "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save(update_fields=['vereniging'])

        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save(update_fields=['vereniging'])

        self.functie_wl = maak_functie("WL Vereniging %s" % ver.ver_nr, "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save(update_fields=['vereniging'])

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_hwl = self._prep_beheerder_lid('HWL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # referentie uit de CRM welke leden secretaris zijn
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1
        lid = Sporter(
                    lid_nr=lid_nr,
                    geslacht="M",
                    voornaam="Secretaris",
                    achternaam="Zonder account",
                    email="secretaris@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver1)
        lid.save()
        self.sec = Secretaris(vereniging=self.ver1)
        self.sec.save()
        self.sec.sporters.add(lid)

        # creëer een competitie met regiocompetities
        competities_aanmaken(jaar=2019)

        self.functie_bko = Kampioenschap.objects.filter(deel=DEEL_BK)[0].functie
        self.functie_rko = Kampioenschap.objects.filter(deel=DEEL_RK, rayon=self.rayon_2)[0].functie
        self.functie_rcl = Regiocompetitie.objects.filter(regio=self.regio_101)[0].functie

        self.functie_bko.accounts.add(self.account_bko)
        self.functie_rko.accounts.add(self.account_rko)
        self.functie_rcl.accounts.add(self.account_rcl)
        self.functie_hwl.accounts.add(self.account_hwl)

        # maak nog een test vereniging, zonder HWL functie
        ver = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver.save()
        # stop de vereniging in clusters
        cluster = Cluster.objects.filter(regio=ver.regio, gebruik='18').first()
        ver.clusters.add(cluster)
        cluster = Cluster.objects.filter(regio=ver.regio, gebruik='25').all()[2]
        ver.clusters.add(cluster)
        self.ver2 = ver

        # geef een verenigingen alle mogelijke externe locaties
        loc = WedstrijdLocatie(baan_type=BAAN_TYPE_BUITEN)
        loc.save()
        loc.verenigingen.add(self.ver1)
        self.loc_buiten = loc

        loc = WedstrijdLocatie(baan_type=BAAN_TYPE_EXTERN)
        loc.save()
        loc.verenigingen.add(self.ver1)

        loc = WedstrijdLocatie(baan_type=BAAN_TYPE_ONBEKEND)
        loc.save()
        loc.verenigingen.add(self.ver1)
        self.loc_binnen = loc

    def test_anon(self):
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assert403(resp)

    def test_it(self):
        # landelijke lijst met rayon & regio + leden aantallen
        self.testdata.account_bb.is_staff = True
        self.testdata.account_bb.save(update_fields=['is_staff'])

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(12):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_lijst)

    def test_bb(self):
        # landelijke lijst met rayon & regio
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(11):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

    def test_competitie_beheerders(self):
        # landelijke lijst met rayon & regio
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_bko)
        self.e2e_check_rol('BKO')

        with self.assert_max_queries(12):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

        # rayon lijst met regio kolom (geen rayon kolom)
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.e2e_check_rol('RKO')

        with self.assert_max_queries(7):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

        # regio lijst met HWL's (zonder rayon/regio kolommen)
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)
        self.e2e_check_rol('RCL')

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(self.url_lijst)

        # verenigingen 1 en 2 horen beide bij regio 101
        # stop ze een voor een in een eigen cluster

        # maak een cluster aan en stop ver1 erin
        cluster = Cluster(
                    regio=self.ver1.regio,
                    letter='Y',
                    naam="Bovenlijns",
                    gebruik='18')
        cluster.save()
        self.ver1.clusters.add(cluster)

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_details % self.ver1.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-details.dtl', 'design/site_layout.dtl'))

        # stop ver2 in hetzelfde cluster
        self.ver2.cluster = cluster
        self.ver2.save()

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

        # stop ver2 in een apart cluster
        cluster = Cluster(
                        regio=self.ver1.regio,
                        letter='Z',
                        naam="Onderlijns",
                        gebruik='18')
        cluster.save()
        self.ver2.cluster = cluster
        self.ver2.save()

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

    def test_hwl(self):
        # de hwl krijgt dezelfde lijst als de rcl
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(9):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst.dtl', 'design/site_layout.dtl'))

        resp = self.client.get(self.url_lijst_details % 999999)
        self.assert404(resp, 'Geen valide vereniging')

        url = self.url_lijst_details % self.ver1.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-details.dtl', 'design/site_layout.dtl'))

        # corner cases
        self.loc_buiten.zichtbaar = False
        self.loc_buiten.save(update_fields=['zichtbaar'])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-details.dtl', 'design/site_layout.dtl'))

        self.loc_buiten.delete()
        self.loc_binnen.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-details.dtl', 'design/site_layout.dtl'))

        self.assertTrue(str(self.sec) != '')

        self.sec.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-details.dtl', 'design/site_layout.dtl'))

        self.functie_sec.accounts.add(self.account_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-details.dtl', 'design/site_layout.dtl'))

        self.functie_wl.delete()
        resp = self.client.get(url)
        self.assert404(resp, "Rol ontbreekt")

        self.ver1.is_extern = True
        self.ver1.save(update_fields=['is_extern'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-details.dtl', 'design/site_layout.dtl'))

        self.functie_sec.delete()
        resp = self.client.get(url)
        self.assert404(resp, "Rol ontbreekt")

    def test_geen_beheerders(self):
        # login als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak een extra vereniging aan zonder beheerders
        ver = Vereniging(
                    naam="Extra Club",
                    ver_nr=1099,
                    regio=Regio.objects.get(regio_nr=101))
        ver.save()

        # maak de SEC, HWL en WL functies aan voor deze vereniging
        for rol in ('SEC', 'HWL', 'WL'):
            tmp_func = maak_functie(rol + " ver 1099", rol)
            tmp_func.vereniging = ver

            if rol == 'SEC':
                tmp_func.bevestigde_email = 'sec@1099.not'

            tmp_func.save()
        # for

        self.functie_sec.accounts.add(self.account_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_geen_beheerders)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/contact-geen-beheerders.dtl', 'design/site_layout.dtl'))

        # corner case
        self.functie_sec.delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_geen_beheerders)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/contact-geen-beheerders.dtl', 'design/site_layout.dtl'))

        # probeer het met een andere rol
        self.e2e_wisselnaarrol_gebruiker()
        resp = self.client.get(self.url_geen_beheerders)
        self.assert403(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_geen_beheerders)

# end of file
