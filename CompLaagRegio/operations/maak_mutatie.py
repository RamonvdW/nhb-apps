# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from django.conf import settings
from Competitie.models import Regiocompetitie, CompetitieMutatie
from Competitie.definities import MUTATIE_REGIO_TEAM_RONDE
from Competitie.operations.competitie_mutaties import ping_achtergrondtaak


def maak_mutatie_regio_team_ronde(deelcomp: Regiocompetitie, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_REGIO_TEAM_RONDE,
                                regiocompetitie=deelcomp,
                                door=door_str)

    ping_achtergrondtaak(mutatie, snel)


# end of file
