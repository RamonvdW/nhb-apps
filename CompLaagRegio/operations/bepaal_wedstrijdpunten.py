# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.db.models import Count
from Competitie.definities import TEAM_PUNTEN_MODEL_FORMULE1, TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_F1
from Competitie.operations.poules import maak_poule_schema
from CompLaagRegio.models import RegioComp, RegioPoule, RegioRondeTeam
from types import SimpleNamespace


def bepaal_wedstrijdpunten(deelcomp: RegioComp, ronde_nr: int):
    """ bepaal de wedstrijdpunten voor elk team in de huidige ronde (1..7),
        afhankelijk van het team punten model dat in gebruik is
        geeft terug:
            regels, is_redelijk

        regels:
            2p:  lijst van tup(team1, team2) met elk: team1/2_str, team1/2_score, team1/2_wp = 0/1/2
            f1:  ronde teams met voorstel wp in ronde_wp (10/8/6/5/4/3/2/1/0)
            som: ronde teams (zonder wp)

        is_redelijk:
            False = Alle teams hebben 0 punten, dus nog niet redelijk om deze ronde af te sluiten
            True  = Er zijn teams met punten
    """

    alle_regels = list()
    is_redelijk = False

    wp_model = deelcomp.regio_team_punten_model

    # TODO: delen die bij de view horen hier uit halen
    for poule in (RegioPoule
                  .objects
                  .prefetch_related('teams')
                  .filter(regiocomp=deelcomp)):

        team_pks = poule.teams.values_list('pk', flat=True)

        ronde_teams = (RegioRondeTeam
                       .objects
                       .select_related('team',
                                       'team__vereniging')
                       .filter(team__in=team_pks,
                               ronde_nr=ronde_nr)
                       .annotate(score_count=Count('scores_feitelijk'))
                       .order_by('-team_score'))        # belangrijke: hoogste score eerst

        # common
        for ronde_team in ronde_teams:
            ronde_team.ronde_wp = 0
            ronde_team.team_str = "[%s] %s" % (ronde_team.team.vereniging.ver_nr,
                                               ronde_team.team.maak_team_naam_kort())
        # for

        if wp_model == TEAM_PUNTEN_MODEL_TWEE:

            # laat het hele wedstrijdschema maken
            maak_poule_schema(poule)

            # haal de juiste ronde eruit
            schemas = [schema for nr, schema in poule.schema if nr == deelcomp.huidige_team_ronde]
            if len(schemas) != 1:       # pragma: no cover
                raise Http404('Probleem met poule wedstrijdschema')

            schema = schemas[0]

            # uit het poule schema komen teams, die moeten we vertalen naar ronde teams
            team_pk2ronde_team = dict()
            for ronde_team in ronde_teams:
                team_pk2ronde_team[ronde_team.team.pk] = ronde_team
            # for

            is_eerste = True
            for team1, team2 in schema:
                regel = SimpleNamespace()
                regel.team1_str = "[%s] %s" % (team1.vereniging.ver_nr, team1.team_naam)
                regel.team1_wp = 0
                regel.ronde_team1 = ronde_team1 = team_pk2ronde_team[team1.pk]
                regel.team1_score = ronde_team1.team_score
                regel.team1_score_count = ronde_team1.score_count

                if ronde_team1.team_score > 0:
                    is_redelijk = True

                if team2.pk == -1:
                    # van een bye win je altijd, als er maar een score neergezet is
                    regel.team2_is_bye = True
                    regel.team2_score = 0
                    regel.ronde_team2 = None
                    regel.team2_wp = 0
                    if regel.team1_score > 0:
                        regel.team1_wp = 2
                else:
                    regel.team2_str = "[%s] %s" % (team2.vereniging.ver_nr, team2.team_naam)
                    regel.team2_wp = 0
                    regel.ronde_team2 = ronde_team2 = team_pk2ronde_team[team2.pk]
                    regel.team2_score = ronde_team2.team_score
                    regel.team2_score_count = ronde_team2.score_count

                    if ronde_team2.team_score > ronde_team1.team_score:
                        regel.team2_wp = 2
                    elif ronde_team2.team_score < ronde_team1.team_score:
                        regel.team1_wp = 2
                    else:
                        if regel.team1_score > 0:
                            regel.team1_wp = 1
                            regel.team2_wp = 1

                if is_eerste:
                    # TODO: dit hoort bij de view-logic
                    regel.break_poule = True
                    regel.poule_str = poule.beschrijving
                    is_eerste = False

                alle_regels.append(regel)
            # for

        elif wp_model == TEAM_PUNTEN_MODEL_FORMULE1:

            f1_scores = list(TEAM_PUNTEN_F1)
            rank = 0
            prev_team_score = 0
            prev_team_wp = 0
            for ronde_team in ronde_teams:
                if rank == 0:
                    ronde_team.break_poule = True
                    ronde_team.poule_str = poule.beschrijving

                rank += 1
                ronde_team.rank = rank

                # geen score dan geen wedstrijdpunten
                if ronde_team.team_score > 0 and len(f1_scores):
                    # gelijke score, gelijke punten
                    if ronde_team.team_score == prev_team_score:
                        ronde_team.ronde_wp = prev_team_wp
                    else:
                        ronde_team.ronde_wp = f1_scores[0]

                    prev_team_score = ronde_team.team_score
                    prev_team_wp = ronde_team.ronde_wp

                    f1_scores.pop(0)
                    is_redelijk = True

                alle_regels.append(ronde_team)
            # for

        else:
            # TEAM_PUNTEN_MODEL_SOM_SCORES
            rank = 0
            for ronde_team in ronde_teams:

                if rank == 0:
                    ronde_team.break_poule = True
                    ronde_team.poule_str = poule.beschrijving

                rank += 1
                ronde_team.rank = rank

                if ronde_team.team_score != 0:
                    is_redelijk = True

                alle_regels.append(ronde_team)
            # for
    # for

    return alle_regels, is_redelijk


# end of file
