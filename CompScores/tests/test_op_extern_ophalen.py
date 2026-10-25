# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import CompetitieIndivKlasse, CompetitieMatch
from CompLaagRegio.models import RegioRonde
from CompScores.operations.uitslag_extern_ophalen import comp_scores_uitslag_extern_ophalen
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
from TestHelpers.testdata import TestData
from Vereniging.definities import TYPE_EXTERNE_SCORES_CENTAUR, TYPE_EXTERNE_SCORES_ONBEKEND
from Vereniging.models import ExterneScores
from requests.exceptions import SSLError
from unittest.mock import patch


class ResponseMock:

    def __init__(self, status_code: int=200, give_token: bool=True, nr_of_results: int=0):
        self.is_auth = True
        self.status_code = status_code
        self.give_token = give_token
        self.nr_of_results = nr_of_results

    def json(self):
        d = dict()

        if self.is_auth:
            # authenticatie
            self.is_auth = False
            if self.give_token:
                d['token'] = '1234'
        else:
            if self.nr_of_results >= 0:
                d['results'] = res = list()

                if self.nr_of_results >= 1:
                    # slecht score, wordt overgeslagen
                    res.append({'score': '', 'lidnummer': '', 'boogtype': ''})

                    # te hoge score, wordt overgeslagen
                    res.append({'score': '301', 'lidnummer': '', 'boogtype': ''})

                    # onbekende deelnemer
                    res.append({'score': '200', 'lidnummer': '100001', 'boogtype': 'Recurve'})

                    if self.nr_of_results > 4:
                        # deelnemer 1
                        res.append({'score': '200', 'lidnummer': '300344', 'boogtype': 'Recurve'})

                        # deelnemer 2; heeft 2 bogen
                        res.append({'score': '280', 'lidnummer': '300326', 'boogtype': 'Compound'})

                        # deelnemer 3
                        res.append({'score': '190', 'lidnummer': '300339', 'boogtype': 'Barebow'})
                    else:
                        # deelnemer 1, aangepaste score
                        res.append({'score': '222', 'lidnummer': '300344', 'boogtype': 'Recurve'})

                        # deelnemer 2 is verwijderd

                        # deelnemer 3, zelfde score
                        res.append({'score': '190', 'lidnummer': '300339', 'boogtype': 'Barebow'})


            elif self.nr_of_results == -2:
                d['results'] = -2        # not a list

        return d


class TestCompScoresOpExternOphalen(E2EHelpers, TestCase):

    """ tests voor de CompScores applicatie, module operations: uitslag extern ophalen """

    url_planning_regio = '/bondscompetities/regio/planning/%s/'                     # deelcomp_pk
    url_planning_regio_ronde = '/bondscompetities/regio/planning/ronde/%s/'         # ronde_pk
    url_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'     # comp_pk

    ver_nr = 0      # wordt in setUpTestData ingevuld
    regio_nr = 102

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][1]
        cls.testdata.maak_sporterboog_aanvangsgemiddelden(18, cls.ver_nr)
        cls.testdata.maak_bondscompetities()
        cls.testdata.maak_inschrijvingen_regiocompetitie(18, ver_nr=cls.ver_nr)
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        # klassengrenzen vaststellen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        resp = self.client.post(self.url_vaststellen % self.testdata.comp18.pk)
        self.assert_is_redirect_not_plein(resp)     # check success

        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[self.regio_nr])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[self.regio_nr])

        # maak een regioplanning aan
        with self.assert_max_queries(20):
            self.client.post(self.url_planning_regio % self.testdata.deelcomp18_regio[self.regio_nr].pk)
        self.ronde18 = RegioRonde.objects.first()
        assert self.ronde18 is not None

        # maak een wedstrijd aan
        indiv_klassen = CompetitieIndivKlasse.objects.values_list('pk', flat=True)

        self.client.post(self.url_planning_regio_ronde % self.ronde18.pk, {})
        match = CompetitieMatch.objects.first()
        assert match is not None
        match.vereniging = self.testdata.functie_hwl[self.ver_nr].vereniging
        match.save()
        match.indiv_klassen.set(indiv_klassen)
        self.match18 = match

        self.ver = self.testdata.vereniging[self.ver_nr]

        self.ext = ExterneScores.objects.create(
                            is_actief=False,
                            vereniging=self.ver,
                            type=TYPE_EXTERNE_SCORES_CENTAUR,
                            url_auth='https://test.not/api/auth/',
                            url_ophalen='https://test.not/api/ophalen/',
                            username='secret_name',
                            password='secret_pass')

        # for deelnemer in self.testdata.comp18_deelnemers:
        #     print(deelnemer)

    def test_extern(self):
        # niet actief
        stdout = OutputBuffer()
        comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("heeft geen externe scores geconfigureerd" in stdout.getvalue())

        self.ext.is_actief = True
        self.ext.save(update_fields=['is_actief'])

        # SSLError
        stdout = OutputBuffer()
        with patch('requests.post', side_effect=SSLError('uitzondering')):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("[ERROR] {ExterneScoresCentaur._fetch_token} Onverwachte fout tijdens authenticatie: uitzondering" in stdout.getvalue())

        # foutcode
        stdout = OutputBuffer()
        resp = ResponseMock(status_code=404)
        with patch('requests.post', return_value=resp):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("[ERROR] {ExterneScoresCentaur._fetch_token} Onverwachte status tijdens authenticatie: 404" in stdout.getvalue())

        # geen token
        stdout = OutputBuffer()
        resp = ResponseMock(give_token=False)
        with patch('requests.post', return_value=resp):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("[ERROR] {ExterneScoresCentaur._fetch_token} Geen token gekregen tijdens authenticatie: data=" in stdout.getvalue())

        # geen resultaten
        stdout = OutputBuffer()
        resp = ResponseMock(nr_of_results=-1)
        with patch('requests.post', return_value=resp):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("[INFO] {ExterneScoresCentaur._fetch_token} token ontvangen (len=4)" in stdout.getvalue())
        self.assertTrue("[ERROR] {ExterneScoresCentaur._fetch_uitslag} Geen results in data {}" in stdout.getvalue())

        # SSLError tijdens tweede request
        stdout = OutputBuffer()
        resp = ResponseMock(nr_of_results=-1)
        with patch('requests.post', side_effect=[resp, SSLError('uitzondering')]):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("[ERROR] {ExterneScoresCentaur._fetch_uitslag} Onverwachte fout tijdens ophalen: uitzondering" in stdout.getvalue())

        # foutcode
        stdout = OutputBuffer()
        resp1 = ResponseMock(nr_of_results=0)
        resp2 = ResponseMock(status_code=404)
        with patch('requests.post', side_effect=[resp1, resp2]):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("[ERROR] {ExterneScoresCentaur._fetch_uitslag} Onverwachte status tijdens ophalen: 404" in stdout.getvalue())

        # verkeerde resultaten
        stdout = OutputBuffer()
        resp = ResponseMock(nr_of_results=-2)
        with patch('requests.post', return_value=resp):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        # print(stdout.getvalue())
        self.assertTrue("[ERROR] {ExterneScoresCentaur._fetch_uitslag} results in data is geen lijst {'results': -2}" in stdout.getvalue())

        # lege resultaten
        stdout = OutputBuffer()
        resp = ResponseMock(nr_of_results=0)
        with patch('requests.post', return_value=resp):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("ERROR] {ExterneScoresCentaur._fetch_uitslag} Geen results in data {'results': []}" in stdout.getvalue())

        # met echte data
        # dit maakt ook de uitslag aan
        stdout = OutputBuffer()
        resp = ResponseMock(nr_of_results=5)
        with patch('requests.post', return_value=resp):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        # print(stdout.getvalue())
        self.assertTrue("[ERROR] {ExterneScoresCentaur._uitslag_opslaan} slechte score waarde: ''" in stdout.getvalue())
        self.assertTrue("[ERROR] {ExterneScoresCentaur._uitslag_opslaan} slechte score waarde: '301'" in stdout.getvalue())
        self.assertTrue("[WARNING] {ExterneScoresCentaur._uitslag_opslaan} is geen regio deelnemer: ('100001', 'Recurve')" in stdout.getvalue())

        self.match18.refresh_from_db()
        count = self.match18.uitslag.scores.count()
        self.assertEqual(count, 3)

        # nog een keer - geeft andere coverage
        # verwijdert 1 uit de uitslag
        stdout = OutputBuffer()
        resp = ResponseMock(nr_of_results=1)
        with patch('requests.post', return_value=resp):
            comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        # print(stdout.getvalue())
        self.assertTrue("[INFO] {ExterneScoresCentaur._uitslag_opslaan} bijgewerkte score:" in stdout.getvalue())
        self.assertTrue("[INFO] {ExterneScoresCentaur._uitslag_opslaan} verwijder uit uitslag:" in stdout.getvalue())

        # verwijderde score: sporter staat er nog steeds in, met speciale score
        count = self.match18.uitslag.scores.count()
        self.assertEqual(count, 3)

        # onbekend type
        self.ext.type = TYPE_EXTERNE_SCORES_ONBEKEND
        self.ext.save(update_fields=['type'])
        stdout = OutputBuffer()
        comp_scores_uitslag_extern_ophalen(stdout, self.testdata.account_bb, self.ver, self.match18)
        self.assertTrue("ExterneSscores.type 0 niet geimplementeerd" in stdout.getvalue())

# end of file
