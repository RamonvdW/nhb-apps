# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from Competitie.models import CompetitieMutatie
from Competitie.definities import MUTATIE_REGIO_TEAM_RONDE
from Competitie.operations.ping_achtergrondtaak import ping_competitie_achtergrondtaak
from CompLaagRegio.models import RegioComp



def maak_mutatie_regio_team_ronde(deelcomp: RegioComp, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_REGIO_TEAM_RONDE,
                                regiocomp=deelcomp,
                                door=door_str)

    ping_competitie_achtergrondtaak(mutatie, snel)


# end of file
