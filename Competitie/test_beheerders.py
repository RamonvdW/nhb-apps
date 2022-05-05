# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, DeelCompetitie, RegioCompetitieSchutterBoog, LAAG_REGIO, LAAG_RK, LAAG_BK
from Competitie.operations import competities_aanmaken
from Competitie.test_fase import zet_competitie_fase
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompetitieBeheerders(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Functie',)

    url_kies = '/bondscompetities/'
    url_overzicht = '/bondscompetities/%s/'  # comp_pk
    url_wijzigdatums = '/bondscompetities/%s/wijzig-datums/'  # comp_pk
    url_aangemeld_alles = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/alles/'  # comp_pk

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter()
        sporter.lid_nr = lid_nr
        sporter.geslacht = "M"
        sporter.voornaam = voornaam
        sporter.achternaam = "Tester"
        sporter.email = voornaam.lower() + "@nhb.test"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = self._ver
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)
        # nu in fase A

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_BK).all():
            deelcomp.functie.accounts.add(self.account_bko)
        # for

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_RK, nhb_rayon=self.rayon_2).all():
            deelcomp.functie.accounts.add(self.account_rko)
        # for

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_REGIO, nhb_regio=self.regio_101).all():
            deelcomp.functie.accounts.add(self.account_rcl)
        # for

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver2 = ver

        # maak HWL functie aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        hwl.nhb_ver = ver
        hwl.save()

    def _doe_inschrijven(self, comp):

        url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/' % comp.pk

        # meld een bak leden aan voor de competitie
        self.e2e_wisselnaarrol_bb()

        # klassengrenzen vaststellen
        url_klassengrenzen = '/bondscompetities/%s/klassengrenzen/vaststellen/'
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_18.pk)
            self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_25.pk)
            self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de datum voor inschrijven op vandaag
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_competitie_fase(comp, 'B')
        # for

        lid_nr = 110000
        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk
        compound_boog_pk = BoogType.objects.get(afkorting='C').pk
        barebow_boog_pk = BoogType.objects.get(afkorting='BB').pk

        # doorloop de 2 verenigingen in deze regio
        for nhb_ver in NhbVereniging.objects.filter(regio=self.regio_101):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = nhb_ver.functie_set.filter(rol='HWL').all()[0]
            self.e2e_wissel_naar_functie(functie_hwl)

            post_params = dict()

            # maak 3 leden aan
            for lp in range(3):
                lid_nr += 1
                sporter = Sporter()
                sporter.lid_nr = lid_nr
                sporter.voornaam = "Lid %s" % lid_nr
                sporter.achternaam = "de Tester"
                sporter.bij_vereniging = nhb_ver
                sporter.is_actief_lid = True
                if barebow_boog_pk:
                    sporter.geboorte_datum = datetime.date(2019-12, 1, 1)   # aspirant
                else:
                    sporter.geboorte_datum = datetime.date(2000, 1, 1)      # senior
                sporter.sinds_datum = datetime.date(2010, 1, 1)
                sporter.geslacht = 'M'
                sporter.save()

                # haal de sporter voorkeuren op, zodat de sporterboog records aangemaakt worden
                url_voorkeuren = '/sporter/voorkeuren/%s/' % lid_nr
                with self.assert_max_queries(20):
                    resp = self.client.get(url_voorkeuren)
                self.assertEqual(resp.status_code, 200)     # 200 = OK

                # zet de recurve boog aan
                if lp == 1:
                    # zet de DT voorkeur aan voor een paar sporters
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on',
                                                                 'voorkeur_eigen_blazoen': 'on'})
                    # onthoud deze sporterboog om straks in bulk aan te melden
                    # 'lid_NNNNNN_boogtype_MM'
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'
                elif lp == 2:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_C': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, compound_boog_pk)] = 'on'
                elif barebow_boog_pk:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_BB': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, barebow_boog_pk)] = 'on'
                    barebow_boog_pk = None
                else:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'

                self.assert_is_redirect_not_plein(resp)         # check for success
            # for

            # schrijf in voor de competitie
            with self.assert_max_queries(22):
                resp = self.client.post(url_inschrijven, post_params)
            self.assert_is_redirect_not_plein(resp)         # check for success
        # for

    def test_kies_anon(self):
        url = self.url_kies
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported(url)

    def test_overzicht(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        comp18 = Competitie.objects.get(afstand='18')
        comp25 = Competitie.objects.get(afstand='25')

        self._doe_inschrijven(comp18)         # wisselt naar HWL rol
        #self._doe_inschrijven(comp25)         # wisselt naar HWL rol

        # BB
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # BKO 18m
        functie_bko = DeelCompetitie.objects.get(competitie=comp18, laag=LAAG_BK).functie
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(functie_bko)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # RKO 25m Rayon 2
        functie_rko = DeelCompetitie.objects.get(competitie=comp25, laag=LAAG_RK, nhb_rayon=self.rayon_2).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_login_and_pass_otp(self.account_rko)
        self.e2e_wissel_naar_functie(functie_rko)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp25.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # RCL
        functie_rcl = DeelCompetitie.objects.get(competitie=comp18, laag=LAAG_REGIO, nhb_regio=self.regio_101).functie
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-beheerder.dtl', 'plein/site_layout.dtl'))

        # HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-hwl.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp25.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht-hwl.dtl', 'plein/site_layout.dtl'))

        # TODO: add WL

        # coverage voor models __str__
        obj = RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__laag=LAAG_REGIO).all()[0]
        self.assertTrue(str(obj) != '')

        deelcomp = obj.deelcompetitie
        deelcomp.laag = LAAG_RK
        deelcomp.nhb_regio = None
        deelcomp.nhb_rayon = self.rayon_1
        deelcomp.save()
        obj = RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__laag=LAAG_RK).all()[0]
        self.assertTrue(str(obj) != '')

        deelcomp = obj.deelcompetitie
        deelcomp.laag = LAAG_BK
        deelcomp.nhb_rayon = None
        deelcomp.save()
        obj = RegioCompetitieSchutterBoog.objects.filter(deelcompetitie__laag=LAAG_BK).all()[0]
        self.assertTrue(str(obj) != '')

    def test_wijzig_datums_not_bb(self):
        comp = Competitie.objects.all()[0]
        url = self.url_wijzigdatums % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_wijzig_datums_bb(self):
        comp = Competitie.objects.all()[0]
        url = self.url_wijzigdatums % comp.pk

        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.begin_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.einde_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.einde_teamvorming)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.eerste_wedstrijd)

        # wordt BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # get
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-wijzig-datums.dtl', 'plein/site_layout.dtl'))

        # post
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': '2019-08-09',
                                          'datum2': '2019-09-10',
                                          'datum3': '2019-10-11',
                                          'datum4': '2019-11-12',
                                          'datum5': '2019-11-12',
                                          'datum6': '2020-02-01',
                                          'datum7': '2019-02-12',
                                          'datum8': '2020-05-01',
                                          'datum9': '2020-05-12',
                                          'datum10': '2020-06-12',
                                          })
        self.assert_is_redirect(resp, self.url_overzicht % comp.pk)

        # controleer dat de nieuwe datums opgeslagen zijn
        comp = Competitie.objects.get(pk=comp.pk)
        self.assertEqual(datetime.date(year=2019, month=8, day=9), comp.begin_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=9, day=10), comp.einde_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=10, day=11), comp.einde_teamvorming)
        self.assertEqual(datetime.date(year=2019, month=11, day=12), comp.eerste_wedstrijd)

        # check corner cases

        # alle datums verplicht
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': '2019-08-09'})
        self.assert404(resp, 'Verplichte parameter ontbreekt')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': 'null',
                                          'datum2': 'hallo',
                                          'datum3': '0',
                                          'datum4': '2019-13-42'})
        self.assert404(resp, 'Geen valide datum')

        # foute comp_pk bij get
        url = self.url_wijzigdatums % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # foute comp_pk bij post
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

# end of file
