# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from Account.models import Account
from Competitie.models import CompetitieMutatie, CompetitieMatch
from Competitie.definities import MUTATIE_REGIO_TEAM_RONDE, MUTATIE_REGIO_EXTERN_SCORES_OPHALEN
from Competitie.operations.ping_achtergrondtaak import ping_competitie_achtergrondtaak
from CompLaagRegio.models import RegioComp


def maak_mutatie_regio_team_ronde(deelcomp: RegioComp, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_REGIO_TEAM_RONDE,
                                regiocomp=deelcomp,
                                door=door_str)

    ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_scores_extern_ophalen(match: CompetitieMatch, door_str: str, door_account: Account, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_REGIO_EXTERN_SCORES_OPHALEN,
                                match=match,
                                door=door_str,
                                door_account=door_account)

    ping_competitie_achtergrondtaak(mutatie, snel)



# end of file
