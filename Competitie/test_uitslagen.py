# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Wedstrijden.models import Wedstrijd
from Overig.e2ehelpers import E2EHelpers
from .models import (Competitie, DeelCompetitie, CompetitieKlasse,
                     DeelcompetitieRonde, competitie_aanmaken,
                     RegioCompetitieSchutterBoog, AG_NUL)
import datetime
import json


class TestCompetitieUitslagen(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, module Informatie over de Competitie """

    test_after = ('Competitie.test_planning',)

    def _prep_beheerder_lid(self, voornaam):
        nhb_nr = self._next_nhbnr
        self._next_nhbnr += 1

        lid = NhbLid()
        lid.nhb_nr = nhb_nr
        lid.geslacht = "M"
        lid.voornaam = voornaam
        lid.achternaam = "Tester"
        lid.email = voornaam.replace(' ', '_').lower() + "@nhb.test"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = self.nhbver
        lid.save()

        return self.e2e_create_account(nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)

    def _maak_schutters_aan(self, ver, aantal, bogen):
        geslacht = 'MV' * aantal

        while aantal:
            aantal -= 1

            # maak een nhblid aan
            lid = NhbLid(
                    nhb_nr=self._next_nhbnr,
                    geslacht=geslacht[0],
                    voornaam='Schutter %s' % (len(self._schuttersboog) + 1),
                    achternaam='Tester',
                    geboorte_datum=datetime.date(year=1982, month=3, day=31-aantal),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
            lid.save()

            self._next_nhbnr += 1
            geslacht = geslacht[1:]

            # maak er een schutter-boog van
            for boog in bogen:
                schutterboog = SchutterBoog(
                                    nhblid=lid,
                                    boogtype=boog,
                                    voor_wedstrijd=True)
                schutterboog.save()
                self._schuttersboog.append(schutterboog)
            # for

        # while

    def _schrijf_in_voor_competitie(self, deelcomp, schuttersboog, skip):
        while len(schuttersboog):
            aanmelding = RegioCompetitieSchutterBoog()
            aanmelding.deelcompetitie = deelcomp
            aanmelding.schutterboog = schuttersboog[0]
            aanmelding.bij_vereniging = aanmelding.schutterboog.nhblid.bij_vereniging
            aanmelding.aanvangsgemiddelde = AG_NUL
            aanmelding.klasse = (CompetitieKlasse
                                 .objects
                                 .filter(competitie=deelcomp.competitie,
                                         indiv__boogtype=aanmelding.schutterboog.boogtype,
                                         indiv__is_onbekend=True)[0])
            aanmelding.save()

            schuttersboog = schuttersboog[skip:]
        # while

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
        self.nhbver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.nhb_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_rcl101 = self._prep_beheerder_lid('RCL 101')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        # klassegrenzen vaststellen
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        resp = self.client.post('/competitie/klassegrenzen/vaststellen/18/')
        self.assertEqual(resp.status_code, 302)
        resp = self.client.post('/competitie/klassegrenzen/vaststellen/25/')
        self.assertEqual(resp.status_code, 302)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')
        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_25, nhb_regio=self.regio_101)[0]

        self.cluster_101a = NhbCluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')

        self.functie_rcl101 = self.deelcomp_regio101_18.functie
        self.functie_rcl101.accounts.add(self.account_rcl101)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.url_planning_regio = '/competitie/planning/regiocompetitie/%s/'    # deelcomp_pk
        self.url_planning_regio_cluster = '/competitie/planning/regiocompetitie/cluster/%s/'    # cluster_pk
        self.url_planning_regio_ronde = '/competitie/planning/regiocompetitie/ronde/%s/'        # ronde_pk

        self.url_uitslag_invoeren = '/competitie/uitslagen-invoeren/wedstrijd/%s/'  # wedstrijd_pk
        self.url_uitslag_deelnemers = '/competitie/dynamic/deelnemers-ophalen/'
        self.url_uitslag_zoeken = '/competitie/dynamic/check-nhbnr/'
        self.url_uitslag_opslaan = '/competitie/dynamic/scores-opslaan/'

        self.url_bekijk_uitslag = '/competitie/wedstrijd/bekijk-uitslag/%s/'    # wedstrijd_pk

        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # maak een regioplanning aan
        self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        ronde18 = DeelcompetitieRonde.objects.all()[0]
        ronde25 = DeelcompetitieRonde.objects.all()[1]

        # maak een wedstrijd aan
        self.client.post(self.url_planning_regio_ronde % ronde18.pk, {})
        self.client.post(self.url_planning_regio_ronde % ronde25.pk, {})
        self.wedstrijd18_pk = Wedstrijd.objects.all()[0].pk
        self.wedstrijd25_pk = Wedstrijd.objects.all()[1].pk

        # schrijf een paar schutters in
        boog_r = BoogType.objects.get(afkorting='R')
        boog_c = BoogType.objects.get(afkorting='C')
        boog_bb = BoogType.objects.get(afkorting='BB')

        self._schuttersboog = list()
        self._maak_schutters_aan(self.nhbver, 5, (boog_r,))
        self._maak_schutters_aan(self.nhbver, 3, (boog_c,))
        self._maak_schutters_aan(self.nhbver, 2, (boog_bb,))
        self._maak_schutters_aan(self.nhbver, 3, (boog_r, boog_bb))
        self._maak_schutters_aan(self.nhbver, 2, (boog_r, boog_c))

        self.client.logout()

    def test_anon(self):
        self.client.logout()
        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        # deelnemers
        resp = self.client.get(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        resp = self.client.post(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # zoeken
        resp = self.client.get(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        resp = self.client.post(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # opslaan
        resp = self.client.get(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        resp = self.client.post(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_get(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslag-invoeren-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # andere tak: max_score/afstand
        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd25_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslag-invoeren-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # nog een keer, dan bestaat de WedstrijdUitslag al
        resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/uitslag-invoeren-wedstrijd.dtl', 'plein/site_layout.dtl'))

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_uitslag_invoeren % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = not found

    def test_rcl_deelnemers_ophalen(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # haal waarschijnlijke deelnemers op
        json_data = {'deelcomp_pk': self.deelcomp_regio101_18.pk}
        resp = self.client.post(self.url_uitslag_deelnemers,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')
        json_data = resp.json()
        self.assertTrue('deelnemers' in json_data.keys())
        self.assertEqual(json_data['deelnemers'], [])   # leeg, want niemand ingeschreven

        # schrijf wat mensen in
        self._schrijf_in_voor_competitie(self.deelcomp_regio101_18,
                                         self._schuttersboog,
                                         1)

        # haal waarschijnlijke deelnemers op
        json_data = {'deelcomp_pk': self.deelcomp_regio101_18.pk}
        resp = self.client.post(self.url_uitslag_deelnemers,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')
        json_data = resp.json()
        self.assertTrue('deelnemers' in json_data)
        # print('test_rcl_deelnemers_ophalen: json_data=%s' % repr(json_data['deelnemers']))
        # print('aantal: %s' % len(json_data['deelnemers']))
        self.assertEqual(len(json_data['deelnemers']), 20)

    def test_rcl_bad_deelnemers_ophalen(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # get (bestaat niet)
        resp = self.client.get(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 405)       # 405 = method not allowed

        # post zonder data
        resp = self.client.post(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met json data maar zonder inhoud
        json_data = {'testje': 1}
        resp = self.client.post(self.url_uitslag_deelnemers,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met niet-bestaande deelcomp
        json_data = {'deelcomp_pk': 999999}
        resp = self.client.post(self.url_uitslag_deelnemers,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_zoeken(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        nhb_nr = self._next_nhbnr - 1
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     'nhb_nr': nhb_nr}
        resp = self.client.post(self.url_uitslag_zoeken,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')
        json_data = resp.json()
        self.assertTrue('fail' in json_data.keys())     # want geen inschrijvingen

        # schrijf wat mensen in
        self._schrijf_in_voor_competitie(self.deelcomp_regio101_18,
                                         self._schuttersboog,
                                         1)

        # nu kunnen we wel wat vinden
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     'nhb_nr': nhb_nr}
        resp = self.client.post(self.url_uitslag_zoeken,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')
        json_data = resp.json()
        # print('test_rcl_zoeken: json_data=%s' % repr(json_data))
        # dit lid als laatste aangemaakte lid heeft 2 bogen
        self.assertEqual(json_data['nhb_nr'], nhb_nr)
        self.assertTrue('naam' in json_data)
        self.assertTrue('regio' in json_data)
        self.assertTrue('bogen' in json_data)
        self.assertTrue('vereniging' in json_data)
        self.assertEqual(len(json_data['bogen']), 2)
        json_data_boog = json_data['bogen'][0]
        self.assertTrue('pk' in json_data_boog)
        self.assertTrue('boog' in json_data_boog)

    def test_rcl_bad_zoeken(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # get (bestaat niet)
        resp = self.client.get(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        resp = self.client.post(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met alleen een nhb_nr
        json_data = {'nhb_nr': 0}
        resp = self.client.post(self.url_uitslag_zoeken,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met alleen wedstrijd_pk
        json_data = {'wedstrijd_pk': 0}
        resp = self.client.post(self.url_uitslag_zoeken,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post niet-bestand wedstrijd_pk
        json_data = {'wedstrijd_pk': 999999,
                     'nhb_nr': 0}
        resp = self.client.post(self.url_uitslag_zoeken,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_opslaan(self):
        self.e2e_login_and_pass_otp(self.account_rcl101)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # get (bestaat niet)
        resp = self.client.get(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        resp = self.client.post(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_bekijk_uitslag(self):
        url = self.url_bekijk_uitslag % self.wedstrijd18_pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)       # 200 = OK

# end of file
