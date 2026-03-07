# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from Competitie.models import Competitie, CompetitieMutatie
from Competitie.definities import MUTATIE_MAAK_WEDSTRIJDFORMULIEREN, MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN
from Competitie.operations import ping_competitie_achtergrondtaak


def maak_mutatie_wedstrijdformulieren_aanmaken(comp: Competitie, door: str):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_MAAK_WEDSTRIJDFORMULIEREN,
                                competitie=comp,
                                door=door)

    # ping de achtergrondtaak (zonder te wachten)
    ping_competitie_achtergrondtaak(mutatie, snel=True)


def aanmaken_wedstrijdformulieren_is_pending():
    # geeft True terug als er nog niet afgehandelde mutaties zijn voor het aanmaken van de wedstrijdformulieren
    cnt = CompetitieMutatie.objects.filter(
                                mutatie=MUTATIE_MAAK_WEDSTRIJDFORMULIEREN,
                                is_verwerkt=False).count()
    return cnt > 0


def maak_mutatie_update_dirty_wedstrijdformulieren(comp: Competitie):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN,
                                competitie=comp)    # nodig voor begin_jaar

    # ping de achtergrondtaak (zonder te wachten)
    ping_competitie_achtergrondtaak(mutatie, snel=True)


# end of file
