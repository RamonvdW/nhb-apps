# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from Competitie.models import CompetitieMutatie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.definities import (MUTATIE_KAMP_RK_WIJZIG_CUT, MUTATIE_KAMP_RK_TEAMS_NUMMEREN,
                                   MUTATIE_EXTRA_RK_DEELNEMER,
                                   MUTATIE_KAMP_AANMELDEN_RK_INDIV, MUTATIE_KAMP_AFMELDEN_RK_INDIV)
from Competitie.operations.ping_achtergrondtaak import ping_competitie_achtergrondtaak
from CompLaagRayon.models import KampRK, DeelnemerRK


def maak_mutatie_kamp_aanmelden_rk_indiv(deelnemer: DeelnemerRK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AANMELDEN_RK_INDIV,
                                deelnemer_rk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_afmelden_rk_indiv(deelnemer: DeelnemerRK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AFMELDEN_RK_INDIV,
                                deelnemer_rk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_rk_wijzig_cut(deelkamp: KampRK,
                                    wijzigingen: list[tuple[CompetitieIndivKlasse, int, int]],
                                    door_str: str, snel: bool):
    # wijzigingen = list of tuples (indiv_klasse, oude_limiet, nieuwe_limiet)
    mutatie = None
    for indiv_klasse, oude_limiet, nieuwe_limiet in wijzigingen:
        mutatie = CompetitieMutatie.objects.create(
                            mutatie=MUTATIE_KAMP_RK_WIJZIG_CUT,
                            door=door_str,
                            kamp_rk=deelkamp,
                            indiv_klasse=indiv_klasse,
                            cut_oud=oude_limiet,
                            cut_nieuw=nieuwe_limiet)
    # for

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    if mutatie:
        ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_rk_teams_nummeren(kamp: KampRK, team_klasse: CompetitieTeamKlasse,
                                        door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_RK_TEAMS_NUMMEREN,
                                door=door_str,
                                kamp_rk=kamp,
                                team_klasse=team_klasse)

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_extra_rk_deelnemer(deelnemer: DeelnemerRK,
                                    door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_EXTRA_RK_DEELNEMER,
                                deelnemer_rk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    ping_competitie_achtergrondtaak(mutatie, snel)


# end of file
