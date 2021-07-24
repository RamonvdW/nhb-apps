# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db.models import Q
from BasisTypen.models import BLAZOEN2STR, BLAZOEN_40CM, BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_DT
from Competitie.models import (RegioCompetitieSchutterBoog, RegiocompetitieTeam,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2, INSCHRIJF_METHODE_3)
from Schutter.models import SchutterVoorkeuren
from types import SimpleNamespace
import math


BLAZOEN_STR_WENS_DT = 'DT (wens)'
BLAZOEN_STR_WENS_4SPOT = '4-spot (wens)'


def bepaal_waarschijnlijke_deelnemers(afstand, deelcomp, wedstrijd):
    """
        bepaal de waarschijnlijke lijst van deelnemers van een wedstrijd

        sporters met meerdere bogen komen maar 1x voor
    """

    # TODO: ondersteuning inschrijfmethode 3 toevoegen - maar hoe?
    if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1:
        # specifiek aangemelde individuele sporters
        deelnemers_indiv = (wedstrijd
                            .regiocompetitieschutterboog_set
                            .select_related('klasse',
                                            'klasse__indiv'))
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
                                                'klasse__indiv'))
        else:
            # fall-back: alle sporters in de hele regio
            deelnemers_indiv = (RegioCompetitieSchutterBoog
                                .objects
                                .filter(deelcompetitie=deelcomp)
                                .select_related('klasse',
                                                'klasse__indiv'))

        if deelcomp.inschrijf_methode == INSCHRIJF_METHODE_2:
            # verder filteren, op gekoppelde wedstrijdklassen

            # team klassen
            team_pks = wedstrijd.team_klassen.values_list('pk', flat=True)
            gekoppeld_pks = RegiocompetitieTeam.objects.filter(klasse__team__pk__in=team_pks).values_list('gekoppelde_schutters__pk', flat=True)

            # individueel
            indiv_pks = wedstrijd.indiv_klassen.values_list('pk', flat=True)
            deelnemers_indiv = deelnemers_indiv.filter(Q(klasse__indiv__pk__in=indiv_pks) | Q(pk__in=gekoppeld_pks))


    # TODO: teams begrenzen tot het cluster
    # TODO: ondersteuning VSG toevoegen voor team deelnemers (nu tonen we sporter AG)
    deelnemers_teams = (RegiocompetitieTeam
                        .objects
                        .filter(deelcompetitie=deelcomp)
                        .select_related('klasse',
                                        'klasse__team'))

    # verenigingsteams
    ver_teams = dict()  # [ver_nr] = dict[team_type] = aantal
    for team in deelnemers_teams:
        ver_nr = team.vereniging.ver_nr
        try:
            type_count = ver_teams[ver_nr]
        except KeyError:
            ver_teams[ver_nr] = type_count = dict()

        try:
            type_count[team.team_type] += 1
        except KeyError:
            type_count[team.team_type] = 1
    # for

    # wens_dt: als het bondsnummer hier in voorkomt heeft de sporters voorkeur voor DT (=eigen blazoen)
    if afstand == '18':
        wens_dt = list(SchutterVoorkeuren
                       .objects
                       .select_related('nhblid')
                       .filter(voorkeur_dutchtarget_18m=True)
                       .values_list('nhblid__nhb_nr', flat=True))
    else:
        wens_dt = list()

    # wens_4spot: als het bondsnummer hier in voorkomt heeft de sporter voorkeur voor de Compound 4-spot (=eigen blazoen)
    wens_4spot = list()
    #wens_4spot = list(SchutterVoorkeuren
    #                   .objects
    #                   .select_related('nhblid')
    #                   .filter(voorkeur_4spot=True)
    #                   .values_list('nhblid__nhb_nr', flat=True))

    nr2para_opmerking = dict()
    for voorkeur in (SchutterVoorkeuren
                     .objects
                     .select_related('nhblid')
                     .exclude(opmerking_para_sporter='')):

        nr2para_opmerking[voorkeur.nhblid.nhb_nr] = voorkeur.opmerking_para_sporter
    # for

    unsorted_sporters = list()
    nr2sporter = dict()

    for deelnemer in deelnemers_indiv:

        schutterboog = deelnemer.schutterboog
        nhblid = schutterboog.nhblid
        nr = nhblid.nhb_nr
        ver = nhblid.bij_vereniging

        try:
            sporter = nr2sporter[nr]
        except KeyError:
            # nieuw record nodig
            sporter = SimpleNamespace()

            sporter.ver_nr = ver.ver_nr
            sporter.ver_naam = ver.naam

            sporter.nhb_nr = nr
            sporter.volledige_naam = nhblid.volledige_naam()

            sporter.schiet_boog_r = False
            sporter.schiet_boog_c = False
            sporter.voorkeur_dt = (nr in wens_dt)
            sporter.voorkeur_4spot = (nr in wens_4spot)
            sporter.is_aspirant = deelnemer.klasse.indiv.is_aspirant_klasse

            sporter.bogen_lijst = list()
            sporter.teams_lijst = list()
            sporter.blazoen_lijst = list()

            try:
                sporter.notitie = nr2para_opmerking[nr]
            except KeyError:
                sporter.notitie = ''

            nr2sporter[nr] = sporter

            if deelnemer.aantal_scores == 0:
                vsg = deelnemer.ag_voor_team
            else:
                vsg = deelnemer.gemiddelde

            # voorbereiden voor sorteren
            volgorde_1 = ver.ver_nr
            volgorde_2 = -vsg     # anders verkeerd om gesorteerd (laagste eerst)
            volgorde_3 = sporter.volledige_naam
            volgorde_4 = nhblid.nhb_nr          # dummy, voorkomt sorteren op Sporter (wat niet kan)
            tup = (volgorde_1, volgorde_2, volgorde_3, volgorde_4, sporter)
            unsorted_sporters.append(tup)

        sporter.wil_team_schieten = deelnemer.inschrijf_voorkeur_team

        for team in deelnemer.regiocompetitieteam_set.all():
            tup = (team.team_type.volgorde, team.maak_team_naam_kort(), team.team_type.beschrijving, deelnemer.ag_voor_team)
            sporter.teams_lijst.append(tup)
        # for

        boog = schutterboog.boogtype
        if boog.afkorting == 'R':
            sporter.schiet_boog_r = True
        elif boog.afkorting == 'C':
            sporter.schiet_boog_c = True

        # TODO: zonder Team-AG kan het geen teamschutter zijn
        if deelnemer.inschrijf_voorkeur_team:
            if deelnemer.aantal_scores == 0:
                vsg = deelnemer.ag_voor_team
            else:
                vsg = deelnemer.gemiddelde
        else:
            vsg = ''    # niet tonen

        tup = (boog.volgorde, boog.beschrijving, vsg, schutterboog.pk)
        sporter.bogen_lijst.append(tup)

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
                type_count = ver_teams[sporter.ver_nr]
            except KeyError:
                pass
            else:
                parts = list()
                for team_type, aantal in type_count.items():
                    tup = (team_type.volgorde, "%sx %s" % (aantal, team_type.beschrijving))
                    parts.append(tup)
                # for
                parts.sort()        # controleer volgorde van de teams
                msg = "[%s] %s heeft " % (sporter.ver_nr, sporter.ver_naam)
                sporter.vereniging_teams = msg + ", ".join([tup[-1] for tup in parts])

        # wens alleen voor juiste boogtype tonen
        sporter.voorkeur_dt &= sporter.schiet_boog_r
        sporter.voorkeur_4spot &= sporter.schiet_boog_c

        sporter.bogen_lijst.sort()      # controleer volgorde van de bogen
        sporter.teams_lijst.sort()      # controleer volgorde van de teams

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
                    teams_60cm=0,
                    teams_60cm_4spot=0,
                    teams_wens_60cm_4spot__anders_60cm=0)

    blazoen_str_dt = BLAZOEN2STR[BLAZOEN_DT]
    blazoen_str_40cm = BLAZOEN2STR[BLAZOEN_40CM]
    blazoen_str_60cm = BLAZOEN2STR[BLAZOEN_60CM]

    for team in deelnemers_teams:
        team_klasse = team.klasse.team

        if afstand == '18':
            blazoen = team_klasse.blazoen_18m_regio
            if blazoen == BLAZOEN_40CM:
                blazoenen.teams_40cm += 1
            elif blazoen == BLAZOEN_DT:
                blazoenen.teams_dt += 1
        else:
            if team_klasse.blazoen1_25m_regio == team_klasse.blazoen2_25m_regio:
                if team_klasse.blazoen1_25m_regio == BLAZOEN_60CM:
                    blazoenen.teams_60cm += 1
                else:
                    blazoenen.teams_60cm_4spot += 1
            else:
                blazoenen.teams_wens_60cm_4spot__anders_60cm += 1
    # for

    for sporter in sporters:

        if sporter.is_aspirant:
            if sporter.voorkeur_4spot:
                blazoenen.sporters_aspirant_wens_60cm_4spot__anders_60cm += 1
            else:
                blazoenen.sporters_aspirant_60cm += 1
        else:
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
    blazoenen.sporters_40cm_excl_teams = blazoenen.sporters_40cm - blazoenen.teams_40cm * 4
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
