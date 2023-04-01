# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Score.definities import AG_DOEL_INDIV, AG_DOEL_TEAM
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist


def _score_ag_opslaan(ag_doel, sporterboog, afstand, gemiddelde, door_account, notitie):
    """ slaan het aanvangsgemiddelde op voor sporterboog

        Return value:
            True  = opslagen
            False = niet opgeslagen / dupe
    """
    waarde = gemiddelde

    try:
        ag = Aanvangsgemiddelde.objects.get(sporterboog=sporterboog,
                                            doel=ag_doel,
                                            afstand_meter=afstand)
    except Aanvangsgemiddelde.DoesNotExist:
        # eerste aanvangsgemiddelde voor deze afstand
        ag = Aanvangsgemiddelde(
                        sporterboog=sporterboog,
                        boogtype=sporterboog.boogtype,
                        doel=ag_doel,
                        waarde=waarde,
                        afstand_meter=afstand)
        ag.save()

        hist = AanvangsgemiddeldeHist(
                        ag=ag,
                        oude_waarde=0,
                        nieuwe_waarde=waarde,
                        door_account=door_account,
                        notitie=notitie)
        hist.save()
        return True

    if ag.waarde != waarde:
        # nieuwe AG voor deze afstand
        hist = AanvangsgemiddeldeHist(
                    ag=ag,
                    oude_waarde=ag.waarde,
                    nieuwe_waarde=waarde,
                    door_account=door_account,
                    notitie=notitie)
        hist.save()

        ag.waarde = waarde
        ag.save(update_fields=['waarde'])
        return True

    # AG is niet gewijzigd, dus maak geen hist record aan
    # (ook al is de datum en/of notitie anders)
    return False


def score_indiv_ag_opslaan(sporterboog, afstand, gemiddelde, door_account, notitie):
    """ sla een individueel AG op voor een specifieke sporterboog en afstand """
    return _score_ag_opslaan(AG_DOEL_INDIV, sporterboog, afstand, gemiddelde, door_account, notitie)


def score_teams_ag_opslaan(sporterboog, afstand, gemiddelde, door_account, notitie):
    """ sla een team-AG op voor een specifieke sporterboog en afstand """
    return _score_ag_opslaan(AG_DOEL_TEAM, sporterboog, afstand, gemiddelde, door_account, notitie)


def wanneer_ag_vastgesteld(afstand_meter):
    """ Zoek de datum waarop de aanvangsgemiddelden voor het laatste vastgesteld zijn """
    qset = (AanvangsgemiddeldeHist
            .objects
            .select_related('ag')
            .filter(door_account=None,
                    ag__afstand_meter=afstand_meter,
                    ag__doel=AG_DOEL_INDIV)
            .order_by('-when'))[:1]

    if len(qset) > 0:
        return qset[0].when

    # nog nooit vastgesteld
    return None


# end of file
