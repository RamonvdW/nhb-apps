# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
import datetime


# korte beschrijving van de competitie fase
comp_fase_kort = {
    'A': 'opstarten',
    'B': 'voorbereiden',
    'C': 'inschrijven',
    'D': 'inschrijving (laat)',
    'F': 'wedstrijden regio',
    'G': 'vaststellen uitslag regio',
    'J': 'voorbereiding RK',
    'K': 'voorbereiding RK',
    'L': 'wedstrijden RK',
    'N': 'kleine klassen samenvoegen BK',
    'O': 'voorbereiding BK',
    'P': 'wedstrijden BK',
    'Q': 'einde competitie',
    'Z': 'afgesloten',
}


def maak_comp_fase_beschrijvingen(comp):
    indiv = "Competitie fase individueel: %s (%s)" % (comp.fase_indiv, comp_fase_kort[comp.fase_indiv])
    teams = "Competitie fase teams: %s (%s)" % (comp.fase_teams, comp_fase_kort[comp.fase_teams])
    return indiv, teams


class EvaluatieDatum(object):
    """ Om de evaluatie datum van een competitie te kunnen beïnvloeden tijdens een test """

    def __init__(self):
        self.gekozen_datum = None

    def zet_test_datum(self, date_str: str):
        if date_str:
            self.gekozen_datum = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            self.gekozen_datum = None


evaluatie_datum = EvaluatieDatum()


def bepaal_fase_indiv(comp) -> str:
    """ bepaal de fase van de individuele competitie """

    comp.begin_fase_K_indiv = comp.begin_fase_L_indiv - datetime.timedelta(days=14)

    # fase A was totdat dit object gemaakt werd

    if comp.is_afgesloten:
        return 'Z'

    if comp.bk_indiv_afgesloten:
        return 'Q'

    vandaag = evaluatie_datum.gekozen_datum
    if not vandaag:
        vandaag = timezone.now().date()

    if comp.bk_indiv_klassen_zijn_samengevoegd:
        # BK fases (tweede deel)

        if vandaag < comp.begin_fase_P_indiv:
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
        if vandaag < comp.begin_fase_K_indiv:
            # fase J: bevestig deelname of afmelden
            return 'J'

        if vandaag < comp.begin_fase_L_indiv:
            # fase K: voorbereiden wedstrijden
            return 'K'

        # fase L: wedstrijden
        return 'L'

    # regiocompetitie fases
    if not comp.klassengrenzen_vastgesteld:
        # A = vaststellen klassengrenzen, instellingen regio en planning regiocompetitie wedstrijden
        #     tot aanmeldingen beginnen; nog niet open voor aanmelden
        return 'A'

    if vandaag < comp.begin_fase_C:
        # B = voorbereidingen door RCL
        return 'B'

    if vandaag < comp.begin_fase_D_indiv:
        # C = open voor inschrijvingen
        return 'C'

    if vandaag < comp.begin_fase_F:
        # D = late inschrijvingen
        return 'D'

    if vandaag <= comp.einde_fase_F:
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

    vandaag = evaluatie_datum.gekozen_datum
    if not vandaag:
        vandaag = timezone.now().date()

    if comp.bk_teams_klassen_zijn_samengevoegd:
        # BK fases (tweede deel)

        if vandaag < comp.begin_fase_P_teams:
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

        if vandaag < comp.begin_fase_L_teams:
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

    if vandaag < comp.begin_fase_C:
        # fase B: instellingen regio teams
        return 'B'

    if vandaag < comp.begin_fase_F:
        # fase C: aanmaken teams; koppel leden; handmatig AG invoeren

        # let op: fase D is regio-specifieke datum; wordt hier niet overwogen
        # fase D: aanmaken poules en afronden wedstrijdschema's
        return 'C'

    if vandaag <= comp.einde_fase_F:
        # F = Wedstrijden
        return 'F'

    # fase G: doorzetten naar RK fase door BKO
    return 'G'


def is_open_voor_inschrijven_rk_teams(comp):

    """
        comp.fase_teams moet al gezet zijn

        Returns: is_open, vanaf_datum

        True,  None:        Deze competitie open is voor het aanmelden van RK teams
        False, vanaf_datum: De inschrijving gaat binnenkort open
        False, None:        De inschrijving ver in de toekomst of in het verre verleden
    """

    if comp.fase_teams <= 'J':

        vanaf = comp.begin_fase_F + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)

        vandaag = evaluatie_datum.gekozen_datum
        if not vandaag:
            vandaag = timezone.now().date()

        if vandaag >= vanaf:
            return True, None

        return False, vanaf

    return False, None


# end of file
