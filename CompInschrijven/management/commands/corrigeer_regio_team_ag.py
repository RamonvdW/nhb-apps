# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import CompetitieTeamKlasse, RegiocompetitieSporterBoog, RegiocompetitieTeam
from Score.definities import AG_NUL


class Command(BaseCommand):
    help = "Corrigeer automatisch team AG voor regio inschrijvingen"
    # deze was overschreven met een handmatig team AG

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Wijzigingen doorvoeren')

    def _update_team(self, team, ags, do_commit):
        klasse_oud = team.team_klasse
        team.team_klasse = None

        if len(ags) >= 3:
            # bereken de team sterkte: de som van de 3 sterkste sporters
            ags.sort(reverse=True)
            ag = sum(ags[:3])

            # bepaal de wedstrijdklasse
            comp = team.regiocompetitie.competitie
            for klasse in (CompetitieTeamKlasse
                           .objects
                           .filter(competitie=comp,
                                   team_type=team.team_type,
                                   is_voor_teams_rk_bk=False)
                           .order_by('min_ag',
                                     '-volgorde')):  # oplopend AG (=hogere klasse later)

                if ag >= klasse.min_ag:
                    team.team_klasse = klasse
            # for
        else:
            ag = AG_NUL

        if ag != team.aanvangsgemiddelde:
            if team.team_klasse == klasse_oud:
                self.stdout.write('[INFO] Team AG wijziging voor ver %s team %s (%s): %s --> %s' % (
                                    team.vereniging.ver_nr, team.volg_nr, team.team_type.beschrijving,
                                    team.aanvangsgemiddelde, ag))
            else:
                self.stdout.write('[WARNING] Team klasse wijziging voor regio %s ver %s team %s (%s): %s --> %s' % (
                                    team.vereniging.regio.regio_nr,
                                    team.vereniging.ver_nr, team.volg_nr, team.team_type.beschrijving,
                                    klasse_oud, team.team_klasse))

            if do_commit:
                team.aanvangsgemiddelde = ag
                team.save(update_fields=['aanvangsgemiddelde', 'team_klasse'])

    def _zoek_en_fix(self, afstand, do_commit):
        check_team_pks = list()

        nieuw_ag = dict()       # [regiocompetitiesporterboog.pk] = team_ag

        # zoek indiv_ag != team_ag
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__competitie__afstand=afstand,
                                  ag_voor_team_mag_aangepast_worden=True,
                                  ag_voor_indiv__gt=AG_NUL)
                          .prefetch_related('regiocompetitieteam_set')):

            if deelnemer.ag_voor_indiv != deelnemer.ag_voor_team:

                team = deelnemer.regiocompetitieteam_set.first()
                if team:
                    if team.pk not in check_team_pks:
                        check_team_pks.append(team.pk)

                nieuw_ag[deelnemer.pk] = deelnemer.ag_voor_indiv

                self.stdout.write('[INFO] Correctie team AG voor deelnemer %s: %s --> %s' % (
                                    deelnemer, deelnemer.ag_voor_team, deelnemer.ag_voor_indiv))

                if do_commit:
                    deelnemer.ag_voor_team = deelnemer.ag_voor_indiv
                    deelnemer.ag_voor_team_mag_aangepast_worden = False
                    deelnemer.save(update_fields=['ag_voor_team', 'ag_voor_team_mag_aangepast_worden'])
        # for

        # nu de team sterktes opnieuw berekenen
        for team in (RegiocompetitieTeam
                     .objects
                     .filter(pk__in=check_team_pks)
                     .select_related('regiocompetitie',
                                     'regiocompetitie__competitie',
                                     'vereniging',
                                     'team_type')
                     .prefetch_related('leden')):

            ags = list()
            for deelnemer in team.leden.all():
                try:
                    ag = nieuw_ag[deelnemer.pk]
                except KeyError:
                    ag = deelnemer.ag_voor_team

                ags.append(ag)
            # fo4

            self._update_team(team, ags, do_commit)
        # for

    def handle(self, *args, **options):

        do_commit = options['commit']

        self.stdout.write('[INFO] --- Indoor ---')
        self._zoek_en_fix(18, do_commit)

        self.stdout.write('[INFO] --- 25m1pijl ---')
        self._zoek_en_fix(25, do_commit)

        self.stdout.write('[INFO] Klaar')
        if not do_commit:
            self.stdout.write('[INFO] Gebruik --commit om wijzigingen door te voeren')

# end of file
