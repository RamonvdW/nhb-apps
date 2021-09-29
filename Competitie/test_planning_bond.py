# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from .models import (Competitie, CompetitieKlasse,
                     DeelCompetitie, LAAG_REGIO, LAAG_RK, LAAG_BK,
                     RegioCompetitieSchutterBoog, KampioenschapSchutterBoog)
from .operations import competities_aanmaken
from .test_fase import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompetitiePlanningBond(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

    url_doorzetten_rk = '/bondscompetities/%s/doorzetten/rk/'  # comp_pk
    url_doorzetten_bk = '/bondscompetities/%s/doorzetten/bk/'  # comp_pk

    testdata = None

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
        sporter.bij_vereniging = self.nhbver_101
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
        self.regio_105 = NhbRegio.objects.get(regio_nr=105)
        self.regio_112 = NhbRegio.objects.get(regio_nr=112)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Zuidelijke Club"
        ver.ver_nr = "1111"
        ver.regio = self.regio_112
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_101 = ver

        loc = WedstrijdLocatie(banen_18m=1,
                               banen_25m=1,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc = loc

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL101')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL101-25')
        self.account_rcl112_18 = self._prep_beheerder_lid('RCL112')
        self.account_schutter = self._prep_beheerder_lid('Schutter')
        self.lid_sporter_1 = Sporter.objects.get(lid_nr=self.account_schutter.username)

        self.account_schutter2 = self._prep_beheerder_lid('Schutter2')
        self.lid_sporter_2 = Sporter.objects.get(lid_nr=self.account_schutter2.username)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.sporterboog = SporterBoog(sporter=self.lid_sporter_1,
                                       boogtype=self.boog_r,
                                       voor_wedstrijd=True)
        self.sporterboog.save()

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.url_klassegrenzen_vaststellen_18 = '/bondscompetities/%s/klassegrenzen/vaststellen/' % self.comp_18.pk
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)  # check for success

        self.deelcomp_bond_18 = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                              laag=LAAG_BK)[0]
        self.deelcomp_rayon1_18 = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                                laag=LAAG_RK,
                                                                nhb_rayon=self.rayon_1)[0]
        self.deelcomp_regio_101 = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                                laag=LAAG_REGIO,
                                                                nhb_regio=self.regio_101)[0]

        self.functie_bko_18 = self.deelcomp_bond_18.functie
        self.functie_bko_18.accounts.add(self.account_bko_18)

        self.functie_rko1_18 = self.deelcomp_rayon1_18.functie
        self.functie_rko1_18.accounts.add(self.account_rko1_18)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

    def _regioschutters_inschrijven(self):

        boog_c = BoogType.objects.get(afkorting='C')

        klasse_r = CompetitieKlasse.objects.filter(indiv__boogtype__afkorting='R',
                                                   indiv__is_onbekend=False,
                                                   indiv__niet_voor_rk_bk=False)[0]

        klasse_c = CompetitieKlasse.objects.filter(indiv__boogtype__afkorting='C',
                                                   indiv__is_onbekend=False,
                                                   indiv__niet_voor_rk_bk=False)[0]

        # recurve, lid 1
        RegioCompetitieSchutterBoog(deelcompetitie=self.deelcomp_regio_101,
                                    sporterboog=self.sporterboog,
                                    bij_vereniging=self.sporterboog.sporter.bij_vereniging,
                                    klasse=klasse_r,
                                    aantal_scores=7).save()

        # compound, lid 1
        sporterboog = SporterBoog(sporter=self.lid_sporter_1,
                                  boogtype=boog_c,
                                  voor_wedstrijd=True)
        sporterboog.save()

        RegioCompetitieSchutterBoog(deelcompetitie=self.deelcomp_regio_101,
                                    sporterboog=sporterboog,
                                    bij_vereniging=sporterboog.sporter.bij_vereniging,
                                    klasse=klasse_c,
                                    aantal_scores=6).save()

        # compound, lid2
        sporterboog = SporterBoog(sporter=self.lid_sporter_2,
                                  boogtype=boog_c,
                                  voor_wedstrijd=True)
        sporterboog.save()

        RegioCompetitieSchutterBoog(deelcompetitie=self.deelcomp_regio_101,
                                    sporterboog=sporterboog,
                                    bij_vereniging=sporterboog.sporter.bij_vereniging,
                                    klasse=klasse_c,
                                    aantal_scores=6).save()

    def test_doorzetten_rk(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_doorzetten_rk % self.comp_18.pk

        # fase F: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'F')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'F')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bko-doorzetten-naar-rk.dtl', 'plein/site_layout.dtl'))

        # sluit alle deelcompetitie regio
        for obj in DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                 is_afgesloten=False,
                                                 laag=LAAG_REGIO):
            obj.is_afgesloten = True
            obj.save()
        # for

        # fase G: pagina met knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'G')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'G')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bko-doorzetten-naar-rk.dtl', 'plein/site_layout.dtl'))

        # nu echt doorzetten
        self._regioschutters_inschrijven()

        self.assertEqual(3, RegioCompetitieSchutterBoog.objects.count())
        self.assertEqual(0, KampioenschapSchutterBoog.objects.count())

        with self.assert_max_queries(55):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        self.assertEqual(3, KampioenschapSchutterBoog.objects.count())

    def test_doorzetten_rk_geen_lid(self):
        # variant van doorzetten_rk met een lid dat niet meer bij een vereniging aangesloten is
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_doorzetten_rk % self.comp_18.pk

        # fase F: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'F')

        # sluit alle deelcompetitie regio
        for obj in DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                 is_afgesloten=False,
                                                 laag=LAAG_REGIO):
            obj.is_afgesloten = True
            obj.save()
        # for

        # fase G: pagina met knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'G')

        # nu echt doorzetten
        self._regioschutters_inschrijven()

        self.assertEqual(3, RegioCompetitieSchutterBoog.objects.count())
        self.assertEqual(0, KampioenschapSchutterBoog.objects.count())

        self.lid_sporter_2.bij_vereniging = None
        self.lid_sporter_2.save()

        with self.assert_max_queries(54):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        # het lid zonder vereniging komt toch gewoon in de RK selectie
        self.assertEqual(3, KampioenschapSchutterBoog.objects.count())

        # verdere tests in test_planning_rayon.test_geen_vereniging check

    def test_doorzetten_bk(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_doorzetten_bk % self.comp_18.pk

        # fase M: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'M')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'M')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bko-doorzetten-naar-bk.dtl', 'plein/site_layout.dtl'))

        # alle rayonkampioenschappen afsluiten
        for obj in DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                 is_afgesloten=False,
                                                 laag=LAAG_RK):
            obj.is_afgesloten = True
            obj.save()
        # for

        # fase N: pagina met knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'N')
        self.comp_18.bepaal_fase()
        self.assertEqual(self.comp_18.fase, 'N')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bko-doorzetten-naar-bk.dtl', 'plein/site_layout.dtl'))

        # nu echt doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        self.assertTrue(str(self.deelcomp_bond_18) != '')

        deelcomp_bk_18 = DeelCompetitie.objects.get(competitie=self.comp_18,
                                                    laag=LAAG_BK)
        objs = KampioenschapSchutterBoog.objects.filter(deelcompetitie=deelcomp_bk_18)
        self.assertEqual(objs.count(), 0)       # worden nog niet gemaakt, dus 0

        team_klasse = CompetitieKlasse.objects.filter(indiv=None)[0]
        deeln_bk = KampioenschapSchutterBoog(deelcompetitie=deelcomp_bk_18,
                                             sporterboog=self.sporterboog,
                                             klasse=team_klasse)
        self.assertTrue(str(deeln_bk) != '')

    def test_doorzetten_bad(self):
        # moet BKO zijn
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_doorzetten_rk % 999999)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_doorzetten_bk % 999999)
        self.assert403(resp)

        # niet bestaande comp_pk
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_doorzetten_rk % 999999)
        self.assert404(resp)     # 404 = Not found/allowed

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_doorzetten_rk % 999999)
        self.assert404(resp)     # 404 = Not found/allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_doorzetten_bk % 999999)
        self.assert404(resp)     # 404 = Not found/allowed

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_doorzetten_bk % 999999)
        self.assert404(resp)     # 404 = Not found/allowed

        # juiste comp_pk maar verkeerde fase
        zet_competitie_fase(self.comp_18, 'C')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_doorzetten_rk % self.comp_18.pk)
        self.assert404(resp)     # 404 = Not found/allowed

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_doorzetten_rk % self.comp_18.pk)
        self.assert404(resp)     # 404 = Not found/allowed

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_doorzetten_bk % self.comp_18.pk)
        self.assert404(resp)     # 404 = Not found/allowed

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_doorzetten_bk % self.comp_18.pk)
        self.assert404(resp)     # 404 = Not found/allowed


# end of file
