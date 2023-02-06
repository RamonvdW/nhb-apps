# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import TemplateCompetitieIndivKlasse, TeamType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.tijdlijn import bepaal_fase_indiv, bepaal_fase_teams
from Competitie.tests.test_helpers import zet_competitie_fases
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieTijdlijn(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, pagina Overzicht """

    url_overzicht = '/bondscompetities/%s/'

    @staticmethod
    def _maak_twee_klassen(comp):
        indiv = TemplateCompetitieIndivKlasse.objects.all()[0]
        CompetitieIndivKlasse(competitie=comp, volgorde=1, boogtype=indiv.boogtype, min_ag=0.0).save()

        teamtype = TeamType.objects.all()[0]
        CompetitieTeamKlasse(competitie=comp, volgorde=1, min_ag=0.0, team_type=teamtype).save()

    def _dump_comp(self, comp, msg=''):
        print('\nCompetitie dump:')
        if msg:
            print(msg)
        print('  afstand: %s' % repr(comp.afstand))
        print('  begin_jaar: %s' % repr(comp.begin_jaar))
        print('  klassegrenzen_vastgesteld: %s' % repr(comp.klassengrenzen_vastgesteld))
        print('  begin_fase_C: %s' % repr(comp.begin_fase_C))
        print('  einde_fase_C: %s' % repr(comp.einde_fase_C))
        print('  begin_fase_F: %s' % repr(comp.begin_fase_F))
        print('  einde_fase_F: %s' % repr(comp.einde_fase_F))
        print('  regiocompetitie_is_afgesloten: %s' % repr(comp.regiocompetitie_is_afgesloten))
        print('  datum_klassengrenzen_rk_bk_teams: %s' % repr(comp.datum_klassengrenzen_rk_bk_teams))
        print('  klassengrenzen_vastgesteld_rk_bk: %s' % repr(comp.klassengrenzen_vastgesteld_rk_bk))
        print('  begin_fase_L_indiv: %s' % repr(comp.begin_fase_L_indiv))
        print('  einde_fase_L_indiv: %s' % repr(comp.einde_fase_L_indiv))
        print('  begin_fase_L_teams: %s' % repr(comp.begin_fase_L_teams))
        print('  einde_fase_L_teams: %s' % repr(comp.einde_fase_L_teams))
        print('  rk_indiv_afgesloten: %s' % repr(comp.rk_indiv_afgesloten))
        print('  rk_teams_afgesloten: %s' % repr(comp.rk_teams_afgesloten))
        print('  bk_indiv_klassen_zijn_samengevoegd: %s' % repr(comp.bk_indiv_klassen_zijn_samengevoegd))
        print('  bk_teams_klassen_zijn_samengevoegd: %s' % repr(comp.bk_teams_klassen_zijn_samengevoegd))
        print('  begin_fase_P_indiv: %s' % repr(comp.begin_fase_P_indiv))
        print('  einde_fase_P_indiv: %s' % repr(comp.einde_fase_P_indiv))
        print('  begin_fase_P_teams: %s' % repr(comp.begin_fase_P_teams))
        print('  einde_fase_P_teams: %s' % repr(comp.einde_fase_P_teams))
        print('  bk_indiv_afgesloten: %s' % repr(comp.bk_indiv_afgesloten))
        print('  bk_teams_afgesloten: %s' % repr(comp.bk_teams_afgesloten))
        print('  is_afgesloten: %s' % repr(comp.is_afgesloten))

    def test_zet_fase_indiv(self):
        # test de helper functie die de competitie fase forceert
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie(
                    begin_jaar=2000,
                    einde_fase_C=einde_jaar,
                    datum_klassengrenzen_rk_bk_teams=einde_jaar)
        comp.save()
        comp = Competitie.objects.get(pk=comp.pk)

        self.assertEqual(bepaal_fase_indiv(comp), 'A')

        zet_competitie_fases(comp, 'A', 'A')
        self.assertEqual(bepaal_fase_indiv(comp), 'A')

        # maak de klassen aan en controleer de fase weer
        self._maak_twee_klassen(comp)
        zet_competitie_fases(comp, 'A', 'A')
        self.assertEqual(bepaal_fase_indiv(comp), 'A')

        comp.klassengrenzen_vastgesteld = True
        zet_competitie_fases(comp, 'A', 'A')
        self.assertEqual(bepaal_fase_indiv(comp), 'A')

        sequence = 'BCFGJKLNOPQZQPONLKJGFCB'
        for fase in sequence:
            zet_competitie_fases(comp, fase, fase)
            # if fase in ('P', 'Q'):
            #     self._dump_comp(comp, 'Fase %s' % fase)
            indiv_fase = bepaal_fase_indiv(comp)
            self.assertEqual(indiv_fase, fase)
        # for

        for fase in sequence:
            zet_competitie_fases(comp, fase, fase)
            comp.save()
            comp = Competitie.objects.get(pk=comp.pk)
            indiv_fase = bepaal_fase_indiv(comp)
            self.assertEqual(indiv_fase, fase)
        # for

    def test_zet_fase_team(self):
        # test de helper functie die de competitie fase forceert
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie(
                    begin_jaar=2000,
                    einde_fase_C=einde_jaar,
                    datum_klassengrenzen_rk_bk_teams=einde_jaar)
        comp.save()
        comp = Competitie.objects.get(pk=comp.pk)

        self.assertEqual(bepaal_fase_indiv(comp), 'A')
        self.assertEqual(bepaal_fase_teams(comp), 'A')

        zet_competitie_fases(comp, 'A', 'A')
        self.assertEqual(bepaal_fase_indiv(comp), 'A')
        self.assertEqual(bepaal_fase_teams(comp), 'A')

        # maak de klassen aan en controleer de fase weer
        self._maak_twee_klassen(comp)
        zet_competitie_fases(comp, 'A', 'A')
        self.assertEqual(bepaal_fase_indiv(comp), 'A')
        self.assertEqual(bepaal_fase_teams(comp), 'A')

        comp.klassengrenzen_vastgesteld = True
        zet_competitie_fases(comp, 'A', 'A')
        self.assertEqual(bepaal_fase_indiv(comp), 'A')
        self.assertEqual(bepaal_fase_teams(comp), 'A')

        sequence = 'BCFGJKLNOPQZQPONLKJGFCB'        # let op: D wordt niet ondersteund
        for fase in sequence:
            zet_competitie_fases(comp, fase, fase)
            # if fase in ('L', 'N'):
            #     self._dump_comp(comp, 'Fase %s' % fase)
            fase_teams = bepaal_fase_teams(comp)
            self.assertEqual(fase_teams, fase)
        # for

        for fase in sequence:
            zet_competitie_fases(comp, fase, fase)
            comp.save()
            comp = Competitie.objects.get(pk=comp.pk)
            fase_teams = bepaal_fase_teams(comp)
            self.assertEqual(fase_teams, fase)
        # for
# end of file
