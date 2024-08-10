# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Score.models import Score
from Competitie.models import CompetitieIndivKlasse, CompetitieMatch, RegiocompetitieRonde
from Score.models import Uitslag
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import json


class TestCompScoresScores(E2EHelpers, TestCase):

    """ tests voor de CompScores applicatie, module Scores """

    test_after = ('Competitie.tests.test_overzicht', 'CompLaagRegio.tests.test_planning',)

    url_planning_regio = '/bondscompetities/regio/planning/%s/'                     # deelcomp_pk
    url_planning_cluster = '/bondscompetities/regio/planning/%s/cluster/%s/'        # deelcomp_pk, cluster_pk
    url_planning_regio_ronde = '/bondscompetities/regio/planning/ronde/%s/'         # ronde_pk

    url_uitslag_invoeren = '/bondscompetities/scores/uitslag-invoeren/%s/'          # match_pk
    url_uitslag_opslaan = '/bondscompetities/scores/dynamic/scores-opslaan/'
    url_deelnemers_ophalen = '/bondscompetities/scores/dynamic/deelnemers-ophalen/'
    url_deelnemer_zoeken = '/bondscompetities/scores/dynamic/check-bondsnummer/'

    url_uitslag_controleren = '/bondscompetities/scores/uitslag-controleren/%s/'    # match_pk
    url_uitslag_accorderen = '/bondscompetities/scores/uitslag-accorderen/%s/'      # match_pk

    url_scores_regio = '/bondscompetities/scores/regio/%s/'                         # deelcomp_pk
    url_bekijk_uitslag = '/bondscompetities/scores/bekijk-uitslag/%s/'              # match_pk

    url_regio_teams = '/bondscompetities/scores/teams/%s/'                          # deelcomp_pk

    url_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'     # comp_pk

    ver_nr = 0      # wordt in setUpTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[101][1]
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(18, cls.ver_nr)
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(25, cls.ver_nr)
        cls.testdata.maak_bondscompetities()
        cls.testdata.maak_inschrijvingen_regiocompetitie(18, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regiocompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regio_teamcompetitie(18, ver_nr=cls.ver_nr)
        cls.testdata.maak_inschrijvingen_regio_teamcompetitie(25, ver_nr=cls.ver_nr)
        cls.testdata.maak_poules(cls.testdata.deelcomp18_regio[101])
        cls.testdata.maak_poules(cls.testdata.deelcomp25_regio[101])
        cls.testdata.regio_teamcompetitie_ronde_doorzetten(cls.testdata.deelcomp18_regio[101])
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        # klassengrenzen vaststellen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        resp = self.client.post(self.url_vaststellen % self.testdata.comp18.pk)
        self.assert_is_redirect_not_plein(resp)     # check success
        resp = self.client.post(self.url_vaststellen % self.testdata.comp25.pk)
        self.assert_is_redirect_not_plein(resp)     # check success

        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        # maak een regioplanning aan
        with self.assert_max_queries(20):
            self.client.post(self.url_planning_regio % self.testdata.deelcomp18_regio[101].pk)
        with self.assert_max_queries(20):
            self.client.post(self.url_planning_regio % self.testdata.deelcomp25_regio[101].pk)
        ronde18 = RegiocompetitieRonde.objects.first()
        ronde25 = RegiocompetitieRonde.objects.all()[1]

        # maak een cluster planning aan
        # cluster = self.testdata.regio_cluster[101]
        # with self.assert_max_queries(20):
        #     self.client.post(self.url_planning_cluster % (self.testdata.deelcomp18_regio[101].pk, cluster.pk))

        # maak een wedstrijd aan in elke competitie
        indiv_klassen = CompetitieIndivKlasse.objects.values_list('pk', flat=True)

        self.client.post(self.url_planning_regio_ronde % ronde18.pk, {})
        match = CompetitieMatch.objects.first()
        match.vereniging = self.testdata.functie_hwl[self.ver_nr].vereniging
        match.save()
        match.indiv_klassen.set(indiv_klassen)
        self.match18_pk = match.pk

        self.client.post(self.url_planning_regio_ronde % ronde25.pk, {})
        match = CompetitieMatch.objects.all()[1]
        match.vereniging = self.testdata.functie_hwl[self.ver_nr].vereniging
        match.save()
        match.indiv_klassen.set(indiv_klassen)
        self.wedstrijd25_pk = match.pk

    def test_anon(self):
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.match18_pk)
        self.assert403(resp)      # not allowed

        # scores
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_scores_regio % self.testdata.deelcomp18_regio[101].pk)
        self.assert403(resp)

        # deelnemers
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_deelnemers_ophalen)
        self.assert403(resp)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemers_ophalen)
        self.assert403(resp)

        # zoeken
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_deelnemer_zoeken)
        self.assert403(resp)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemer_zoeken)
        self.assert403(resp)

        # opslaan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_opslaan)
        self.assert403(resp)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan)
        self.assert403(resp)

        # team scores
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.testdata.deelcomp18_regio[101].pk)
        self.assert403(resp)

    def test_rcl_get(self):
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.match18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compscores/scores-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # nog een keer, dan bestaat de WedstrijdUitslag al
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.match18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compscores/scores-invoeren.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # niet bestaande wedstrijd
        resp = self.client.get(self.url_uitslag_invoeren % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_rcl_deelnemers_ophalen(self):
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        # haal waarschijnlijke deelnemers op
        json_data = {'deelcomp_pk': self.testdata.deelcomp18_regio[101].pk,
                     'wedstrijd_pk': self.match18_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemers_ophalen,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')
        json_data = resp.json()
        self.assertTrue('deelnemers' in json_data.keys())
        self.assertEqual(len(json_data['deelnemers']), 60)

        # get (bestaat niet)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_deelnemers_ophalen)
        self.assertEqual(resp.status_code, 405)       # 405 = method not allowed

        # post zonder data
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemers_ophalen)
        self.assert404(resp, 'Geen valide verzoek')

        # post met json data maar zonder inhoud
        json_data = {'testje': 1}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemers_ophalen,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assert404(resp, 'Competitie niet gevonden')

        # post met niet-bestaande deelcomp_pk
        json_data = {'deelcomp_pk': 999999}
        resp = self.client.post(self.url_deelnemers_ophalen,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Competitie niet gevonden')

        # post met niet-bestaande wedstrijd_pk
        json_data = {'deelcomp_pk': self.testdata.deelcomp18_regio[101].pk,
                     'wedstrijd_pk': 999999}
        resp = self.client.post(self.url_deelnemers_ophalen,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_rcl_zoeken(self):
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        json_data = {'wedstrijd_pk': self.match18_pk,
                     'lid_nr': 1}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemer_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')
        json_data = resp.json()
        self.assertTrue('fail' in json_data.keys())     # want geen inschrijvingen

        deelnemer = self.testdata.comp18_deelnemers_geen_team[0]
        self.assertFalse(deelnemer.inschrijf_voorkeur_team)
        sporterboog_pk = deelnemer.sporterboog.pk
        lid_nr = deelnemer.sporterboog.sporter.lid_nr
        json_data = {'wedstrijd_pk': self.match18_pk,
                     'lid_nr': lid_nr}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemer_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')
        json_data = resp.json()
        # print('test_rcl_zoeken: json_data=%s' % repr(json_data))
        self.assertTrue('lid_nr' in json_data)
        self.assertEqual(json_data['lid_nr'], lid_nr)
        self.assertTrue('naam' in json_data)
        self.assertTrue('ver_nr' in json_data)
        self.assertTrue('ver_naam' in json_data)
        self.assertTrue('vereniging' in json_data)
        self.assertTrue('regio' in json_data)
        self.assertTrue('deelnemers' in json_data)
        json_deelnemer = json_data['deelnemers'][0]
        self.assertTrue('pk' in json_deelnemer)
        self.assertEqual(json_deelnemer['pk'], sporterboog_pk)
        self.assertTrue('boog' in json_deelnemer)
        self.assertTrue('team_gem' in json_deelnemer)
        self.assertTrue('team_pk' in json_deelnemer)

        deelnemer = self.testdata.comp18_deelnemers_team[0]
        self.assertTrue(deelnemer.inschrijf_voorkeur_team)
        lid_nr = deelnemer.sporterboog.sporter.lid_nr
        json_data = {'wedstrijd_pk': self.match18_pk,
                     'lid_nr': lid_nr}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemer_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assertEqual(resp['Content-Type'], 'application/json')

    def test_rcl_bad_zoeken(self):
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        # get (bestaat niet)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_deelnemer_zoeken)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemer_zoeken)
        self.assert404(resp, 'Geen valide verzoek')

        # post met alleen een lid_nr
        json_data = {'lid_nr': 0}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemer_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')

        # post met alleen wedstrijd_pk
        json_data = {'wedstrijd_pk': 0}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_deelnemer_zoeken,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')

        # post niet-bestand wedstrijd_pk
        json_data = {'wedstrijd_pk': 999999,
                     'lid_nr': 0}
        resp = self.client.post(self.url_deelnemer_zoeken,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')

    def test_rcl_opslaan(self):
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        # doe eerst een get zodat de wedstrijd.uitslag gegarandeerd is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.match18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # zonder scores
        json_data = {'wedstrijd_pk': self.match18_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # met sporterboog_pk's en scores
        json_data = {'wedstrijd_pk': self.match18_pk,
                     self.testdata.comp18_deelnemers[0].sporterboog.pk: 123,
                     self.testdata.comp18_deelnemers[1].sporterboog.pk: -1,
                     self.testdata.comp18_deelnemers[2].sporterboog.pk: 999999,
                     self.testdata.comp18_deelnemers[3].sporterboog.pk: 'hoi',
                     self.testdata.comp18_deelnemers[4].sporterboog.pk: 100,
                     self.testdata.comp18_deelnemers[5].sporterboog.pk: 101,
                     self.testdata.comp18_deelnemers[6].sporterboog.pk: '',  # verwijderd maar was niet aanwezig
                     'hoi': 1,
                     999999: 111}                           # niet bestaande sporterboog_pk
        # print('json_data for post: %s' % json.dumps(json_data))
        resp = self.client.post(self.url_uitslag_opslaan,
                                json.dumps(json_data),
                                content_type='application/json')
        json_data = self.assert200_json(resp)
        self.assertEqual(json_data['done'], 1)

        # nog een keer opslaan - met mutaties
        json_data = {'wedstrijd_pk': self.match18_pk,
                     self.testdata.comp18_deelnemers[0].sporterboog.pk: 132,  # aangepaste score
                     self.testdata.comp18_deelnemers[4].sporterboog.pk: 100,  # ongewijzigde score
                     self.testdata.comp18_deelnemers[5].sporterboog.pk: ''}   # verwijderde score
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        json_data = self.assert200_json(resp)
        self.assertEqual(json_data['done'], 1)

    def test_rcl_accorderen(self):
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        url = self.url_uitslag_controleren % self.match18_pk
        ack_url = self.url_uitslag_accorderen % self.match18_pk

        # doe eerst een get zodat de wedstrijd.uitslag gegarandeerd is
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # scores aanmaken
        waarde = 123
        json_data = {'wedstrijd_pk': self.match18_pk}
        for deelnemer in self.testdata.comp18_deelnemers[:7]:
            sporterboog = deelnemer.sporterboog
            json_data[sporterboog.pk] = waarde
            waarde += 1
        # for
        with self.assert_max_queries(34):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        json_data = self.assert200_json(resp)
        self.assertEqual(json_data['done'], 1)

        # controleer dat de uitslag nog niet geaccordeerd is
        wed = CompetitieMatch.objects.select_related('uitslag').get(pk=self.match18_pk)
        self.assertFalse(wed.uitslag.is_bevroren)

        # haal de uitslag op en controleer aanwezigheid 'accorderen' knop
        with self.assert_max_queries(22):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('compscores/scores-invoeren.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertIn(ack_url, urls)

        # accordeer de wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.post(ack_url)
        self.assert_is_redirect(resp, url)

        wed = CompetitieMatch.objects.select_related('uitslag').get(pk=self.match18_pk)
        self.assertTrue(wed.uitslag.is_bevroren)

        # haal de uitslag op en controleer afwezigheid 'accorderen' knop
        with self.assert_max_queries(22):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(ack_url, urls)

        # probeer toch nog een keer te accorderen
        with self.assert_max_queries(20):
            resp = self.client.post(ack_url)
        self.assert_is_redirect(resp, url)

        # probeer als HWL de wedstrijd te wijzigen
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])
        self.e2e_check_rol('HWL')

        json_data = {'wedstrijd_pk': self.match18_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assert404(resp, 'Uitslag mag niet meer gewijzigd worden')

        # probeer ook een keer als 'de verkeerde rcl'
        self.e2e_login_and_pass_otp(self.testdata.comp25_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_rcl[101])

        with self.assert_max_queries(20):
            resp = self.client.post(ack_url)
        self.assert403(resp)

    def test_rcl_bad_opslaan(self):
        # post zonder inlog
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        # get (bestaat niet)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_opslaan)
        self.assertEqual(resp.status_code, 405)        # 405 = method not allowed

        # post zonder data
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan)
        self.assert404(resp, 'Geen valide verzoek')

        # post zonder wedstrijd_pk
        json_data = {'hallo': 'daar'}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # post met niet bestaande wedstrijd_pk
        json_data = {'wedstrijd_pk': 999999}
        resp = self.client.post(self.url_uitslag_opslaan,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # post met wedstrijd_pk waar deze RCL geen toegang toe heeft
        with self.assert_max_queries(20):
            self.client.get(self.url_uitslag_invoeren % self.wedstrijd25_pk)
        json_data = {'wedstrijd_pk': self.wedstrijd25_pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assert403(resp)

        # wedstrijd die niet bij de competitie hoort
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren % self.match18_pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        wedstrijd = CompetitieMatch.objects.get(pk=self.match18_pk)
        wedstrijd2 = CompetitieMatch(
                            competitie=self.testdata.comp18,
                            beschrijving="niet in een plan",
                            datum_wanneer=wedstrijd.datum_wanneer,
                            tijd_begin_wedstrijd=wedstrijd.tijd_begin_wedstrijd,
                            uitslag=wedstrijd.uitslag)
        wedstrijd2.save()
        json_data = {'wedstrijd_pk': wedstrijd2.pk}
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        self.assert404(resp, 'Geen regio wedstrijd')

        self.assertTrue(str(wedstrijd2) != '')
        wedstrijd2.vereniging = self.testdata.vereniging[self.testdata.regio_ver_nrs[111][0]]
        self.assertTrue(str(wedstrijd2) != '')

    def test_hwl(self):
        # log in als HWL
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])
        self.e2e_check_rol('HWL')

        url = self.url_uitslag_invoeren % self.wedstrijd25_pk
        ack_url = self.url_uitslag_accorderen % self.wedstrijd25_pk

        # doe eerst een get zodat de wedstrijd.uitslag gegarandeerd is
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        # TODO: check template, anders detecteren we geen situatie 403/404

        # scores aanmaken
        json_data = {'wedstrijd_pk': self.wedstrijd25_pk}
        waarde = 123
        for deelnemer in self.testdata.comp25_deelnemers[:7]:
            json_data[deelnemer.sporterboog.pk] = waarde
            waarde += 1
        # for
        # TODO: niet stabiel!!
        # with self.assert_max_queries(24):  # 24, 27, 33, ...
        resp = self.client.post(self.url_uitslag_opslaan,
                                json.dumps(json_data),
                                content_type='application/json')
        json_data = self.assert200_json(resp)
        self.assertEqual(json_data['done'], 1)

        # controleer dat de uitslag nog niet geaccordeerd is
        wed = CompetitieMatch.objects.select_related('uitslag').get(pk=self.wedstrijd25_pk)
        self.assertFalse(wed.uitslag.is_bevroren)

        # haal de uitslag op en controleer afwezigheid 'accorderen' knop
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertNotIn(ack_url, urls)

        # laat de RCL de uitslag accorderen
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_rcl[101])
        self.e2e_check_rol('RCL')

        with self.assert_max_queries(20):
            resp = self.client.post(ack_url)
        self.assert_is_redirect(resp, self.url_uitslag_controleren % self.wedstrijd25_pk)
        wed = CompetitieMatch.objects.select_related('uitslag').get(pk=self.wedstrijd25_pk)
        self.assertTrue(wed.uitslag.is_bevroren)

        # terug naar HWL rol
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])
        self.e2e_check_rol('HWL')

        # check dat de uitslag niet meer aan te passen is
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

    def _maak_uitslag(self, match_pk):
        # log in als RCL om de wedstrijduitslag in te voeren
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        # maak de data set
        json_data = {'wedstrijd_pk': match_pk}
        waarde = 100
        for deelnemer in self.testdata.comp18_deelnemers:
            sporterboog = deelnemer.sporterboog
            json_data[sporterboog.pk] = waarde
            waarde += 1
        # for

        with self.assert_max_queries(252):
            resp = self.client.post(self.url_uitslag_opslaan,
                                    json.dumps(json_data),
                                    content_type='application/json')
        json_data = self.assert200_json(resp)
        self.assertEqual(json_data['done'], 1)

        self.client.logout()

    def test_scores_regio(self):
        # RCL kan scores invoeren / inzien / accorderen voor zijn regio
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        url = self.url_scores_regio % self.testdata.deelcomp18_regio[101].pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # zet de ronde uitslag
        score = Score(sporterboog=self.testdata.comp18_deelnemers[0].sporterboog,
                      afstand_meter=18,
                      waarde=123)
        score.save()

        uitslag = Uitslag(max_score=300,
                          afstand=18)
        uitslag.save()
        uitslag.scores.add(score)

        ronde = RegiocompetitieRonde.objects.filter(regiocompetitie=self.testdata.deelcomp18_regio[101])[0]
        match = ronde.matches.first()
        match.uitslag = uitslag
        match.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        url = self.url_scores_regio % self.testdata.deelcomp18_regio[101].pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # bad deelcomp_pk
        url = self.url_scores_regio % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # verkeerde regio
        url = self.url_scores_regio % self.testdata.deelcomp25_regio[101].pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_bekijk_uitslag(self):
        self._maak_uitslag(self.match18_pk)     # logt uit

        # log in als HWL
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])
        self.e2e_check_rol('HWL')

        url = self.url_bekijk_uitslag % self.match18_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assert_template_used(resp, ('compscores/scores-bekijken.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_scores_teams(self):
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[101])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[101])

        # bad deelcomp_pk
        resp = self.client.get(self.url_regio_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_regio_teams % "xyz")
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_regio_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        deelcomp = self.testdata.deelcomp18_regio[101]

        with self.assert_max_queries(49):
            resp = self.client.get(self.url_regio_teams % deelcomp.pk)
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assert_template_used(resp, ('compscores/rcl-scores-regio-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # do een post
        with self.assert_max_queries(65):
            resp = self.client.post(self.url_regio_teams % deelcomp.pk)
        self.assert_is_redirect_not_plein(resp)

        # verkeerde deelcomp
        bad_deelcomp = self.testdata.deelcomp25_regio[101]
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % bad_deelcomp.pk)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_regio_teams % bad_deelcomp.pk)
        self.assert403(resp)

        # zet ronde = 0
        deelcomp.huidige_team_ronde = 0
        deelcomp.save(update_fields=['huidige_team_ronde'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % deelcomp.pk)
        self.assertEqual(resp.status_code, 200)       # 200 = OK
        self.assert_template_used(resp, ('compscores/rcl-scores-regio-teams.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # regio organiseert geen teamcompetitie
        deelcomp.regio_organiseert_teamcompetitie = False
        deelcomp.save(update_fields=['regio_organiseert_teamcompetitie'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % deelcomp.pk)
        self.assert404(resp, 'Geen teamcompetitie in deze regio')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_regio_teams % deelcomp.pk)
        self.assert404(resp, 'Geen teamcompetitie in deze regio')

# end of file
