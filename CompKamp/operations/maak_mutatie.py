# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from django.conf import settings
from Competitie.models import Competitie, CompetitieMutatie, KampioenschapSporterBoog, Kampioenschap
from Competitie.definities import (MUTATIE_COMPETITIE_OPSTARTEN, MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M,
                                   MUTATIE_KAMP_CUT, MUTATIE_KAMP_REINIT_TEST, MUTATIE_KAMP_AFMELDEN_INDIV,
                                   MUTATIE_KAMP_AANMELDEN_INDIV, MUTATIE_KAMP_TEAMS_NUMMEREN, MUTATIE_REGIO_TEAM_RONDE,
                                   MUTATIE_DOORZETTEN_REGIO_NAAR_RK, MUTATIE_EXTRA_RK_DEELNEMER,
                                   MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK, MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK,
                                   MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV, MUTATIE_KAMP_INDIV_AFSLUITEN,
                                   MUTATIE_KAMP_TEAMS_AFSLUITEN, MUTATIE_MAAK_WEDSTRIJD_FORMULIEREN)
from Site.core.background_sync import BackgroundSync
import time

competitie_mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__COMPETITIE_MUTATIES)


def _competitie_mutatie_ping_achtergrondtaak(mutatie: CompetitieMutatie, snel: bool):

    # ping de achtergrondtaak
    competitie_mutatie_ping.ping()

    if not snel:  # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0     # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie.refresh_from_db()
        # while


def maak_mutatie_kamp_aanmelden_indiv(deelnemer: KampioenschapSporterBoog, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AANMELDEN_INDIV,
                                deelnemer=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    _competitie_mutatie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_afmelden_indiv(deelnemer: KampioenschapSporterBoog, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AFMELDEN_INDIV,
                                deelnemer=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    _competitie_mutatie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_cut(deelkamp: Kampioenschap, door_str: str, wijzigingen: list, snel: bool):
    # wijzigingen = list of tuples (indiv_klasse | None, team_klasse | None, oude_limiet, nieuwe_limiet)

    mutatie = None
    for indiv_klasse, team_klasse, oude_limiet, nieuwe_limiet in wijzigingen:
        mutatie = CompetitieMutatie.objects.create(
                                            mutatie=MUTATIE_KAMP_CUT,
                                            door=door_str,
                                            kampioenschap=deelkamp,
                                            indiv_klasse=indiv_klasse,
                                            team_klasse=team_klasse,
                                            cut_oud=oude_limiet,
                                            cut_nieuw=nieuwe_limiet)
    # for

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    if mutatie:
        _competitie_mutatie_ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_wedstrijdformulieren_aanmaken(comp: Competitie, door: str):
    CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_MAAK_WEDSTRIJD_FORMULIEREN,
                                competitie=comp,
                                door=door)

    # ping de achtergrondtaak (zonder te wachten)
    competitie_mutatie_ping.ping()


def aanmaken_wedstrijdformulieren_is_pending():
    # geeft True terug als er nog niet afgehandelde mutaties zijn voor het aanmaken van de wedstrijdformulieren
    cnt = CompetitieMutatie.objects.filter(
                                mutatie=MUTATIE_MAAK_WEDSTRIJD_FORMULIEREN,
                                is_verwerkt=False).count()
    return cnt > 0


# end of file
