# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db.models import Q
from BasisTypen.models import BLAZOEN2STR, BLAZOEN_40CM, BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_DT
from Competitie.models import (RegioCompetitieSchutterBoog, RegiocompetitieTeam,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2, INSCHRIJF_METHODE_3)
from Sporter.models import SporterVoorkeuren
from types import SimpleNamespace
import math


# TODO: vervangen door standaard strings uit BasisTypen
BLAZOEN_STR_WENS_DT = 'DT (wens)'
BLAZOEN_STR_WENS_4SPOT = '4-spot (wens)'


def _query_wedstrijd_deelnemers(afstand, deelcomp, wedstrijd):

    """ geef de lijst van deelnemers en teams terug voor deze wedstrijd,
        rekening houdend met de inschrijfmethode
    """

    # TODO: ondersteuning inschrijfmethode 3 toevoegen - maar hoe?
    if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
        # specifiek aangemelde individuele sporters
        deelnemers_indiv = (wedstrijd
                            .regiocompetitieschutterboog_set
                            .select_related('klasse',
                                            'klasse__indiv',
                                            'sporterboog',
                                            'sporterboog__boogtype',
                                            'sporterboog__sporter',
                                            'sporterboog__sporter__bij_vereniging'))

        if deelcomp.regio_organiseert_teamcompetitie:
            deelnemers_teams = (RegiocompetitieTeam
                                .objects
                                .filter(deelcompetitie=deelcomp)
                                .prefetch_related('team_type__boog_typen')
                                .select_related('vereniging',
                                                'team_type',
                                                'klasse',
                                                'klasse__team'))
    else:
        # vereniging zit in 0 of 1 clusters voor deze competitie
        clusters = wedstrijd.vereniging.clusters.filter(gebruik=afstand)

        if clusters.count() > 0:
            # vereniging zit in een cluster, dus toon alleen de deelnemers van dit cluster
            ver_pks = clusters[0].nhbvereniging_set.values_list('pk', flat=True)
            deelnemers_indiv = (RegioCompetitieSchutterBoog
                                .objects
                                .filter(deelcompetitie=deelcomp,
                                        bij_vereniging__in=ver_pks)
                                .select_related('klasse',
                                                'klasse__indiv',
                                                'sporterboog',
                                                'sporterboog__boogtype',
                                                'sporterboog__sporter',
                                                'sporterboog__sporter__bij_vereniging'))

            if deelcomp.regio_organiseert_teamcompetitie:
                deelnemers_teams = (RegiocompetitieTeam
                                    .objects
                                    .filter(deelcompetitie=deelcomp,
                                            vereniging__in=ver_pks)
                                    .prefetch_related('team_type__boog_typen')
                                    .select_related('vereniging',
                                                    'team_type',
                                                    'klasse',
                                                    'klasse__team'))
        else:
            # fall-back: alle sporters in de hele regio
            deelnemers_indiv = (RegioCompetitieSchutterBoog
                                .objects
                                .filter(deelcompetitie=deelcomp)
                                .select_related('klasse',
                                                'klasse__indiv',
                                                'sporterboog',
                                                'sporterboog__boogtype',
                                                'sporterboog__sporter',
                                                'sporterboog__sporter__bij_vereniging'))

            if deelcomp.regio_organiseert_teamcompetitie:
                deelnemers_teams = (RegiocompetitieTeam
                                    .objects
                                    .filter(deelcompetitie=deelcomp)
                                    .prefetch_related('team_type__boog_typen')
                                    .select_related('vereniging',
                                                    'team_type',
                                                    'klasse',
                                                    'klasse__team'))

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_2:
            # verder filteren, op gekoppelde wedstrijdklassen

            if deelcomp.regio_organiseert_teamcompetitie:
                # team klassen
                team_pks = wedstrijd.team_klassen.values_list('pk', flat=True)
                gekoppeld_pks = RegiocompetitieTeam.objects.filter(klasse__team__pk__in=team_pks).values_list('gekoppelde_schutters__pk', flat=True)
            else:
                gekoppeld_pks = list()

            # individueel
            indiv_pks = wedstrijd.indiv_klassen.values_list('pk', flat=True)
            deelnemers_indiv = deelnemers_indiv.filter(Q(klasse__indiv__pk__in=indiv_pks) | Q(pk__in=gekoppeld_pks))

    if not deelcomp.regio_organiseert_teamcompetitie:
        deelnemers_teams = list()

    return deelnemers_indiv, deelnemers_teams


def bepaal_waarschijnlijke_deelnemers(afstand, deelcomp, wedstrijd):
    """
        bepaal de waarschijnlijke lijst van deelnemers van een wedstrijd

        sporters met meerdere bogen komen meerdere keren voor
    """

    deelnemers_indiv, deelnemers_teams = _query_wedstrijd_deelnemers(afstand, deelcomp, wedstrijd)

    # bepaal voor elke vereniging en boog afkorting in welke teams een sporterboog uit mag komen
    ver_teams = dict()      # [ver_nr] = dict[boog afkorting] = list()
    ver_aantal = dict()     # [ver_nr] = dict[team type] = aantal

    # verenigingsteams
    if deelcomp.regio_organiseert_teamcompetitie:
        for team in deelnemers_teams:
            ver_nr = team.vereniging.ver_nr
            try:
                boog_dict = ver_teams[ver_nr]
                aantal_dict = ver_aantal[ver_nr]
            except KeyError:
                ver_teams[ver_nr] = boog_dict = dict()
                ver_aantal[ver_nr] = aantal_dict = dict()

            try:
                aantal_dict[team.team_type] += 1
            except KeyError:
                aantal_dict[team.team_type] = 1

            for boog in team.team_type.boog_typen.all():
                try:
                    boog_dict[boog.afkorting].append(team)
                except KeyError:
                    boog_dict[boog.afkorting] = [team]
            # for
        # for

    # maak lijst nhb_nrs van sporters met voorkeur voor eigen blazoen
    wens_eigen_blazoen = list(SporterVoorkeuren
                              .objects
                              .select_related('sporter')
                              .filter(voorkeur_eigen_blazoen=True)
                              .values_list('sporter__lid_nr', flat=True))

    lid_nr2para_opmerking = dict()
    for voorkeur in (SporterVoorkeuren
                     .objects
                     .select_related('sporter')
                     .exclude(opmerking_para_sporter='')):

        lid_nr2para_opmerking[voorkeur.sporter.lid_nr] = voorkeur.opmerking_para_sporter
    # for

    unsorted_sporters = list()
    for deelnemer in deelnemers_indiv:
        sporterboog = deelnemer.sporterboog
        sporter = sporterboog.sporter
        ver = sporter.bij_vereniging
        boog = sporterboog.boogtype

        sporter = SimpleNamespace(
                        lid_nr=sporter.lid_nr,
                        volledige_naam=sporter.volledige_naam(),
                        ver_nr=ver.ver_nr,
                        ver_naam=ver.naam,
                        boog=boog.beschrijving,
                        sporterboog_pk=sporterboog.pk,
                        deelnemer_pk=deelnemer.pk,
                        schiet_boog_r=(boog.afkorting == 'R'),
                        schiet_boog_c=(boog.afkorting == 'C'),
                        voorkeur_dt=(sporter.lid_nr in wens_eigen_blazoen),
                        voorkeur_4spot=(sporter.lid_nr in wens_eigen_blazoen),
                        is_aspirant=deelnemer.klasse.indiv.is_aspirant_klasse,
                        wil_team_schieten=deelnemer.inschrijf_voorkeur_team,
                        team_pk=0,
                        vsg="")

        # wens alleen voor juiste boogtype tonen
        sporter.voorkeur_dt &= sporter.schiet_boog_r
        sporter.voorkeur_4spot &= sporter.schiet_boog_c

        try:
            sporter.notitie = lid_nr2para_opmerking[sporter.lid_nr]
        except KeyError:
            sporter.notitie = ''

        if deelnemer.aantal_scores == 0:
            vsg = deelnemer.ag_voor_team
        else:
            vsg = deelnemer.gemiddelde      # individuele voortschrijdend gemiddelde

        sporter.blazoen_lijst = list()

        # voorbereiden voor sorteren
        volgorde_1 = ver.ver_nr
        volgorde_2 = -vsg     # negatief geeft hoogste bovenaan
        volgorde_3 = sporter.volledige_naam
        volgorde_4 = deelnemer.pk                # dummy, voorkomt sorteren op Sporter (wat niet kan)
        tup = (volgorde_1, volgorde_2, volgorde_3, volgorde_4, sporter)
        unsorted_sporters.append(tup)

        # TODO: ondersteuning VSG toevoegen voor team deelnemers (nu tonen we sporter AG)
        # TODO: zonder Team-AG kan het geen teamschutter zijn
        if deelnemer.inschrijf_voorkeur_team:
            if deelnemer.aantal_scores == 0:
                sporter.vsg = deelnemer.ag_voor_team
            else:
                sporter.vsg = deelnemer.gemiddelde

            # zoek het huidige team erbij
            ronde_teams = deelnemer.teamronde_feitelijk.filter(ronde_nr=deelcomp.huidige_team_ronde)
            if ronde_teams.count() > 0:
                # sporter is gekoppeld aan een team
                sporter.team_pk = ronde_teams[0].team.pk

        if afstand == '18':
            blazoenen = (deelnemer.klasse.indiv.blazoen1_18m_regio, deelnemer.klasse.indiv.blazoen2_18m_regio)
        else:
            blazoenen = (deelnemer.klasse.indiv.blazoen1_25m_regio, deelnemer.klasse.indiv.blazoen2_25m_regio)
        for blazoen in blazoenen:
            if blazoen not in sporter.blazoen_lijst:
                sporter.blazoen_lijst.append(blazoen)
        # for
    # for

    # sorteer
    unsorted_sporters.sort()

    sporters = [tup[-1] for tup in unsorted_sporters]

    # bogen uitspellen
    prev_ver_nr = 0
    for sporter in sporters:

        if prev_ver_nr != sporter.ver_nr:
            prev_ver_nr = sporter.ver_nr
            try:
                aantal_dict = ver_aantal[sporter.ver_nr]
            except KeyError:
                pass
            else:
                parts = list()
                for team_type, aantal in aantal_dict.items():
                    tup = (team_type.volgorde, "%sx %s" % (aantal, team_type.beschrijving))
                    parts.append(tup)
                # for
                parts.sort()        # controleer volgorde van de teams
                msg = "[%s] %s heeft " % (sporter.ver_nr, sporter.ver_naam)
                sporter.vereniging_teams = msg + ", ".join([tup[-1] for tup in parts])

        blazoenen = sporter.blazoen_lijst[:]
        sporter.blazoen_str_lijst = lijst = list()

        if BLAZOEN_DT in blazoenen and BLAZOEN_40CM in blazoenen:
            if sporter.voorkeur_dt:
                blazoenen.remove(BLAZOEN_40CM)
                blazoenen.remove(BLAZOEN_DT)
                lijst.append(BLAZOEN_STR_WENS_DT)
            else:
                # behoud 40cm
                blazoenen.remove(BLAZOEN_DT)

        if BLAZOEN_60CM in blazoenen and BLAZOEN_60CM_4SPOT in blazoenen:
            if sporter.voorkeur_4spot:
                blazoenen.remove(BLAZOEN_60CM)
                blazoenen.remove(BLAZOEN_60CM_4SPOT)
                lijst.append(BLAZOEN_STR_WENS_4SPOT)
            else:
                # behoud 60cm
                blazoenen.remove(BLAZOEN_60CM_4SPOT)

        for blazoen in blazoenen:
            lijst.append(BLAZOEN2STR[blazoen])
        # for
    # for

    return sporters, deelnemers_teams


def bepaal_blazoen_behoefte(afstand, sporters, deelnemers_teams):
    """ bepaal hoeveel blazoenen er nodig zijn, gebaseerd op de lijst van waarschijnlijke deelnemers. """

    blazoenen = SimpleNamespace(
                    sporters_dt=0,       # TODO: opsplitsen in R en C variant?
                    sporters_40cm=0,
                    sporters_60cm=0,
                    sporters_60cm_4spot=0,          # alleen voor RK/BK
                    sporters_aspirant_60cm=0,
                    sporters_aspirant_wens_60cm_4spot__anders_60cm=0,
                    sporters_wens_dt__anders_40cm=0,
                    sporters_wens_60cm_4spot__anders_60cm=0,
                    teams_dt=0,
                    teams_40cm=0,
                    teams_dt_of_40cm=0,             # team kiest
                    teams_60cm=0,
                    teams_60cm_4spot=0,
                    teams_60cm_4spot_of_60cm=0)     # team kiest

    blazoen_str_dt = BLAZOEN2STR[BLAZOEN_DT]
    blazoen_str_40cm = BLAZOEN2STR[BLAZOEN_40CM]
    blazoen_str_60cm = BLAZOEN2STR[BLAZOEN_60CM]

    ver2teams = dict()      # [ver_nr] = aantal teams van deze vereniging

    for team in deelnemers_teams:

        # team wat nog niet in een klasse staat slaan we over
        if team.klasse:
            team_klasse = team.klasse.team

            ver_nr = team.vereniging.ver_nr
            try:
                ver2teams[ver_nr] += 1
            except KeyError:
                ver2teams[ver_nr] = 1

            if afstand == '18':
                if team_klasse.blazoen1_18m_regio == team_klasse.blazoen2_18m_regio:
                    blazoen = team_klasse.blazoen1_18m_regio
                    if blazoen == BLAZOEN_40CM:
                        blazoenen.teams_40cm += 1
                    elif blazoen == BLAZOEN_DT:
                        blazoenen.teams_dt += 1
                else:
                    blazoenen.teams_dt_of_40cm += 1
            else:
                if team_klasse.blazoen1_25m_regio == team_klasse.blazoen2_25m_regio:
                    if team_klasse.blazoen1_25m_regio == BLAZOEN_60CM:
                        blazoenen.teams_60cm += 1
                    else:
                        blazoenen.teams_60cm_4spot += 1
                else:
                    blazoenen.teams_60cm_4spot_of_60cm += 1
    # for

    ver2count = dict()      # [ver_nr] = aantal ingeschreven sporters met voorkeur voor teamschieten

    for sporter in sporters:
        if sporter.is_aspirant:
            if sporter.voorkeur_4spot:
                blazoenen.sporters_aspirant_wens_60cm_4spot__anders_60cm += 1
            else:
                blazoenen.sporters_aspirant_60cm += 1
        else:
            if sporter.wil_team_schieten:
                try:
                    ver2count[sporter.ver_nr] += 1
                except KeyError:
                    ver2count[sporter.ver_nr] = 1

            for blaz in sporter.blazoen_str_lijst:
                if blaz == BLAZOEN_STR_WENS_4SPOT:
                    blazoenen.sporters_wens_60cm_4spot__anders_60cm += 1
                elif blaz == BLAZOEN_STR_WENS_DT:
                    blazoenen.sporters_wens_dt__anders_40cm += 1
                elif blaz == blazoen_str_40cm:
                    blazoenen.sporters_40cm += 1
                elif blaz == blazoen_str_60cm:
                    blazoenen.sporters_60cm += 1
                elif blaz == blazoen_str_dt:
                    blazoenen.sporters_dt += 1
            # for
    # for

    blazoenen.sporters_60cm_excl_teams = blazoenen.sporters_60cm - blazoenen.teams_60cm * 4
    blazoenen.sporters_60cm_4spot_excl_teams = blazoenen.sporters_60cm_4spot - blazoenen.teams_60cm_4spot * 4
    blazoenen.sporters_40cm_excl_teams = max(0, blazoenen.sporters_40cm - blazoenen.teams_40cm * 4)
    blazoenen.sporters_dt_excl_teams = blazoenen.sporters_dt - blazoenen.teams_dt * 4

    blazoenen.banen_aspiranten_60cm = math.ceil(blazoenen.sporters_aspirant_60cm / 4.0)
    blazoenen.banen_aspiranten_wens_60cm_4spot = math.ceil(blazoenen.sporters_aspirant_wens_60cm_4spot__anders_60cm / 4.0)

    blazoenen.banen_60cm_excl_teams = math.ceil(blazoenen.sporters_60cm_excl_teams / 4.0)
    blazoenen.banen_60cm_4spot_excl_teams = math.ceil(blazoenen.sporters_60cm_4spot_excl_teams / 4.0)
    blazoenen.banen_40cm_excl_teams = math.ceil(blazoenen.sporters_40cm_excl_teams / 4.0)
    blazoenen.banen_dt_excl_teams = math.ceil(blazoenen.sporters_dt_excl_teams / 4.0)

    blazoenen.plekjes_over_60cm = (blazoenen.banen_60cm_excl_teams * 4) - blazoenen.sporters_60cm_excl_teams
    blazoenen.plekjes_over_60cm_4spot = (blazoenen.banen_60cm_4spot_excl_teams * 4) - blazoenen.sporters_60cm_4spot_excl_teams
    blazoenen.plekjes_over_40cm = (blazoenen.banen_40cm_excl_teams * 4) - blazoenen.sporters_40cm_excl_teams

    return blazoenen


# end of file
