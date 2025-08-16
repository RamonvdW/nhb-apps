# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from Competitie.models import (Competitie, CompetitieMutatie, KampioenschapSporterBoog, Kampioenschap,
                               CompetitieTeamKlasse)
from Competitie.definities import (MUTATIE_KAMP_CUT, MUTATIE_KAMP_TEAMS_NUMMEREN,
                                   MUTATIE_KAMP_AANMELDEN_INDIV, MUTATIE_KAMP_AFMELDEN_INDIV,
                                   MUTATIE_MAAK_WEDSTRIJD_FORMULIEREN)
from Competitie.operations.competitie_mutaties import ping_achtergrondtaak


def maak_mutatie_kamp_aanmelden_indiv(deelnemer: KampioenschapSporterBoog, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AANMELDEN_INDIV,
                                deelnemer=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_afmelden_indiv(deelnemer: KampioenschapSporterBoog, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AFMELDEN_INDIV,
                                deelnemer=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


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
        ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_teams_nummeren(comp: Competitie, kamp: Kampioenschap, team_klasse: CompetitieTeamKlasse,
                                     door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_TEAMS_NUMMEREN,
                                door=door_str,
                                competitie=comp,
                                kampioenschap=kamp,
                                team_klasse=team_klasse)

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_wedstrijdformulieren_aanmaken(comp: Competitie, door: str):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_MAAK_WEDSTRIJD_FORMULIEREN,
                                competitie=comp,
                                door=door)

    # ping de achtergrondtaak (zonder te wachten)
    ping_achtergrondtaak(mutatie, snel=True)


def aanmaken_wedstrijdformulieren_is_pending():
    # geeft True terug als er nog niet afgehandelde mutaties zijn voor het aanmaken van de wedstrijdformulieren
    cnt = CompetitieMutatie.objects.filter(
                                mutatie=MUTATIE_MAAK_WEDSTRIJD_FORMULIEREN,
                                is_verwerkt=False).count()
    return cnt > 0


# end of file
