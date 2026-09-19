# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.tijdlijn import evaluatie_datum
# from CompLaagRegio.models import RegioComp        # circular import


def bepaal_fase_teams_regio(deelcomp) -> str:
    """ bepaal de fase van de teamcompetitie voor de regio

        competitie < C of > F: volg competitie
        competitie == C: aanmelden teams
        competitie == D: teams in een poule plaatsen
        competitie == F: wedstrijden

        precondition: deelcomp.competitie.fase_teams is gezet

        return: letter A..Z
    """

    comp_fase_teams = deelcomp.competitie.fase_teams

    if comp_fase_teams < 'C' or comp_fase_teams > 'F':
        # toon de nationale tijdlijn
        return comp_fase_teams

    if not deelcomp.regio_organiseert_teamcompetitie:
        # geen teamcompetitie in deze regio
        # slag fase C t/m F over
        return 'G'

    if deelcomp.huidige_team_ronde > 0:
        # fase F: wedstrijden
        return 'F'

    vandaag = evaluatie_datum.gekozen_datum
    if not vandaag:
        vandaag = timezone.now().date()

    # fase C: aanmaken teams; koppel leden; handmatig AG invoeren
    # fase D: aanmaken poules en afronden wedstrijdschema's

    if vandaag < deelcomp.begin_fase_D:
        return 'C'

    # teamcompetitie blijft hangen in fase D totdat de eerste ronde opgestart is
    return 'D'

# end of file
