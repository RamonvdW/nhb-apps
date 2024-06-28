# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import TEAM_PUNTEN_MODEL_FORMULE1
from Competitie.models import RegiocompetitieTeamPoule, RegiocompetitieRondeTeam


class Command(BaseCommand):
    help = "Controleer wedstrijdpunten Formule 1"

    def __init__(self):
        super().__init__()

        self.deelcomp_poule_msg = ''
        self.teams = list()

    def _check_wp_f1(self):
        if len(self.teams) > 0:

            if self.deelcomp_poule_msg:
                self.stdout.write("[INFO] Controle " + self.deelcomp_poule_msg)
                self.deelcomp_poule_msg = ''

            prev_team = self.teams[0]
            for team in self.teams[1:]:
                if team.team_score > 0 and team.team_score == prev_team.team_score:
                    if prev_team.team_punten != team.team_punten:
                        self.stdout.write(
                            '[WARNING] Verschillende WP voor zelfde score! Corrigeer in ronde team pk %s' % team.pk)
                        self.stdout.write(
                            '   %3s  %2s  %s' % (prev_team.team_score, prev_team.team_punten, prev_team))
                        self.stdout.write(
                            '   %3s  %2s  %s' % (team.team_score, team.team_punten, team))

                prev_team = team
            # for

            self.teams = list()

    def handle(self, *args, **options):

        for poule in (RegiocompetitieTeamPoule
                      .objects
                      .filter(regiocompetitie__regio_team_punten_model=TEAM_PUNTEN_MODEL_FORMULE1)
                      .order_by('regiocompetitie__competitie',
                                'regiocompetitie__regio__regio_nr',
                                'beschrijving')):

            self.deelcomp_poule_msg = "%s poule %s: %s" % (poule.regiocompetitie, poule.pk, poule)

            # poule bevat teams
            team_pks = list(poule.teams.values_list('pk', flat=True))

            # teams hebben rondes
            prev_ronde = -1
            for team_ronde in (RegiocompetitieRondeTeam
                               .objects
                               .filter(team__pk__in=team_pks)
                               .order_by('ronde_nr',
                                         'team_score',          # groeperen
                                         '-team_punten')):      # hoogste eerst, laatste aanpassen

                if prev_ronde != team_ronde.ronde_nr:
                    # controleer de scores en reset de tellers
                    self._check_wp_f1()
                    prev_ronde = team_ronde.ronde_nr

                self.teams.append(team_ronde)
            # for

            # controleer de laatste ronde
            self._check_wp_f1()
        # for

# end of file
