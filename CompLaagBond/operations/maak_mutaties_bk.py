# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from Competitie.models import CompetitieMutatie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.definities import (MUTATIE_KAMP_BK_WIJZIG_INDIV_CUT, MUTATIE_KAMP_BK_TEAMS_NUMMEREN,
                                   MUTATIE_KAMP_AANMELDEN_BK_INDIV, MUTATIE_KAMP_AFMELDEN_BK_INDIV,
                                   MUTATIE_KAMP_BK_VERPLAATS_KLASSE_INDIV)
from Competitie.operations.ping_achtergrondtaak import ping_competitie_achtergrondtaak
from CompLaagBond.models import KampBK, DeelnemerBK


def maak_mutatie_kamp_aanmelden_bk_indiv(deelnemer: DeelnemerBK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AANMELDEN_BK_INDIV,
                                deelnemer_bk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_afmelden_bk_indiv(deelnemer: DeelnemerBK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AFMELDEN_BK_INDIV,
                                deelnemer_bk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_bk_wijzig_cut(deelkamp: KampBK,
                                    wijzigingen: list[tuple[CompetitieIndivKlasse, int, int]],
                                    door_str: str, snel: bool):
    # wijzigingen = list of tuples (indiv_klasse, oude_limiet, nieuwe_limiet)
    mutatie = None
    for indiv_klasse, oude_limiet, nieuwe_limiet in wijzigingen:
        mutatie = CompetitieMutatie.objects.create(
                            mutatie=MUTATIE_KAMP_BK_WIJZIG_INDIV_CUT,
                            door=door_str,
                            kamp_bk=deelkamp,
                            indiv_klasse=indiv_klasse,
                            cut_oud=oude_limiet,
                            cut_nieuw=nieuwe_limiet)
    # for

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    if mutatie:
        ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_bk_teams_nummeren(kamp: KampBK,
                                        team_klasse: CompetitieTeamKlasse,
                                        door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_BK_TEAMS_NUMMEREN,
                                door=door_str,
                                kamp_bk=kamp,
                                team_klasse=team_klasse)

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    ping_competitie_achtergrondtaak(mutatie, snel)


def maak_mutatie_verplaats_bk_deelnemer_kleine_klasse(deelnemer: DeelnemerBK,
                                                      indiv_klasse: CompetitieIndivKlasse,
                                                      door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_BK_VERPLAATS_KLASSE_INDIV,
                                door=door_str,
                                deelnemer_bk=deelnemer,
                                indiv_klasse=indiv_klasse)

    ping_competitie_achtergrondtaak(mutatie, snel)

# end of file
