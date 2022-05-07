# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import RegioCompetitieSchutterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRegioWieSchietWaar(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, functies voor Wie schiet waar """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_medailles = '/bondscompetities/regio/medailles/regio-%s/'      # regio nr

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_bondscompetities()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_medailles(self):

        url = self.url_medailles % 111

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

        # TODO: verkeerde fase
        # with self.assert_max_queries(20):
        #     resp = self.client.get(url)
        # self.assert404(resp)

        ver_nr = self.testdata.regio_ver_nrs[111][0]
        self.testdata.maak_sporterboog_aanvangsgemiddelden(18, ver_nr)
        self.testdata.maak_inschrijvingen_regiocompetitie(ver_nr=ver_nr)
        # geef alle deelnemers genoeg scores
        for deelnemer in RegioCompetitieSchutterBoog.objects.all():
            deelnemer.aantal_scores = 6
            deelnemer.save(update_fields=['aantal_scores'])
        # for

        # de echte pagina
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/medailles.dtl', 'plein/site_layout.dtl'))

        # regio zonder sporters
        url = self.url_medailles % 110
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK

# end of file
