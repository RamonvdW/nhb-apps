# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Wedstrijden.models import WedstrijdLocatie
from Overig.e2ehelpers import E2EHelpers
from .models import (Competitie, DeelCompetitie, competitie_aanmaken,
                     LAAG_REGIO, LAAG_RK)
from .test_fase import zet_competitie_fase
import datetime


class TestCompetitiePlanningBond(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, Koppel Beheerders functie """

    test_after = ('Competitie.test_fase', 'Competitie.test_beheerders', 'Competitie.test_competitie')

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
        lid.bij_vereniging = self.nhbver_101
        lid.save()

        return self.e2e_create_account(nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.account_admin = self.e2e_create_account_admin()

        self._next_nhbnr = 100001

        self.rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)
        self.regio_105 = NhbRegio.objects.get(regio_nr=105)
        self.regio_112 = NhbRegio.objects.get(regio_nr=112)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Zuidelijke Club"
        ver.nhb_nr = "1111"
        ver.regio = self.regio_112
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver_112 = ver

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
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
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.nhb_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_rko1_18 = self._prep_beheerder_lid('RKO1')
        self.account_rko2_18 = self._prep_beheerder_lid('RKO2')
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL101')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL101-25')
        self.account_rcl112_18 = self._prep_beheerder_lid('RCL112')
        self.account_schutter = self._prep_beheerder_lid('Schutter')
        self.lid_schutter = NhbLid.objects.get(nhb_nr=self.account_schutter.username)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.schutterboog = SchutterBoog(nhblid=self.lid_schutter,
                                         boogtype=self.boog_r,
                                         voor_wedstrijd=True)
        self.schutterboog.save()

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        # klassengrenzen vaststellen om de competitie voorbij fase A1 te krijgen
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        self.deelcomp_bond_18 = DeelCompetitie.objects.filter(laag='BK', competitie=self.comp_18)[0]
        self.deelcomp_rayon1_18 = DeelCompetitie.objects.filter(laag='RK', competitie=self.comp_18, nhb_rayon=self.rayon_1)[0]

        self.functie_bko_18 = self.deelcomp_bond_18.functie
        self.functie_bko_18.accounts.add(self.account_bko_18)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.url_doorzetten_rk = '/competitie/planning/doorzetten/%s/rk/'     # comp_pk
        self.url_doorzetten_bk = '/competitie/planning/doorzetten/%s/bk/'     # comp_pk

    def test_doorzetten_rk(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_doorzetten_rk % self.comp_18.pk

        # fase F: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'F')
        self.comp_18.zet_fase()
        self.assertEqual(self.comp_18.fase, 'F')
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
        self.comp_18.zet_fase()
        self.assertEqual(self.comp_18.fase, 'G')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bko-doorzetten-naar-rk.dtl', 'plein/site_layout.dtl'))

        # nu echt doorzetten
        resp = self.client.post(url)
        self.assert_is_redirect(resp, '/competitie/overzicht/')       # redirect = Success

    def test_doorzetten_bk(self):
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        url = self.url_doorzetten_bk % self.comp_18.pk

        # fase M: pagina zonder knop 'doorzetten'
        zet_competitie_fase(self.comp_18, 'M')
        self.comp_18.zet_fase()
        self.assertEqual(self.comp_18.fase, 'M')
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
        self.comp_18.zet_fase()
        self.assertEqual(self.comp_18.fase, 'N')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bko-doorzetten-naar-bk.dtl', 'plein/site_layout.dtl'))

        # nu echt doorzetten
        resp = self.client.post(url)
        self.assert_is_redirect(resp, '/competitie/overzicht/')       # redirect = Success

    def test_doorzetten_bad(self):
        # moet BKO zijn
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_doorzetten_rk % 999999)
        self.assert_is_redirect(resp, '/plein/')

        resp = self.client.get(self.url_doorzetten_bk % 999999)
        self.assert_is_redirect(resp, '/plein/')

        # niet bestaande comp_pk
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        resp = self.client.get(self.url_doorzetten_rk % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed

        resp = self.client.post(self.url_doorzetten_rk % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed

        resp = self.client.get(self.url_doorzetten_bk % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed

        resp = self.client.post(self.url_doorzetten_bk % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed

        # juiste comp_pk maar verkeerde fase
        zet_competitie_fase(self.comp_18, 'C')
        resp = self.client.get(self.url_doorzetten_rk % self.comp_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed

        resp = self.client.post(self.url_doorzetten_rk % self.comp_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed

        resp = self.client.get(self.url_doorzetten_bk % self.comp_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed

        resp = self.client.post(self.url_doorzetten_bk % self.comp_18.pk)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found/allowed


# end of file
