# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import TemplateCompetitieIndivKlasse, TeamType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.test_utils.tijdlijn import zet_competitie_fases
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompBeheerTijdlijn(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module Tijdlijn """

    test_after = ('Competitie.tests.test_tijdlijn',)

    url_tijdlijn = '/bondscompetities/beheer/%s/tijdlijn/'     # comp_pk

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def test_alle_fases(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # test de helper functie die de competitie fase forceert
        comp = Competitie(
                    begin_jaar=2000,
                    afstand=25,
                    klassengrenzen_vastgesteld=True)
        comp.save()
        comp.refresh_from_db()      # echte datums ipv strings

        indiv = TemplateCompetitieIndivKlasse.objects.first()
        teamtype = TeamType.objects.first()

        CompetitieIndivKlasse(competitie=comp, volgorde=1, boogtype=indiv.boogtype, min_ag=0.0).save()
        CompetitieTeamKlasse(competitie=comp, volgorde=1, min_ag=0.0, team_type=teamtype).save()

        url = self.url_tijdlijn % comp.pk

        sequence = 'ABCDFGJKLNOPQZ'      # noqa
        for fase in sequence:
            zet_competitie_fases(comp, fase, fase)

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'plein/site_layout.dtl'))
        # for


# end of file
