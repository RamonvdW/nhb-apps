# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from django.conf import settings
from Competitie.models import Regiocompetitie, CompetitieMutatie
from Competitie.definities import (MUTATIE_COMPETITIE_OPSTARTEN, MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M,
                                   MUTATIE_KAMP_CUT, MUTATIE_KAMP_REINIT_TEST, MUTATIE_KAMP_AFMELDEN_INDIV,
                                   MUTATIE_KAMP_AANMELDEN_INDIV, MUTATIE_KAMP_TEAMS_NUMMEREN, MUTATIE_REGIO_TEAM_RONDE,
                                   MUTATIE_DOORZETTEN_REGIO_NAAR_RK, MUTATIE_EXTRA_RK_DEELNEMER,
                                   MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK, MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK,
                                   MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV, MUTATIE_KAMP_INDIV_AFSLUITEN,
                                   MUTATIE_KAMP_TEAMS_AFSLUITEN, MUTATIE_MAAK_WEDSTRIJDFORMULIEREN)
from Competitie.operations.competitie_mutaties import ping_achtergrondtaak


def maak_mutatie_regio_team_ronde(deelcomp: Regiocompetitie, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_REGIO_TEAM_RONDE,
                                regiocompetitie=deelcomp,
                                door=door_str)

    ping_achtergrondtaak(mutatie, snel)


# end of file
