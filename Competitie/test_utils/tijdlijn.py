# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.tijdlijn import evaluatie_datum
import datetime


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

    vandaag = evaluatie_datum.gekozen_datum
    if not vandaag:
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
        comp.begin_fase_D_indiv = morgen
        return

    comp.begin_fase_D_indiv = gister
    if indiv_fase == 'D':
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

    vandaag = evaluatie_datum.gekozen_datum
    if not vandaag:
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

    # volgende worden in _zet_competitie_indiv_fase gezet
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
        if team_fase != indiv_fase:                                         # pragma: no cover
            raise NotImplementedError("Combinatie indiv_fase=%s en team_fase=%s niet ondersteund" % (
                                        indiv_fase, team_fase))

    if indiv_fase in ('C', 'D') and team_fase not in ('C', 'D'):            # pragma: no cover
        raise NotImplementedError("Combinatie indiv_fase=%s en team_fase=%s niet ondersteund" % (
                                        indiv_fase, team_fase))

    if isinstance(comp.begin_fase_L_indiv, str):                            # pragma: no cover
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


def zet_competitie_fase_bk_klein(comp):
    zet_competitie_fases(comp, 'N', 'N')


def zet_competitie_fase_bk_prep(comp):
    zet_competitie_fases(comp, 'O', 'O')


def zet_competitie_fase_bk_wedstrijden(comp):
    zet_competitie_fases(comp, 'P', 'P')


def zet_competitie_fase_afsluiten(comp):
    zet_competitie_fases(comp, 'Q', 'Q')


# end of file
