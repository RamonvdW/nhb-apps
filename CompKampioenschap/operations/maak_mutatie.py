# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies die een CompetitieMutatie aanmaken en de achtergrondtaak vragen deze te verwerken """

from Competitie.models import Competitie, CompetitieMutatie, CompetitieTeamKlasse
from Competitie.definities import (MUTATIE_KAMP_CUT, MUTATIE_KAMP_BK_TEAMS_NUMMEREN, MUTATIE_KAMP_RK_TEAMS_NUMMEREN,
                                   MUTATIE_KAMP_AANMELDEN_RK_INDIV, MUTATIE_KAMP_AFMELDEN_RK_INDIV,
                                   MUTATIE_KAMP_AANMELDEN_BK_INDIV, MUTATIE_KAMP_AFMELDEN_BK_INDIV,
                                   MUTATIE_MAAK_WEDSTRIJDFORMULIEREN, MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN)
from Competitie.operations.competitie_mutaties import ping_achtergrondtaak
from CompLaagBond.models import KampBK, DeelnemerBK
from CompLaagRayon.models import KampRK, DeelnemerRK

# TODO: split naar CompLaagBond/Rayon


def maak_mutatie_kamp_aanmelden_rk_indiv(deelnemer: DeelnemerRK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AANMELDEN_RK_INDIV,
                                deelnemer_rk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_afmelden_rk_indiv(deelnemer: DeelnemerRK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AFMELDEN_RK_INDIV,
                                deelnemer_rk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_aanmelden_bk_indiv(deelnemer: DeelnemerBK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AANMELDEN_BK_INDIV,
                                deelnemer_bk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_afmelden_bk_indiv(deelnemer: DeelnemerBK, door_str: str, snel: bool):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_AFMELDEN_BK_INDIV,
                                deelnemer_bk=deelnemer,
                                door=door_str)

    # wacht tot de achtergrondtaak deze mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_bk_cut(deelkamp: KampBK, door_str: str, wijzigingen: list, snel: bool):
    # wijzigingen = list of tuples (indiv_klasse, oude_limiet, nieuwe_limiet)

    mutatie = None
    for indiv_klasse, oude_limiet, nieuwe_limiet in wijzigingen:
        mutatie = CompetitieMutatie.objects.create(
                            mutatie=MUTATIE_KAMP_CUT,
                            door=door_str,
                            kamp_bk=deelkamp,
                            indiv_klasse=indiv_klasse,
                            cut_oud=oude_limiet,
                            cut_nieuw=nieuwe_limiet)
    # for

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    if mutatie:
        ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_rk_cut(deelkamp: KampRK, door_str: str, wijzigingen: list, snel: bool):
    # wijzigingen = list of tuples (indiv_klasse, oude_limiet, nieuwe_limiet)

    mutatie = None
    for indiv_klasse, oude_limiet, nieuwe_limiet in wijzigingen:
        mutatie = CompetitieMutatie.objects.create(
                            mutatie=MUTATIE_KAMP_CUT,
                            door=door_str,
                            kamp_rk=deelkamp,
                            indiv_klasse=indiv_klasse,
                            cut_oud=oude_limiet,
                            cut_nieuw=nieuwe_limiet)
    # for

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    if mutatie:
        ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_bk_teams_nummeren(comp: Competitie, kamp: KampBK, team_klasse: CompetitieTeamKlasse,
                                        door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_BK_TEAMS_NUMMEREN,
                                door=door_str,
                                competitie=comp,
                                kamp_bk=kamp,
                                team_klasse=team_klasse)

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_kamp_rk_teams_nummeren(comp: Competitie, kamp: KampRK, team_klasse: CompetitieTeamKlasse,
                                        door_str: str, snel: bool):

    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_KAMP_RK_TEAMS_NUMMEREN,
                                door=door_str,
                                competitie=comp,
                                kamp_rk=kamp,
                                team_klasse=team_klasse)

    # wacht tot de achtergrondtaak de laatste mutatie verwerkt heeft (maximaal 3 seconden)
    ping_achtergrondtaak(mutatie, snel)


def maak_mutatie_wedstrijdformulieren_aanmaken(comp: Competitie, door: str):
    mutatie = CompetitieMutatie.objects.create(
                                mutatie=MUTATIE_MAAK_WEDSTRIJDFORMULIEREN,
                                competitie=comp,
                                door=door)

    # ping de achtergrondtaak (zonder te wachten)
    ping_achtergrondtaak(mutatie, snel=True)


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
    ping_achtergrondtaak(mutatie, snel=True)


# end of file
