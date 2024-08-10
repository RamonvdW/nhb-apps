# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamType, ORGANISATIE_WA
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, Regiocompetitie,
                               RegiocompetitieSporterBoog, RegiocompetitieTeam)
from Competitie.operations import competities_aanmaken
from Geo.models import Regio
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestCompInschrijvenCliCorrigeerTeamAG(E2EHelpers, TestCase):
    """ unittests voor de CompInschrijven applicatie, management command meld_rcl_nieuwe_inschrijvingen """

    def _maak_deelnemer(self, lid_nr, geslacht, voornaam, achternaam, same_ag=False):
        sporter = Sporter(
                            lid_nr=lid_nr,
                            geslacht=geslacht,
                            voornaam=voornaam,
                            achternaam=achternaam,
                            email="pijlhaler@test.not",
                            geboorte_datum="1972-03-04",
                            sinds_datum="2010-11-12",
                            bij_vereniging=self.ver)
        sporter.save()
        self.sporters.append(sporter)

        sporterboog = SporterBoog(
                                sporter=sporter,
                                boogtype=self.boog_c,
                                voor_wedstrijd=True)
        sporterboog.save()
        self.sportersboog.append(sporterboog)

        deelnemer = RegiocompetitieSporterBoog(
                                regiocompetitie=self.deelcomp103_18m,
                                sporterboog=sporterboog,
                                bij_vereniging=self.ver,
                                indiv_klasse=self.indiv_klasse_c,
                                ag_voor_team_mag_aangepast_worden=True,
                                ag_voor_indiv="7",
                                ag_voor_team="6.5")
        if same_ag:
            deelnemer.ag_voor_team = deelnemer.ag_voor_indiv

        deelnemer.save()
        self.deelnemers.append(deelnemer)

    def setUp(self):
        """ initialisatie van de test case """

        # comp en deelcomp nodig
        competities_aanmaken(2023)

        self.regio_103 = Regio.objects.get(regio_nr=103)
        self.boog_c = BoogType.objects.get(afkorting='C', organisatie=ORGANISATIE_WA)

        self.comp_18m = Competitie.objects.get(afstand='18')

        self.deelcomp103_18m = (Regiocompetitie
                                .objects
                                .get(competitie=self.comp_18m,
                                     regio__regio_nr=103))

        self.indiv_klasse_c = (CompetitieIndivKlasse
                               .objects
                               .filter(competitie=self.comp_18m,
                                       boogtype=self.boog_c,
                                       is_ook_voor_rk_bk=False)
                               .all())[0]

        self.team_type_c = TeamType.objects.get(afkorting='C')

        self.team_klasse_bb = CompetitieTeamKlasse.objects.filter(team_type=self.team_type_c).first()
        self.team_klasse_bb.min_ag = "30"
        self.team_klasse_bb.save(update_fields=['min_ag'])

        # maak een test vereniging
        self.ver = Vereniging(
                        naam="Grote Club",
                        ver_nr="1000",
                        regio=self.regio_103)
        self.ver.save()

        self.sporters = list()
        self.sportersboog = list()
        self.deelnemers = list()

        self._maak_deelnemer(100001, "M", "Gert", "Pijlhaler")
        self._maak_deelnemer(100002, "V", "Gertruud", "Pijlhaler", same_ag=True)
        self._maak_deelnemer(100003, "M", "Jonkie", "Pijlhaler")

        self.beheerder = self.e2e_create_account('100002', 'beheerder@test.not', 'Beheerdertje')

        self.team = RegiocompetitieTeam(
                            regiocompetitie=self.deelcomp103_18m,
                            vereniging=self.ver,
                            volg_nr=1,
                            team_type=self.team_type_c,
                            team_naam='test',
                            aanvangsgemiddelde="15")
        self.team.save()

    def test_basis(self):
        self.team.leden.set(self.deelnemers)
        f1, f2 = self.run_management_command('corrigeer_regio_team_ag')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertFalse('[ERROR]' in f2.getvalue())

        # wijzigingen door laten voeren met gedeeltelijk team
        # --> team_ag wordt op 0 gezet
        self.team.leden.set(self.deelnemers[:2])
        f1, f2 = self.run_management_command('corrigeer_regio_team_ag', '--commit')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertFalse('[ERROR]' in f2.getvalue())

        # wijzigingen door laten voeren met volledig team
        self.team.leden.set(self.deelnemers)
        # --> team_ag wordt op 21 gezet
        deelnemer = RegiocompetitieSporterBoog.objects.get(pk=self.deelnemers[0].pk)
        deelnemer.ag_voor_team = "5"
        deelnemer.ag_voor_team_mag_aangepast_worden = True
        deelnemer.save(update_fields=['ag_voor_team_mag_aangepast_worden', 'ag_voor_team'])
        f1, f2 = self.run_management_command('corrigeer_regio_team_ag', '--commit')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertFalse('[ERROR]' in f2.getvalue())

        # nog een keer, nu zonder wijziging van team_ag
        deelnemer = RegiocompetitieSporterBoog.objects.get(pk=self.deelnemers[0].pk)
        deelnemer.ag_voor_team = "5"
        deelnemer.ag_voor_team_mag_aangepast_worden = True
        deelnemer.save(update_fields=['ag_voor_team_mag_aangepast_worden', 'ag_voor_team'])
        f1, f2 = self.run_management_command('corrigeer_regio_team_ag', '--commit')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertFalse('[ERROR]' in f1.getvalue())
        self.assertFalse('[ERROR]' in f2.getvalue())


# end of file
