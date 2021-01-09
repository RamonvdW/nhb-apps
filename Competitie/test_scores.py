# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Score.models import Score
from Wedstrijden.models import Wedstrijd, WedstrijdUitslag
from .models import (Competitie, DeelCompetitie, CompetitieKlasse,
                     DeelcompetitieRonde, competitie_aanmaken,
                     RegioCompetitieSchutterBoog, AG_NUL)
from Overig.e2ehelpers import E2EHelpers
import datetime
import json


class TestCompetitieScores(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, module Scores """

    test_after = ('Competitie.test_fase', 'Competitie.test_planning_regio',)

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

    @staticmethod
    def _schrijf_in_voor_competitie(deelcomp, schuttersboog, skip):
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
        self.account_rcl101_18 = self._prep_beheerder_lid('RCL 101 18m')
        self.account_rcl101_25 = self._prep_beheerder_lid('RCL 101 25m')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # klassegrenzen vaststellen
        url_vaststellen = '/bondscompetities/%s/klassegrenzen/vaststellen/'  # comp_pk
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.post(url_vaststellen % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)     # check success
        with self.assert_max_queries(20):
            resp = self.client.post(url_vaststellen % self.comp_25.pk)
        self.assert_is_redirect_not_plein(resp)     # check success

        self.deelcomp_regio101_18 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_18, nhb_regio=self.regio_101)[0]
        self.deelcomp_regio101_25 = DeelCompetitie.objects.filter(laag='Regio', competitie=self.comp_25, nhb_regio=self.regio_101)[0]

        self.cluster_101a = NhbCluster.objects.get(regio=self.regio_101, letter='a', gebruik='18')

        self.functie_rcl101_18 = self.deelcomp_regio101_18.functie
        self.functie_rcl101_18.accounts.add(self.account_rcl101_18)

        self.functie_rcl101_25 = self.deelcomp_regio101_25.functie
        self.functie_rcl101_25.accounts.add(self.account_rcl101_25)

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.nhb_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()

        self.url_planning_regio = '/bondscompetities/planning/regio/%s/'                   # deelcomp_pk
        self.url_planning_regio_cluster = '/bondscompetities/planning/regio/cluster/%s/'   # cluster_pk
        self.url_planning_regio_ronde = '/bondscompetities/planning/regio/ronde/%s/'       # ronde_pk

        self.url_uitslag_invoeren = '/bondscompetities/scores/uitslag-invoeren/%s/'        # wedstrijd_pk
        self.url_uitslag_deelnemers = '/bondscompetities/scores/dynamic/deelnemers-ophalen/'
        self.url_uitslag_zoeken = '/bondscompetities/scores/dynamic/check-nhbnr/'
        self.url_uitslag_opslaan = '/bondscompetities/scores/dynamic/scores-opslaan/'

        self.url_uitslag_controleren = '/bondscompetities/scores/uitslag-controleren/%s/'  # wedstrijd_pk
        self.url_uitslag_accorderen = '/bondscompetities/scores/uitslag-accorderen/%s/'    # wedstrijd_pk

        self.url_scores_regio = '/bondscompetities/scores/regio/%s/'                       # deelcomp_pk
        self.url_bekijk_uitslag = '/bondscompetities/scores/bekijk-uitslag/%s/'            # wedstrijd_pk

        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # maak een regioplanning aan
        with self.assert_max_queries(20):
            self.client.post(self.url_planning_regio % self.deelcomp_regio101_18.pk)
        with self.assert_max_queries(20):
            self.client.post(self.url_planning_regio % self.deelcomp_regio101_25.pk)
        ronde18 = DeelcompetitieRonde.objects.all()[0]
        ronde25 = DeelcompetitieRonde.objects.all()[1]

        # maak een wedstrijd aan
        with self.assert_max_queries(20):
            self.client.post(self.url_planning_regio_ronde % ronde18.pk, {})
        with self.assert_max_queries(20):
            self.client.post(self.url_planning_regio_ronde % ronde25.pk, {})
        self.wedstrijd18_pk = Wedstrijd.objects.all()[0].pk
        self.wedstrijd25_pk = Wedstrijd.objects.all()[1].pk
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd18_pk)
        wedstrijd.vereniging = self.functie_hwl.nhb_ver
        wedstrijd.save()

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
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assert_is_redirect(resp, '/plein/')      # not allowed

        # scores
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_scores_regio % self.deelcomp_regio101_18.pk)
        self.assert_is_redirect(resp, '/plein/')

        # deelnemers
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # zoeken
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # opslaan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_get(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('competitie/scores-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # andere tak: max_score/afstand
        # with self.assert_max_queries(20):
        #     resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd25_pk)
        # self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.assert_html_ok(resp)
        # self.assert_template_used(resp, ('competitie/scores-invoeren.dtl', 'plein/site_layout.dtl'))

        # nog een keer, dan bestaat de WedstrijdUitslag al
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('competitie/scores-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % 999999)
        self.assertEqual(resp.status_code, 404)     # 404 = not found

    def test_rcl_deelnemers_ophalen(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # haal waarschijnlijke deelnemers op
        json_data = {'deelcomp_pk': self.deelcomp_regio101_18.pk}
        with self.assert_max_queries(20):
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
        with self.assert_max_queries(20):
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
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # get (bestaat niet)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 405)       # 405 = method not allowed

        # post zonder data
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_deelnemers)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met json data maar zonder inhoud
        json_data = {'testje': 1}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_deelnemers,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met niet-bestaande deelcomp
        json_data = {'deelcomp_pk': 999999}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_deelnemers,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_zoeken(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        nhb_nr = self._next_nhbnr - 1
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     'nhb_nr': nhb_nr}
        with self.assert_max_queries(20):
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
        with self.assert_max_queries(20):
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
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # get (bestaat niet)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_zoeken)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met alleen een nhb_nr
        json_data = {'nhb_nr': 0}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met alleen wedstrijd_pk
        json_data = {'wedstrijd_pk': 0}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post niet-bestand wedstrijd_pk
        json_data = {'wedstrijd_pk': 999999,
                     'nhb_nr': 0}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_rcl_opslaan(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # doe eerst een get zodat de wedstrijd.uitslag gegarandeerd is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # zonder scores
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # met schutterboog_pk's en scores
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     self._schuttersboog[0].pk: 123,
                     self._schuttersboog[1].pk: -1,
                     self._schuttersboog[2].pk: 999999,
                     self._schuttersboog[3].pk: 'hoi',
                     self._schuttersboog[4].pk: 100,
                     self._schuttersboog[5].pk: 101,
                     self._schuttersboog[6].pk: '',         # verwijderd maar was niet aanwezig
                     'hoi': 1,
                     999999: 111}                           # niet bestaande schutterboog_pk
        # print('json_data for post: %s' % json.dumps(json_data))
        with self.assert_max_queries(25):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)
        self.assertEqual(json_data['done'], 1)

        # nog een keer opslaan - met mutaties
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     self._schuttersboog[0].pk: 132,        # aangepaste score
                     self._schuttersboog[4].pk: 100,        # ongewijzigde score
                     self._schuttersboog[5].pk: ''}         # verwijderde score
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)
        self.assertEqual(json_data['done'], 1)

    def test_rcl_accorderen(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        url = self.url_uitslag_controleren % self.wedstrijd18_pk
        ackurl = self.url_uitslag_accorderen % self.wedstrijd18_pk

        # doe eerst een get zodat de wedstrijd.uitslag gegarandeerd is
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # scores aanmaken
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     self._schuttersboog[0].pk: 123,
                     self._schuttersboog[1].pk: 124,
                     self._schuttersboog[2].pk: 125,
                     self._schuttersboog[3].pk: 126,
                     self._schuttersboog[4].pk: 127,
                     self._schuttersboog[5].pk: 128,
                     self._schuttersboog[6].pk: 129}
        with self.assert_max_queries(40):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)
        self.assertEqual(json_data['done'], 1)

        # controleer dat de uitslag nog niet geaccordeerd is
        wed = Wedstrijd.objects.select_related('uitslag').get(pk=self.wedstrijd18_pk)
        self.assertFalse(wed.uitslag.is_bevroren)

        # haal de uitslag op en controleer aanwezigheid 'accorderen' knop
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertIn(ackurl, urls)

        # accordeer de wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.post(ackurl)
        self.assert_is_redirect(resp, url)

        wed = Wedstrijd.objects.select_related('uitslag').get(pk=self.wedstrijd18_pk)
        self.assertTrue(wed.uitslag.is_bevroren)

        # haal de uitslag op en controleer AFwezigheid 'accorderen' knop
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(ackurl, urls)

        # probeer toch nog een keer te accorderen
        with self.assert_max_queries(20):
            resp = self.client.post(ackurl)
        self.assert_is_redirect(resp, url)

        # probeer ook een keer als 'de verkeerde rcl'
        self.e2e_login_and_pass_otp(self.account_rcl101_25)
        self.e2e_wissel_naar_functie(self.functie_rcl101_25)

        with self.assert_max_queries(20):
            resp = self.client.post(ackurl)
        self.assertEqual(resp.status_code, 404)     # 404 = Not allowed

    def test_rcl_bad_opslaan(self):
        # post zonder inlog
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # get (bestaat niet)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post zonder wedstrijd_pk
        json_data = {'hallo': 'daar'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met niet bestaande wedstrijd_pk
        json_data = {'wedstrijd_pk': 999999}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met wedstrijd_pk die nog geen uitslag heeft
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # post met wedstrijd_pk waar deze RCL geen toegang toe heeft
        with self.assert_max_queries(20):
            self.client.get(self.url_uitslag_invoeren % self.wedstrijd25_pk)
        json_data = {'wedstrijd_pk': self.wedstrijd25_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

        # wedstrijd die niet bij de competitie hoort
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd18_pk)
        wedstrijd2 = Wedstrijd(beschrijving="niet in een plan",
                               datum_wanneer=wedstrijd.datum_wanneer,
                               tijd_begin_aanmelden=wedstrijd.tijd_begin_aanmelden,
                               tijd_begin_wedstrijd=wedstrijd.tijd_begin_wedstrijd,
                               tijd_einde_wedstrijd=wedstrijd.tijd_einde_wedstrijd,
                               uitslag=wedstrijd.uitslag)
        wedstrijd2.save()
        json_data = {'wedstrijd_pk': wedstrijd2.pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)       # 404 = not found / not allowed

    def test_hwl(self):
        # log in als RCL en help de HWL
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_uitslag_invoeren % self.wedstrijd18_pk
        ackurl = self.url_uitslag_accorderen % self.wedstrijd18_pk

        # doe eerst een get zodat de wedstrijd.uitslag gegarandeerd is
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # scores aanmaken
        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     self._schuttersboog[0].pk: 123,
                     self._schuttersboog[1].pk: 124,
                     self._schuttersboog[2].pk: 125,
                     self._schuttersboog[3].pk: 126,
                     self._schuttersboog[4].pk: 127,
                     self._schuttersboog[5].pk: 128,
                     self._schuttersboog[6].pk: 129}
        with self.assert_max_queries(40):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)
        self.assertEqual(json_data['done'], 1)

        # controleer dat de uitslag nog niet geaccordeerd is
        wed = Wedstrijd.objects.select_related('uitslag').get(pk=self.wedstrijd18_pk)
        self.assertFalse(wed.uitslag.is_bevroren)

        # haal de uitslag op en controleer AFwezigheid 'accorderen' knop
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(ackurl, urls)

        # laat de RCL de uitslag accorderen
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)
        self.e2e_check_rol('RCL')

        with self.assert_max_queries(20):
            resp = self.client.post(ackurl)
        self.assert_is_redirect(resp, self.url_uitslag_controleren % self.wedstrijd18_pk)
        wed = Wedstrijd.objects.select_related('uitslag').get(pk=self.wedstrijd18_pk)
        self.assertTrue(wed.uitslag.is_bevroren)

        # terug naar HWL rol
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # check dat de uitslag niet meer aan te passen is
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        json_data = {'wedstrijd_pk': self.wedstrijd18_pk,
                     self._schuttersboog[0].pk: 123,
                     self._schuttersboog[6].pk: 129}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 404)

    def _maak_uitslag(self, wedstrijd_pk):
        # log in als RCL om de wedstrijduitslag in te voeren
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        self._schrijf_in_voor_competitie(self.deelcomp_regio101_18,
                                         self._schuttersboog,
                                         1)
        # voer een wedstrijd.uitslag in
        json_data = {'wedstrijd_pk': wedstrijd_pk}
        waarde = 100
        for schutterboog in self._schuttersboog:
            json_data[schutterboog.pk] = waarde
            waarde += 1
        # for

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.wedstrijd18_pk)     # garandeert wedstrijd.uitslag
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        with self.assert_max_queries(91):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)
        self.assertEqual(json_data['done'], 1)

        self.client.logout()

    def test_scores_regio(self):
        # RCL kan scores invoeren / inzien / accorderen voor zijn regio
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        url = self.url_scores_regio % self.deelcomp_regio101_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # zet de ronde uitslag
        score = Score(schutterboog=self._schuttersboog[0],
                      afstand_meter=18,
                      waarde=123)
        score.save()

        uitslag = WedstrijdUitslag(max_score=300,
                                   afstand_meter=18)
        uitslag.save()
        uitslag.scores.add(score)

        ronde = DeelcompetitieRonde.objects.filter(deelcompetitie=self.deelcomp_regio101_18)[0]
        wedstrijd = ronde.plan.wedstrijden.all()[0]
        wedstrijd.uitslag = uitslag
        wedstrijd.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # zet 1 ronde om voor het oude programma
        ronde.beschrijving = 'Ronde 99 oude programma'
        ronde.save()
        self.assertTrue(ronde.is_voor_import_oude_programma())

        url = self.url_scores_regio % self.deelcomp_regio101_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

    def test_scores_regio_bad(self):
        self.e2e_login_and_pass_otp(self.account_rcl101_18)
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # bad deelcomp_pk
        url = self.url_scores_regio % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

        # verkeerde regio
        url = self.url_scores_regio % self.deelcomp_regio101_25.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)     # 404 = Not found

    def test_bekijk_uitslag(self):
        self._maak_uitslag(self.wedstrijd18_pk)
        url = self.url_bekijk_uitslag % self.wedstrijd18_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assert_template_used(resp, ('competitie/scores-bekijken.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

# end of file
