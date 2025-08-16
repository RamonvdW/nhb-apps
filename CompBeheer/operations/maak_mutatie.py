# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from django.conf import settings
from Competitie.models import Competitie, CompetitieMutatie
from Competitie.definities import (MUTATIE_COMPETITIE_OPSTARTEN, MUTATIE_AG_VASTSTELLEN,
                                   MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                                   MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK, MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK,
                                   MUTATIE_KAMP_INDIV_AFSLUITEN, MUTATIE_KAMP_TEAMS_AFSLUITEN)
from Site.core.background_sync import BackgroundSync
import time

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__COMPETITIE_MUTATIES)


def _competitie_ping_achtergrondtaak(mutatie: CompetitieMutatie, snel: bool):

    # ping de achtergrondtaak
    mutatie_ping.ping()

    if not snel:
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0  # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval  # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2  # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie.refresh_from_db()
        # while


def maak_mutatie_competitie_opstarten(door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                        mutatie=MUTATIE_COMPETITIE_OPSTARTEN,
                        door=door_str)

    _competitie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_ag_vaststellen(comp: Competitie, door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                        mutatie=MUTATIE_AG_VASTSTELLEN,
                        competitie=comp,
                        door=door_str)

    _competitie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_doorzetten_regio_naar_rk(comp: Competitie, door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                        mutatie=MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                        competitie=comp,
                        door=door_str)

    _competitie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_indiv_doorzetten_naar_bk(comp: Competitie, door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                        mutatie=MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK,
                        competitie=comp,
                        door=door_str)

    _competitie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_teams_doorzetten_naar_bk(comp: Competitie, door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                        mutatie=MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK,
                        competitie=comp,
                        door=door_str)

    _competitie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_indiv_afsluiten(comp: Competitie, door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                        mutatie=MUTATIE_KAMP_INDIV_AFSLUITEN,
                        competitie=comp,
                        door=door_str)

    _competitie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_teams_afsluiten(comp: Competitie, door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                        mutatie=MUTATIE_KAMP_TEAMS_AFSLUITEN,
                        competitie=comp,
                        door=door_str)

    _competitie_ping_achtergrondtaak(mutatie, snel)


# end of file
