# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
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
    'F': 'wedstrijden regio',
    'G': 'vaststellen uitslag regio',
    'J': 'voorbereiding RK',
    'K': 'voorbereiding RK',
    'L': 'wedstrijden RK',
    'N': 'kleine klassen samenvoegen BK',
    'O': 'voorbereiding BK',
    'P': 'wedstrijden BK',
    'Q': 'einde competitie',
}


def maak_comp_fase_beschrijvingen(comp):
    indiv = "Competitie fase individueel: %s (%s)" % (comp.fase_indiv, comp_fase_kort[comp.fase_indiv])
    teams = "Competitie fase teams: %s (%s)" % (comp.fase_teams, comp_fase_kort[comp.fase_teams])
    return indiv, teams


# wordt gebruikt vanuit Competitie.tijdlijn
test_met_deze_evaluatie_datum = None


def zet_test_datum(date_str: str):

    global test_met_deze_evaluatie_datum

    if date_str:
        test_met_deze_evaluatie_datum = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        test_met_deze_evaluatie_datum = None


def _zet_competitie_indiv_fase(comp, indiv_fase):

    comp.bk_indiv_afgesloten = True
    comp.bk_indiv_klassen_zijn_samengevoegd = True
    comp.rk_indiv_afgesloten = True
    comp.regiocompetitie_is_afgesloten = True
    comp.klassengrenzen_vastgesteld = True

    if indiv_fase == 'Q':
        # comp.bk_indiv_afgesloten = True
        return

    comp.bk_indiv_afgesloten = False

    if test_met_deze_evaluatie_datum:
        vandaag = test_met_deze_evaluatie_datum
    else:
        vandaag = timezone.now().date()

    gister = vandaag - datetime.timedelta(days=1)
    morgen = vandaag + datetime.timedelta(days=1)

    if indiv_fase >= 'O':
        # BK fases (deel 2)
        # comp.bk_indiv_klassen_zijn_samengevoegd = True

        if indiv_fase == 'O':
            comp.begin_fase_P_indiv = morgen
            return

        comp.begin_fase_P_indiv = gister
        return

    comp.bk_indiv_klassen_zijn_samengevoegd = False

    if indiv_fase == 'N':
        # BK fases (deel 1)
        # comp.rk_indiv_afgesloten = True
        return

    comp.rk_indiv_afgesloten = False

    if indiv_fase >= 'J':
        # RK fases
        # comp.regiocompetitie_is_afgesloten = True

        if indiv_fase == 'J':
            # fase J: begin fase K is minsten 2 weken weg
            comp.begin_fase_L_indiv = morgen + datetime.timedelta(days=14)
            return

        if indiv_fase == 'K':
            # fase K: tot begin fase L
            comp.begin_fase_L_indiv = morgen
            return

        # fase L
        comp.begin_fase_L_indiv = gister
        return

    comp.regiocompetitie_is_afgesloten = False

    # fase A begon toen de competitie werd aangemaakt

    if indiv_fase == 'A':
        comp.klassengrenzen_vastgesteld = False
        return

    if comp.competitieindivklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar indiv fase %s zonder competitie indiv klassen!" % indiv_fase)

    # comp.klassengrenzen_vastgesteld = True

    if indiv_fase == 'B':
        comp.begin_fase_C = morgen
        return

    comp.begin_fase_C = gister

    if indiv_fase == 'C':
        comp.begin_fase_F = morgen
        return

    comp.begin_fase_F = gister
    if indiv_fase == 'F':
        comp.einde_fase_F = morgen
        return

    # fase G
    comp.einde_fase_F = gister


def _zet_competitie_team_fase(comp, team_fase):

    comp.bk_teams_afgesloten = True
    comp.bk_teams_klassen_zijn_samengevoegd = True
    comp.rk_teams_afgesloten = True
    comp.klassengrenzen_vastgesteld_rk_bk = True

    if team_fase == 'Q':
        # comp.bk_teams_afgesloten = True
        return

    comp.bk_teams_afgesloten = False

    if test_met_deze_evaluatie_datum:
        vandaag = test_met_deze_evaluatie_datum
    else:
        vandaag = timezone.now().date()

    gister = vandaag - datetime.timedelta(days=1)
    morgen = vandaag + datetime.timedelta(days=1)

    if team_fase >= 'O':
        # BK fases (deel 2)

        if team_fase == 'O':
            comp.begin_fase_P_teams = morgen
            return

        comp.begin_fase_P_teams = gister
        return

    comp.bk_teams_klassen_zijn_samengevoegd = False

    if team_fase == 'N':
        # BK teams (fase 1)
        # comp.rk_teams_afgesloten = True
        return

    comp.rk_teams_afgesloten = False

    if team_fase >= 'J':
        # RK fases

        if team_fase == 'J':
            comp.klassengrenzen_vastgesteld_rk_bk = False
            return

        # comp.klassengrenzen_vastgesteld_rk_bk = True

        if team_fase == 'K':
            comp.begin_fase_L_teams = morgen
            return

        comp.begin_fase_L_teams = gister
        return

    comp.klassengrenzen_vastgesteld_rk_bk = False

    # fase A begon toen de competitie werd aangemaakt

    if team_fase == 'A':
        return

    if comp.competitieteamklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar team fase %s zonder competitie team klassen!" % team_fase)

    if team_fase == 'B':
        comp.begin_fase_C = morgen
        return

    comp.begin_fase_C = gister

    if team_fase in ('C', 'D'):
        comp.begin_fase_F = morgen
        return

    comp.begin_fase_F = gister

    if team_fase == 'F':
        comp.einde_fase_F = morgen
        return

    # fase G
    comp.einde_fase_F = gister


def zet_competitie_fases(comp, indiv_fase, team_fase):
    """ deze helper weet hoe de Competitie datums en vlaggen gemanipuleerd moeten worden
        om de competitie in de gevraagde fases te krijgen.
    """

    # sommige fases kunnen alleen synchroon gezet worden
    if indiv_fase in ('A', 'B', 'F', 'G', 'Q', 'Z'):
        if team_fase != indiv_fase:
            raise NotImplementedError("Combinatie indiv_fase=%s en team_fase=%s niet ondersteund" % (indiv_fase, team_fase))

    if indiv_fase == 'C' and team_fase not in ('C', 'D'):
        raise NotImplementedError("Combinatie indiv_fase=%s en team_fase=%s niet ondersteund" % (indiv_fase, team_fase))

    if isinstance(comp.begin_fase_L_indiv, str):
        raise NotImplementedError("Kan niet rekenen met string datums (object moet uit database geladen zijn)")

    if indiv_fase == 'Z':
        comp.is_afgesloten = True
        comp.save()
        return

    comp.is_afgesloten = False

    _zet_competitie_indiv_fase(comp, indiv_fase)
    _zet_competitie_team_fase(comp, team_fase)

    comp.save()


def zet_competitie_fase_regio_prep(comp):
    zet_competitie_fases(comp, 'B', 'B')


def zet_competitie_fase_regio_inschrijven(comp):
    zet_competitie_fases(comp, 'C', 'C')


def zet_competitie_fase_regio_wedstrijden(comp):
    zet_competitie_fases(comp, 'F', 'F')


def zet_competitie_fase_regio_afsluiten(comp):
    zet_competitie_fases(comp, 'G', 'G')


def zet_competitie_fase_rk_prep(comp):
    zet_competitie_fases(comp, 'J', 'J')


def zet_competitie_fase_rk_wedstrijden(comp):
    zet_competitie_fases(comp, 'L', 'L')


def zet_competitie_fase_bk_prep(comp):
    zet_competitie_fases(comp, 'O', 'O')


def zet_competitie_fase_bk_wedstrijden(comp):
    zet_competitie_fases(comp, 'P', 'P')


def zet_competitie_fase_afsluiten(comp):
    zet_competitie_fases(comp, 'Q', 'Q')


def bepaal_fase_indiv(comp) -> str:
    """ bepaal de fase van de individuele competitie """

    # fase A was totdat dit object gemaakt werd

    if comp.is_afgesloten:
        return 'Z'

    if comp.bk_indiv_afgesloten:
        return 'Q'

    if test_met_deze_evaluatie_datum:
        now = test_met_deze_evaluatie_datum
    else:
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

    if test_met_deze_evaluatie_datum:
        now = test_met_deze_evaluatie_datum
    else:
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


def is_open_voor_inschrijven_rk_teams(comp):

    """
        comp.fase_teams moet al gezet zijn

        Returns: is_open, vanaf_datum

        True,  None:        Deze competitie open is voor het aanmelden van RK teams
        False, vanaf_datum: De inschrijving gaat binnenkort open
        False, None:        De inschrijving ver in de toekomst of in het verre verleden
    """

    if 'F' <= comp.fase_teams <= 'J':

        vanaf = comp.begin_fase_F + datetime.timedelta(days=settings.COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER)

        if test_met_deze_evaluatie_datum:
            vandaag = test_met_deze_evaluatie_datum
        else:
            vandaag = timezone.now().date()

        if vandaag >= vanaf:
            return True, None

        return False, vanaf

    return False, None


# end of file
