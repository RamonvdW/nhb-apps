# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import DEEL_RK
from Competitie.models import Competitie, Kampioenschap
from Competitie.operations import (competities_aanmaken, aanvangsgemiddelden_vaststellen_voor_afstand,
                                   competitie_klassengrenzen_vaststellen)
import datetime


def _zet_competitie_indiv_fase(comp, indiv_fase):

    if indiv_fase == 'Q':
        comp.bk_indiv_afgesloten = True
        return

    comp.bk_indiv_afgesloten = False

    now = timezone.now()
    vandaag = datetime.date(year=now.year, month=now.month, day=now.day)
    gister = vandaag - datetime.timedelta(days=1)
    morgen = vandaag + datetime.timedelta(days=1)

    if indiv_fase >= 'O':
        # BK fases (deel 2)
        comp.bk_indiv_klassen_zijn_samengevoegd = True

        if indiv_fase == 'O':
            comp.begin_fase_P_indiv = morgen
            return

        comp.begin_fase_P_indiv = gister
        return

    comp.bk_indiv_klassen_zijn_samengevoegd = False

    if indiv_fase == 'N':
        # BK fases (deel 1)
        comp.rk_indiv_afgesloten = True
        return

    comp.rk_indiv_afgesloten = False

    if indiv_fase >= 'J':
        # RK fases
        comp.regiocompetitie_is_afgesloten = True

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
        raise NotImplementedError("Kan niet naar fase %s zonder competitie indiv klassen!" % fase)

    comp.klassengrenzen_vastgesteld = True

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

    if team_fase == 'Q':
        comp.bk_teams_afgesloten = True
        return

    comp.bk_teams_afgesloten = False

    now = timezone.now()
    vandaag = datetime.date(year=now.year, month=now.month, day=now.day)
    gister = vandaag - datetime.timedelta(days=1)
    morgen = vandaag + datetime.timedelta(days=1)

    if team_fase >= 'O':
        # BK fases (deel 2)
        comp.bk_teams_klassen_zijn_samengevoegd = True

        if team_fase == 'O':
            comp.begin_fase_P_teams = morgen
            return

        comp.begin_fase_P_teams = gister
        return

    comp.bk_teams_klassen_zijn_samengevoegd = False

    if team_fase == 'N':
        # BK teams (fase 1)
        comp.rk_teams_afgesloten = True
        return

    comp.rk_teams_afgesloten = False

    if team_fase >= 'J':
        # RK fases
        comp.regiocompetitie_is_afgesloten = True

        if team_fase == 'J':
            comp.klassengrenzen_vastgesteld_rk_bk = False
            return

        comp.klassengrenzen_vastgesteld_rk_bk = True

        if team_fase == 'K':
            comp.begin_fase_L_teams = morgen
            return

        comp.begin_fase_L_teams = gister
        return

    comp.regiocompetitie_is_afgesloten = False

    # fase A begon toen de competitie werd aangemaakt

    if team_fase == 'A':
        comp.klassengrenzen_vastgesteld = False
        return

    if comp.competitieteamklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar fase %s zonder competitie team klassen!" % fase)

    comp.klassengrenzen_vastgesteld = True

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
    if indiv_fase in ('A', 'B', 'C', 'F', 'G', 'Q', 'Z'):
        if team_fase != indiv_fase:
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


def maak_competities_en_zet_fase_b(startjaar=None):
    """ Competities 18m en 25m aanmaken, AG vaststellen, klassengrenzen vaststelen, instellen op fase B """

    # dit voorkomt kennis en afhandelen van achtergrondtaken in alle applicatie test suites

    # competitie aanmaken
    competities_aanmaken(startjaar)

    comp_18 = Competitie.objects.get(afstand='18')
    comp_25 = Competitie.objects.get(afstand='25')

    # aanvangsgemiddelden vaststellen
    aanvangsgemiddelden_vaststellen_voor_afstand(18)
    aanvangsgemiddelden_vaststellen_voor_afstand(25)

    # klassengrenzen vaststellen
    competitie_klassengrenzen_vaststellen(comp_18)
    competitie_klassengrenzen_vaststellen(comp_25)

    zet_competitie_fases(comp_18, 'B', 'B')
    zet_competitie_fases(comp_25, 'B', 'B')

    return comp_18, comp_25


# end of file
