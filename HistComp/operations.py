# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from HistComp.definities import HIST_BOOG2URL, HIST_TEAM2URL
# from HistComp.models import HistCompSeizoen


def get_hist_url(seizoen: str, indiv_teams: str, laag: str, boog_of_team_afkorting: str) -> str | None:
    """ returns a URL to a historical competition, if available

        Wordt gebruikt om een URL naar een afgesloten competitie om te zetten naar een histcomp URL.

        parameters:
            comp_pk_of_seizoen: "indoor-2024-2025" of "25m1pijl-2024-2025"
            indiv_teams: 'indiv' of 'teams'
            laag: 'regio', 'rk' of 'bk'
            boog_of_team_afkorting: 'r', 'c', etc.
    """

    # determine indoor or 25m1pijl
    histcomp_type = 'indoor'
    seizoen = seizoen.lower()
    if seizoen.startswith('indoor-'):
        seizoen = seizoen[7:]
    elif seizoen.startswith('25m1pijl-'):
        histcomp_type = '25m1pijl'
        seizoen = seizoen[9:]

    # 2024-2025
    if len(seizoen) != 9:
        # niet in het formaat "2024-2025"
        return None

    # als het seizoen niet bestaat dan toont HistComp het nieuwste seizoen
    # hist_seizoen = comp_pk_of_seizoen.replace('-', '/')     # 2024-2025 --> 2024/2025
    # if HistCompSeizoen.objects.filter(seizoen=hist_seizoen).count() == 0:
    #     # seizoen niet beschikbaar, of geen valide combinatie van jaren
    #     return None

    if laag not in ('regio', 'rk', 'bk'):
        return None

    if indiv_teams == 'indiv':
        # indiv
        boog_type = HIST_BOOG2URL.get(boog_of_team_afkorting.upper(), None)
        if boog_type:
            name = 'HistComp:uitslagen-%s-indiv' % laag
            url = reverse(name, kwargs={'seizoen': seizoen,
                                        'histcomp_type': histcomp_type,
                                        'boog_type': boog_type})
            return url

    elif indiv_teams == 'teams':
        # teams
        team_type = HIST_TEAM2URL.get(boog_of_team_afkorting.upper(), None)
        if team_type:
            name = 'HistComp:uitslagen-%s-teams' % laag
            url = reverse(name, kwargs={'seizoen': seizoen,
                                        'histcomp_type': histcomp_type,
                                        'team_type': team_type})
            return url

    return None

# end of file
