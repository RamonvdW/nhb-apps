# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from types import SimpleNamespace

# 8 teams: 0, 1, 2, 3, 4, 5, 6, 7
RONDE_PLANNEN_8 = (                       # 0 1 2 3 4 5 6 7 thuis
    [(0, 1), (6, 2), (5, 3), (4, 7)],     # 0 1 1 1 0 0 0 1
    [(2, 0), (1, 7), (3, 6), (4, 5)],     # 1 1 1 1 0 1 1 2
    [(0, 5), (1, 4), (2, 3), (7, 6)],     # 1 1 1 2 1 2 2 2
    [(4, 0), (3, 1), (2, 7), (5, 6)],     # 2 2 1 2 1 2 3 3
    [(7, 0), (6, 1), (5, 2), (3, 4)],     # 3 3 2 2 2 2 3 3
    [(0, 3), (1, 2), (6, 4), (7, 5)],     # 3 3 3 3 3 3 3 3
    [(6, 0), (1, 5), (4, 2), (3, 7)],     # 4 3 4 3 3 4 3 4
)

# 4 teams: 0, 1, 2, 3
RONDE_PLANNEN_4 = (                         # 0 1 2 3 thuis
    [(0, 9), (1, 9), (2, 9), (3, 9)],       # 1 1 1 1
    [(0, 1), (2, 3)],                       # 1 2 1 2
    [(3, 0), (1, 2)],                       # 2 2 2 2
    [(0, 2), (3, 1)],                       # 2 3 3 2
    [(1, 0), (2, 3)],                       # 3 3 3 3
    [(0, 2), (1, 3)],                       # 3 3 4 4
    [(3, 0), (2, 1)]                        # 4 4 4 4
)

# 2: teams 0, 1
RONDE_PLANNEN_2 = (
    [(0, 1)],
    [(1, 0)],
    [(0, 1)],
    [(1, 0)],
    [(0, 1)],
    [(1, 0)],
    [(0, 1)],
)


def maak_poule_schema(poule):

    teams = poule.teams.select_related('vereniging').order_by('pk')

    if len(teams) > 4:
        plannen = RONDE_PLANNEN_8
    elif len(teams) > 2:
        plannen = RONDE_PLANNEN_4
    else:
        plannen = RONDE_PLANNEN_2

    pk2team = dict()
    for team in teams:
        team.team_str = "[%s] %s" % (team.vereniging.ver_nr, team.team_naam)
        pk2team[team.pk] = team
    # for

    team_pks = list(pk2team.keys())
    team_pks += [0, 0, 0, 0, 0, 0, 0, 0]

    # dummy team
    pk2team[0] = SimpleNamespace(team_str='')

    poule.schema = list()

    # verdeling maken volgens het maximale schema van 8 teams
    for ronde_nr in range(7):
        schema_ronde = list()
        tup = (ronde_nr + 1, schema_ronde)
        poule.schema.append(tup)

        for team1, team2 in plannen[ronde_nr]:
            pk1 = team_pks[team1]
            pk2 = team_pks[team2]

            if pk1 == pk2 == 0:
                # skip dummy tegen dummy
                pass
            else:
                if pk1 == 0:
                    # zet eigen team aan de 'thuis' kant
                    pk1, pk2 = pk2, pk1

                tup = (pk2team[pk1], pk2team[pk2])
                schema_ronde.append(tup)
        # for
    # for


# end of file
