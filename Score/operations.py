# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Score.models import Score, ScoreHist, SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG


def _score_ag_opslaan(score_type, schutterboog, afstand, gemiddelde, door_account, notitie):
    """ slaan het aanvangsgemiddelde op voor schutterboog

        Return value:
            True  = opslagen
            False = niet opgeslagen / dupe
    """
    waarde = int(gemiddelde * 1000)

    try:
        score = Score.objects.get(schutterboog=schutterboog,
                                  type=score_type,
                                  afstand_meter=afstand)
    except Score.DoesNotExist:
        # eerste aanvangsgemiddelde voor deze afstand
        score = Score(schutterboog=schutterboog,
                      type=score_type,
                      waarde=waarde,
                      afstand_meter=afstand)
        score.save()

        hist = ScoreHist(score=score,
                         oude_waarde=0,
                         nieuwe_waarde=waarde,
                         door_account=door_account,
                         notitie=notitie)
        hist.save()
        return True

    if score.waarde != waarde:
        # nieuwe score voor deze afstand
        hist = ScoreHist(score=score,
                         oude_waarde=score.waarde,
                         nieuwe_waarde=waarde,
                         door_account=door_account,
                         notitie=notitie)
        hist.save()

        score.waarde = waarde
        score.save()
        return True

    # dezelfde score als voorheen --> voorlopig niet opslaan
    # (ook al is de datum en/of notitie anders)
    return False


def score_indiv_ag_opslaan(schutterboog, afstand, gemiddelde, door_account, notitie):
    """ sla een individueel AG op voor een specifieke schutter-boog en afstand """
    return _score_ag_opslaan(SCORE_TYPE_INDIV_AG, schutterboog, afstand, gemiddelde, door_account, notitie)


def score_teams_ag_opslaan(schutterboog, afstand, gemiddelde, door_account, notitie):
    """ sla een team-AG op voor een specifieke schutter-boog en afstand """
    return _score_ag_opslaan(SCORE_TYPE_TEAM_AG, schutterboog, afstand, gemiddelde, door_account, notitie)


def wanneer_ag_vastgesteld(afstand_meter):
    """ Zoek de datum waarop de aanvangsgemiddelden voor het laatste vastgesteld zijn """
    scorehist = (ScoreHist
                 .objects
                 .select_related('score')
                 .filter(door_account=None,
                         score__afstand_meter=afstand_meter,
                         score__type=SCORE_TYPE_INDIV_AG)
                 .order_by('-when'))[:1]
    if len(scorehist) > 0:
        return scorehist[0].when

    # nog nooit vastgesteld
    return None

# end of file
