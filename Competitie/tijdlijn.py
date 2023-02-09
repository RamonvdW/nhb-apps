# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
import datetime


def bepaal_fase_indiv(comp) -> str:
    """ bepaal de fase van de individuele competitie """

    # fase A was totdat dit object gemaakt werd

    if comp.is_afgesloten:
        return 'Z'

    if comp.bk_indiv_afgesloten:
        return 'Q'

    now = timezone.now()
    now = datetime.date(year=now.year, month=now.month, day=now.day)

    if comp.bk_indiv_klassen_zijn_samengevoegd:
        # BK fases (tweede deel)

        if now < comp.begin_fase_P_indiv:
            # fase O: BK wedstrijden voorbereiden
            return 'O'

        # fase P: BK wedstrijden
        return 'P'

    if comp.rk_indiv_afgesloten:
        # in BK fases (eerste deel)
        return 'N'

    if comp.regiocompetitie_is_afgesloten:
        # in RK fase

        # fase K begint 2 weken voor fase L
        begin_fase_k = comp.begin_fase_L_indiv - datetime.timedelta(days=14)
        if now < begin_fase_k:
            # fase J: bevestig deelname of afmelden
            return 'J'

        if now < comp.begin_fase_L_indiv:
            # fase K: voorbereiden wedstrijden
            return 'K'

        # fase L: wedstrijden
        return 'L'

    # regiocompetitie fases
    if not comp.klassengrenzen_vastgesteld:
        # A = vaststellen klassengrenzen, instellingen regio en planning regiocompetitie wedstrijden
        #     tot aanmeldingen beginnen; nog niet open voor aanmelden
        return 'A'

    if now < comp.begin_fase_C:
        # B = voorbereidingen door RCL
        return 'B'

    if now < comp.begin_fase_F:
        # C = open voor inschrijvingen
        return 'C'

    if now <= comp.einde_fase_F:
        # F = Wedstrijden
        return 'F'

    # fase G: doorzetten naar RK fase door BKO
    return 'G'


def bepaal_fase_teams(comp) -> str:
    """ bepaal de fase van de teamcompetitie """
    # fase A was totdat dit object gemaakt werd

    if comp.is_afgesloten:
        return 'Z'

    if comp.bk_teams_afgesloten:
        return 'Q'

    now = timezone.now()
    now = datetime.date(year=now.year, month=now.month, day=now.day)

    if comp.bk_teams_klassen_zijn_samengevoegd:
        # BK fases (tweede deel)

        if now < comp.begin_fase_P_teams:
            # fase O: BK wedstrijden voorbereiden
            return 'O'

        # fase P: BK wedstrijden
        return 'P'

    if comp.rk_teams_afgesloten:
        # in BK fases (eerste deel)

        # fase N: BK klassen samenvoegen
        return 'N'

    if comp.klassengrenzen_vastgesteld_rk_bk:
        # RK fases

        if now < comp.begin_fase_L_teams:
            # fase K: voorbereiding RK wedstrijden; afmelden bij vereniging
            return 'K'

        # fase L, tot de BKO deze handmatig doorzet
        return 'L'

    if comp.regiocompetitie_is_afgesloten:
        # in RK fase

        # fase J: compleet maken RK teams; verwijderen incomplete teams
        #         tot de BKO de klassengrenzen vaststelt
        return 'J'

    # regiocompetitie fases
    if not comp.klassengrenzen_vastgesteld:
        # fase A: vaststellen klassengrenzen, instellingen regio teams
        return 'A'

    if now < comp.begin_fase_C:
        # fase B: instellingen regio teams
        return 'B'

    if now < comp.begin_fase_F:
        # fase C: aanmaken teams; koppel leden; handmatig AG invoeren

        # let op: fase D is regio-specifieke datum; wordt hier niet overwogen
        # fase D: aanmaken poules en afronden wedstrijdschema's
        return 'C'

    if now <= comp.einde_fase_F:
        # F = Wedstrijden
        return 'F'

    # fase G: doorzetten naar RK fase door BKO
    return 'G'


# end of file
