# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from BasisTypen.models import TemplateCompetitieIndivKlasse, TeamType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.tests.test_helpers import zet_competitie_fases, maak_competities_en_zet_fase_b
from Functie.definities import Rollen
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieOverzicht(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, pagina Overzicht """

    test_after = ('Competitie.tests.test_tijdlijn',)

    url_overzicht = '/bondscompetities/%s/'

    @staticmethod
    def _maak_twee_klassen(comp):
        indiv = TemplateCompetitieIndivKlasse.objects.all()[0]
        CompetitieIndivKlasse(competitie=comp, volgorde=1, boogtype=indiv.boogtype, min_ag=0.0).save()

        teamtype = TeamType.objects.all()[0]
        CompetitieTeamKlasse(competitie=comp, volgorde=1, min_ag=0.0, team_type=teamtype).save()

    def test_openbaar(self):
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.begin_fase_C = comp.einde_fase_C = einde_jaar
        comp.begin_fase_F = comp.einde_fase_F = einde_jaar
        comp.datum_klassengrenzen_rk_bk_teams = einde_jaar
        comp.begin_fase_L_indiv = comp.einde_fase_L_indiv = einde_jaar
        comp.begin_fase_L_teams = comp.einde_fase_L_teams = einde_jaar
        comp.begin_fase_P_indiv = comp.einde_fase_P_indiv = einde_jaar
        comp.begin_fase_P_teams = comp.einde_fase_P_teams = einde_jaar
        comp.save()

        zet_competitie_fases(comp, 'A', 'A')

        # altijd openbaar voor BB en BKO
        comp.bepaal_openbaar(Rollen.ROL_BB)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_BKO)
        self.assertTrue(comp.is_openbaar)

        # altijd openbaar voor RKO/RCL/HWL
        comp.bepaal_openbaar(Rollen.ROL_RKO)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_RCL)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_HWL)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_WL)
        self.assertFalse(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_SEC)
        self.assertFalse(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_MO)
        self.assertFalse(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_SPORTER)
        self.assertFalse(comp.is_openbaar)

        # vanaf fase B altijd openbaar
        comp.fase = 'B'

        comp.bepaal_openbaar(Rollen.ROL_SPORTER)
        self.assertTrue(comp.is_openbaar)

    def test_top(self):
        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        way_before = datetime.date(year=2018, month=1, day=1)   # must be before timezone.now()

        comp_18, comp_25 = maak_competities_en_zet_fase_b(startjaar=2020)

        comp = comp_25

        # fase A
        comp.begin_fase_C = now + datetime.timedelta(days=1)      # morgen
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase < 'B', msg="comp.fase=%s (expected: below B)" % comp.fase)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # zet competitie fase B zodat we in mogen schrijven
        zet_competitie_fases(comp, 'B', 'B')

        # uitslagen met competitie in prep fase (B+)
        comp.begin_fase_C = way_before   # fase B
        comp.einde_fase_C = way_before   # fase C
        comp.save()
        comp.bepaal_fase()
        # self.assertTrue(comp.fase >= 'B')
        self.assertTrue(comp.fase >= 'B', msg="comp.fase=%s (expected: not below B)" % comp.fase)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in scorende fase (E+)
        comp.begin_fase_F = way_before     # fase E
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase >= 'E')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))


# end of file
