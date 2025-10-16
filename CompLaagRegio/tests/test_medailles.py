# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import RegiocompetitieSporterBoog
from CompLaagRegio.view_medailles import bepaal_medailles
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from types import SimpleNamespace


class TestCompLaagRegioMedailles(E2EHelpers, TestCase):

    """ tests voor de CompLaagRegio applicatie, functies voor Medailles """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_medailles = '/bondscompetities/regio/medailles/regio-%s/'      # regio nr

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_bondscompetities()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_medailles(self):

        regio_nr = 111
        url = self.url_medailles % regio_nr

        # zonder inlog
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert_is_redirect(resp, '/account/login/')

        # login
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        # probeer als niet-RCL
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        self.e2e_check_rol('BKO')
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # probeer als RCL
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[111])
        self.e2e_check_rol('RCL')

        # niet bestaande regio
        resp = self.client.get(self.url_medailles % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_medailles % 'xxx')
        self.assert404(resp, 'Competitie niet gevonden')

        # TODO: verkeerde fase
        # with self.assert_max_queries(20):
        #     resp = self.client.get(url)
        # self.assert404(resp)

        ver_nr = self.testdata.regio_ver_nrs[111][0]
        self.testdata.maak_sporterboog_aanvangsgemiddelden(18, ver_nr)
        self.testdata.maak_inschrijvingen_regiocompetitie(ver_nr=ver_nr)

        # geef alle deelnemers genoeg scores
        prev_volgorde = None
        nr = 0
        aantal = 0
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__regio__regio_nr=111)
                          .select_related('indiv_klasse')
                          .order_by('indiv_klasse')):
            if deelnemer.indiv_klasse.volgorde != prev_volgorde:
                prev_volgorde = deelnemer.indiv_klasse.volgorde
                nr += 1
                aantal = 0

            aantal += 1
            if nr == 1:             # heeft 16 deelnemers: 3 medailles
                # goud, zilver, brons
                if aantal <= 3:
                    deelnemer.gemiddelde = 10.0 - aantal

            elif nr == 9:           # heeft 5 deelnemers: 2 medailles
                # goud, zilver, zilver
                if aantal == 1:
                    deelnemer.gemiddelde = 9.0
                elif aantal in (2, 3):
                    deelnemer.gemiddelde = 8.0

            elif nr == 6:           # heeft 12 deelnemers: 3 medailles
                # goud, zilver, brons, brons
                if aantal == 1:
                    deelnemer.gemiddelde = 9.0
                elif aantal == 2:
                    deelnemer.gemiddelde = 8.0
                elif aantal in (3, 4):
                    deelnemer.gemiddelde = 7.0

            # print(nr, aantal, deelnemer.gemiddelde)

            deelnemer.aantal_scores = 6
            deelnemer.save(update_fields=['aantal_scores', 'gemiddelde'])
        # for

        deelcomp = self.testdata.deelcomp18_regio[regio_nr]
        deelcomp.huidige_team_ronde = 6
        deelcomp.save(update_fields=['huidige_team_ronde'])

        # de echte pagina
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/medailles.dtl', 'design/site_layout.dtl'))

        # regio zonder sporters
        # ook: elke RCL mag de medailles van elke regio inzien
        url = self.url_medailles % 110
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

        uitslag = list()
        for rank in range(9):
            deelnemer = SimpleNamespace(rank=rank+1, toon_goud=False, toon_zilver=False, toon_brons=False)
            uitslag.append(deelnemer)
        # for
        bepaal_medailles(uitslag, False)
        self.assertEqual([uitslag[0].toon_goud, uitslag[0].toon_zilver, uitslag[0].toon_brons], [True, False, False])
        self.assertEqual([uitslag[1].toon_goud, uitslag[1].toon_zilver, uitslag[1].toon_brons], [False, True, False])
        self.assertEqual([uitslag[2].toon_goud, uitslag[2].toon_zilver, uitslag[2].toon_brons], [False, False, True])
        self.assertEqual([uitslag[3].toon_goud, uitslag[3].toon_zilver, uitslag[3].toon_brons], [False, False, False])

        # goud, goud, brons
        uitslag = list()
        for rank in range(9):
            deelnemer = SimpleNamespace(rank=rank+1, toon_goud=False, toon_zilver=False, toon_brons=False)
            uitslag.append(deelnemer)
        # for
        uitslag[1].rank = 1
        bepaal_medailles(uitslag, False)
        self.assertEqual([uitslag[0].toon_goud, uitslag[0].toon_zilver, uitslag[0].toon_brons], [True, False, False])
        self.assertEqual([uitslag[1].toon_goud, uitslag[1].toon_zilver, uitslag[1].toon_brons], [True, False, False])
        self.assertEqual([uitslag[2].toon_goud, uitslag[2].toon_zilver, uitslag[2].toon_brons], [False, False, True])
        self.assertEqual([uitslag[3].toon_goud, uitslag[3].toon_zilver, uitslag[3].toon_brons], [False, False, False])

        # maar 1 medaille bij 3 deelnemers
        uitslag = list()
        for rank in range(3):
            deelnemer = SimpleNamespace(rank=rank+1, toon_goud=False, toon_zilver=False, toon_brons=False)
            uitslag.append(deelnemer)
        # for
        bepaal_medailles(uitslag, False)
        self.assertEqual([uitslag[0].toon_goud, uitslag[0].toon_zilver, uitslag[0].toon_brons], [True, False, False])
        self.assertEqual([uitslag[1].toon_goud, uitslag[1].toon_zilver, uitslag[1].toon_brons], [False, False, False])
        self.assertEqual([uitslag[2].toon_goud, uitslag[2].toon_zilver, uitslag[2].toon_brons], [False, False, False])

        # altijd goud, zilver, brons voor aspiranten
        uitslag = list()
        for rank in range(4):
            deelnemer = SimpleNamespace(rank=rank+1, toon_goud=False, toon_zilver=False, toon_brons=False)
            uitslag.append(deelnemer)
        # for
        bepaal_medailles(uitslag, True)
        self.assertEqual([uitslag[0].toon_goud, uitslag[0].toon_zilver, uitslag[0].toon_brons], [True, False, False])
        self.assertEqual([uitslag[1].toon_goud, uitslag[1].toon_zilver, uitslag[1].toon_brons], [False, True, False])
        self.assertEqual([uitslag[2].toon_goud, uitslag[2].toon_zilver, uitslag[2].toon_brons], [False, False, True])
        self.assertEqual([uitslag[3].toon_goud, uitslag[3].toon_zilver, uitslag[3].toon_brons], [False, False, False])


# end of file
