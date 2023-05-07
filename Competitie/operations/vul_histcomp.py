# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.definities import DEEL_RK, DEEL_BK, KAMP_RANK_BLANCO
from Competitie.models import (CompetitieIndivKlasse,
                               RegiocompetitieSporterBoog, RegiocompetitieRondeTeam,
                               KampioenschapSporterBoog, KampioenschapTeam)
from HistComp.definities import HISTCOMP_RK, HISTCOMP_BK
from HistComp.models import (HistCompetitie,
                             HistCompRegioIndiv, HistCompRegioTeam,
                             HistKampIndiv, HistKampTeam)


def uitslag_regio_indiv_naar_histcomp(comp):
    """ uitslag regiocompetitie individueel overnemen als histcomp """

    seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

    try:
        histcomps = HistCompetitie.objects.filter(seizoen=seizoen,
                                                  comp_type=comp.afstand,
                                                  is_team=False)
    except HistCompetitie.DoesNotExist:
        pass
    else:
        # er bestaat al een uitslag - verwijder deze eerst
        histcomps.delete()

    boogtype_pk2histcomp = dict()
    for boogtype in comp.boogtypen.all():
        histcomp = HistCompetitie(seizoen=seizoen,
                                  comp_type=comp.afstand,
                                  beschrijving=boogtype.beschrijving,
                                  is_team=False,
                                  is_openbaar=False)                # nog niet laten zien
        histcomp.save()
        boogtype_pk2histcomp[boogtype.pk] = histcomp
    # for

    aantal = 0
    bulk = list()
    for boogtype in comp.boogtypen.all():
        histcomp = boogtype_pk2histcomp[boogtype.pk]

        klassen_pks = (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=comp,
                               boogtype=boogtype)
                       .values_list('pk', flat=True))

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'regiocompetitie__nhb_regio',
                                      'indiv_klasse')
                      .filter(regiocompetitie__competitie=comp,
                              indiv_klasse__in=klassen_pks)
                      .order_by('-gemiddelde'))     # hoogste boven

        rank = 0
        for deelnemer in deelnemers:
            # skip sporters met helemaal geen scores
            if deelnemer.totaal > 0:
                aantal += 1
                rank += 1
                sporter = deelnemer.sporterboog.sporter
                ver = deelnemer.bij_vereniging
                hist = HistCompRegioIndiv(
                            histcompetitie=histcomp,
                            klasse_indiv=deelnemer.indiv_klasse.beschrijving,
                            rank=rank,
                            sporter_lid_nr=sporter.lid_nr,
                            sporter_naam=sporter.volledige_naam(),
                            boogtype=boogtype.afkorting,
                            vereniging_nr=ver.ver_nr,
                            vereniging_naam=ver.naam,
                            vereniging_plaats=ver.plaats,
                            regio_nr=deelnemer.regiocompetitie.nhb_regio.regio_nr,
                            score1=deelnemer.score1,
                            score2=deelnemer.score2,
                            score3=deelnemer.score3,
                            score4=deelnemer.score4,
                            score5=deelnemer.score5,
                            score6=deelnemer.score6,
                            score7=deelnemer.score7,
                            laagste_score_nr=deelnemer.laagste_score_nr,
                            totaal=deelnemer.totaal,
                            gemiddelde=deelnemer.gemiddelde)

                bulk.append(hist)
                if len(bulk) >= 500:
                    HistCompRegioIndiv.objects.bulk_create(bulk)
                    bulk = list()
        # for

    # for

    if len(bulk):
        HistCompRegioIndiv.objects.bulk_create(bulk)

    print('[INFO] --> %s' % aantal)


def uitslag_rk_indiv_naar_histcomp(comp):
    """ uitslag rk individueel overnemen als histcomp
        maak voor elke sporter een HistCompKampioenschapIndiv record aan
    """

    seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

    beschrijving2boogtype_pk = dict()
    for boogtype in comp.boogtypen.all():
        beschrijving2boogtype_pk[boogtype.beschrijving] = boogtype.pk
    # for

    boogtype_pk2histcomp = dict()
    for histcomp in HistCompetitie.objects.filter(seizoen=seizoen, comp_type=comp.afstand, is_team=False):
        pk = beschrijving2boogtype_pk[histcomp.beschrijving]
        boogtype_pk2histcomp[pk] = histcomp
    # for

    vlag_rk = list()

    aantal = 0
    bulk = list()
    for deelnemer in (KampioenschapSporterBoog
                      .objects
                      .filter(kampioenschap__competitie=comp,
                              kampioenschap__deel=DEEL_RK)
                      .select_related('sporterboog__sporter',
                                      'sporterboog__boogtype',
                                      'kampioenschap__nhb_rayon',
                                      'bij_vereniging',
                                      'indiv_klasse')):

        # sporters met rank=0 toch opnemen ivm mogelijk koppeling aan team
        is_in_team = deelnemer.kampioenschapteam_feitelijke_leden.count() > 0

        if 0 < deelnemer.result_rank <= KAMP_RANK_BLANCO or is_in_team:
            kampioenschap = deelnemer.kampioenschap
            sporter = deelnemer.sporterboog.sporter
            boogtype = deelnemer.sporterboog.boogtype
            ver = deelnemer.bij_vereniging
            histcomp = boogtype_pk2histcomp[boogtype.pk]

            if deelnemer.result_rank > KAMP_RANK_BLANCO:
                deelnemer.result_rank = 0                   # verwijder speciale codes (no show / reserve)

            hist = HistKampIndiv(
                            histcompetitie=histcomp,
                            klasse_indiv=deelnemer.indiv_klasse.beschrijving,
                            sporter_lid_nr=sporter.lid_nr,
                            sporter_naam=sporter.volledige_naam(),
                            boogtype=boogtype.afkorting,
                            vereniging_nr=ver.ver_nr,
                            vereniging_naam=ver.naam,
                            vereniging_plaats=ver.plaats,
                            rayon_nr=kampioenschap.nhb_rayon.rayon_nr,
                            rank_rk=deelnemer.result_rank,
                            rk_score_is_blanco=(deelnemer.result_rank == KAMP_RANK_BLANCO),
                            rk_score_1=deelnemer.result_score_1,
                            rk_score_2=deelnemer.result_score_2)
            bulk.append(hist)
            aantal += 1

            if histcomp not in vlag_rk:
                vlag_rk.append(histcomp)
    # for

    HistKampIndiv.objects.bulk_create(bulk)
    print('[INFO] --> %s' % aantal)

    for histcomp in vlag_rk:
        histcomp.heeft_uitslag_rk = True
        histcomp.save(update_fields=['heeft_uitslag_rk'])
    # for


def uitslag_bk_indiv_naar_histcomp(comp):
    """ uitslag bk individueel overnemen als histcomp """

    seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

    histcomp_pks = list(HistCompetitie
                        .objects
                        .filter(seizoen=seizoen,
                                comp_type=comp.afstand,
                                is_team=False)
                        .values_list('pk', flat=True))

    klasse_indiv_lid_nr2hist = dict()
    for hist in HistKampIndiv.objects.filter(histcompetitie__pk__in=histcomp_pks):
        tup = (hist.klasse_indiv, hist.sporter_lid_nr)
        klasse_indiv_lid_nr2hist[tup] = hist
    # for

    vlag_bk = list()
    aantal = 0
    for deelnemer in (KampioenschapSporterBoog
                      .objects
                      .filter(kampioenschap__competitie=comp,
                              kampioenschap__deel=DEEL_BK)
                      .select_related('sporterboog__sporter',
                                      'sporterboog__boogtype',
                                      'bij_vereniging',
                                      'indiv_klasse')):

        if 0 < deelnemer.result_rank < KAMP_RANK_BLANCO:
            sporter = deelnemer.sporterboog.sporter

            tup = (deelnemer.indiv_klasse.beschrijving, sporter.lid_nr)
            hist = klasse_indiv_lid_nr2hist[tup]

            if deelnemer.result_rank > KAMP_RANK_BLANCO:
                deelnemer.result_rank = 0                   # verwijder speciale codes (no show / reserve)

            hist.rank_bk = deelnemer.result_rank
            hist.bk_score_1 = deelnemer.result_score_1
            hist.bk_score_2 = deelnemer.result_score_2
            hist.save(update_fields=['rank_bk', 'bk_score_1', 'bk_score_2'])

            aantal += 1

            histcomp = hist.histcompetitie
            if histcomp not in vlag_bk:
                vlag_bk.append(histcomp)
    # for

    for histcomp in vlag_bk:
        histcomp.heeft_uitslag_bk = True
        histcomp.save(update_fields=['heeft_uitslag_bk'])
    # for

    print('[INFO] --> %s' % aantal)


def uitslag_regio_teams_naar_histcomp(comp):
    """ uitslag regiocompetitie teams overnemen als histcomp """

    seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

    try:
        histcomps = HistCompetitie.objects.filter(seizoen=seizoen,
                                                  comp_type=comp.afstand,
                                                  is_team=True)
    except HistCompetitie.DoesNotExist:
        pass
    else:
        # er bestaat al een uitslag - verwijder deze eerst
        histcomps.delete()

    teamtype_pk2histcomp = dict()
    for teamtype in comp.teamtypen.all():
        histcomp = HistCompetitie(seizoen=seizoen,
                                  comp_type=comp.afstand,
                                  beschrijving=teamtype.beschrijving,
                                  is_team=True,
                                  is_openbaar=False)                # nog niet laten zien
        histcomp.save()
        teamtype_pk2histcomp[teamtype.pk] = histcomp
    # for

    aantal = 0

    bulk = list()
    prev_team = None
    hist = None
    unsorted = list()
    for ronde in (RegiocompetitieRondeTeam
                  .objects
                  .filter(team__regiocompetitie__competitie=comp)
                  .select_related('team',
                                  'team__regiocompetitie',
                                  'team__regiocompetitie__nhb_regio')
                  .order_by('team',
                            'ronde_nr')):

        if ronde.team != prev_team:
            if hist:
                tup = (hist.totaal_punten, hist.totaal_score, len(unsorted), hist)
                unsorted.append(tup)

            team = ronde.team
            histcomp = teamtype_pk2histcomp[team.team_type.pk]
            ver = team.vereniging

            aantal += 1
            hist = HistCompRegioTeam(
                        histcompetitie=histcomp,
                        team_klasse=team.team_klasse.beschrijving,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        regio_nr=team.regiocompetitie.nhb_regio.regio_nr,
                        team_nr=team.volg_nr)
            bulk.append(hist)

            prev_team = ronde.team

        hist.totaal_punten += ronde.team_punten
        hist.totaal_score += ronde.team_score

        if ronde.ronde_nr == 1:
            hist.ronde_1_score = ronde.team_score
            hist.ronde_1_punten = ronde.team_punten
        elif ronde.ronde_nr == 2:
            hist.ronde_2_score = ronde.team_score
            hist.ronde_2_punten = ronde.team_punten
        elif ronde.ronde_nr == 3:
            hist.ronde_3_score = ronde.team_score
            hist.ronde_3_punten = ronde.team_punten
        elif ronde.ronde_nr == 4:
            hist.ronde_4_score = ronde.team_score
            hist.ronde_4_punten = ronde.team_punten
        elif ronde.ronde_nr == 5:
            hist.ronde_5_score = ronde.team_score
            hist.ronde_5_punten = ronde.team_punten
        elif ronde.ronde_nr == 6:
            hist.ronde_6_score = ronde.team_score
            hist.ronde_6_punten = ronde.team_punten
        elif ronde.ronde_nr == 7:
            hist.ronde_7_score = ronde.team_score
            hist.ronde_7_punten = ronde.team_punten
    # for

    teamklasse_rank = dict()
    unsorted.sort()
    for tup in unsorted:
        hist = tup[-1]
        try:
            rank = teamklasse_rank[hist.team_klasse]
        except KeyError:
            rank = 0
        rank += 1
        hist.rank = rank
        teamklasse_rank[hist.team_klasse] = rank
    # for

    HistCompRegioTeam.objects.bulk_create(bulk)

    print('[INFO] --> %s' % aantal)


def uitslag_rk_teams_naar_histcomp(comp):
    """ uitslag rk teams overnemen als histcomp """

    seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

    histcomp_pks = list(HistCompetitie
                        .objects
                        .filter(seizoen=seizoen,
                                comp_type=comp.afstand,
                                is_team=False)
                        .values_list('pk', flat=True))

    klasse_indiv_lid_nr2hist = dict()
    for hist in HistKampIndiv.objects.filter(histcompetitie__pk__in=histcomp_pks):
        tup = (hist.klasse_indiv, hist.sporter_lid_nr)
        klasse_indiv_lid_nr2hist[tup] = hist
    # for

    beschrijving2teamtype_pk = dict()
    for teamtype in comp.teamtypen.all():
        beschrijving2teamtype_pk[teamtype.beschrijving] = teamtype.pk
    # for

    teamtype_pk2histcomp = dict()
    for histcomp in HistCompetitie.objects.filter(seizoen=seizoen, comp_type=comp.afstand, is_team=True):
        pk = beschrijving2teamtype_pk[histcomp.beschrijving]
        teamtype_pk2histcomp[pk] = histcomp
    # for

    aantal = 0
    bulk = list()
    vlag_rk = list()
    for team in (KampioenschapTeam
                 .objects
                 .filter(kampioenschap__competitie=comp,
                         kampioenschap__deel=DEEL_RK)
                 .select_related('team_klasse',
                                 'team_type',
                                 'vereniging')
                 .prefetch_related('feitelijke_leden')):

        if team.result_rank > 0:
            histcomp = teamtype_pk2histcomp[team.team_type.pk]
            ver = team.vereniging

            hist = HistKampTeam(
                        histcompetitie=histcomp,
                        rk_of_bk=HISTCOMP_RK,
                        klasse_teams=team.team_klasse.beschrijving,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        team_nr=team.volg_nr,
                        team_score=team.result_teamscore,
                        rank=team.result_rank)

            unsorted = list()
            for team_lid in team.feitelijke_leden.select_related('indiv_klasse', 'sporterboog__sporter').all():

                s1 = team_lid.result_rk_teamscore_1
                s2 = team_lid.result_rk_teamscore_2

                lid_nr = team_lid.sporterboog.sporter.lid_nr
                tup = (team_lid.indiv_klasse.beschrijving, lid_nr)
                hist_indiv = klasse_indiv_lid_nr2hist[tup]
                hist_indiv.teams_rk_score_1 = s1
                hist_indiv.teams_rk_score_2 = s2
                hist_indiv.save(update_fields=['teams_rk_score_1', 'teams_rk_score_2'])

                tup = (s1, s2, max(s1, s2), min(s1, s2), lid_nr, hist_indiv)
                unsorted.append(tup)
            # for
            unsorted.sort(reverse=True)     # hoogste eerst

            if len(unsorted) > 0:
                s1, s2, _, _, _, hist_indiv = unsorted[0]
                hist.score_lid_1 = s1 + s2
                hist.lid_1 = hist_indiv

            if len(unsorted) > 1:
                s1, s2, _, _, _, hist_indiv = unsorted[1]
                hist.score_lid_2 = s1 + s2
                hist.lid_2 = hist_indiv

            if len(unsorted) > 2:
                s1, s2, _, _, _, hist_indiv = unsorted[2]
                hist.score_lid_3 = s1 + s2
                hist.lid_3 = hist_indiv

            if len(unsorted) > 3:
                s1, s2, _, _, _, hist_indiv = unsorted[3]
                hist.score_lid_4 = s1 + s2
                hist.lid_4 = hist_indiv

            bulk.append(hist)
            aantal += 1

            if histcomp not in vlag_rk:
                vlag_rk.append(histcomp)
    # for

    HistKampTeam.objects.bulk_create(bulk)

    for histcomp in vlag_rk:
        histcomp.heeft_uitslag_rk = True
        histcomp.save(update_fields=['heeft_uitslag_rk'])
    # for

    print('[INFO] --> %s' % aantal)


def uitslag_bk_teams_naar_histcomp(comp):
    """ uitslag bk teams overnemen als histcomp """

    seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

    histcomp_pks = list(HistCompetitie
                        .objects
                        .filter(seizoen=seizoen,
                                comp_type=comp.afstand,
                                is_team=False)
                        .values_list('pk', flat=True))

    klasse_indiv_lid_nr2hist = dict()
    for hist in HistKampIndiv.objects.filter(histcompetitie__pk__in=histcomp_pks):
        tup = (hist.klasse_indiv, hist.sporter_lid_nr)
        klasse_indiv_lid_nr2hist[tup] = hist
    # for

    beschrijving2teamtype_pk = dict()
    for teamtype in comp.teamtypen.all():
        beschrijving2teamtype_pk[teamtype.beschrijving] = teamtype.pk
    # for

    teamtype_pk2histcomp = dict()
    for histcomp in HistCompetitie.objects.filter(seizoen=seizoen, comp_type=comp.afstand, is_team=True):
        pk = beschrijving2teamtype_pk[histcomp.beschrijving]
        teamtype_pk2histcomp[pk] = histcomp
    # for

    aantal = 0
    bulk = list()
    vlag_bk = list()
    for team in (KampioenschapTeam
                 .objects
                 .filter(kampioenschap__competitie=comp,
                         kampioenschap__deel=DEEL_BK)
                 .select_related('team_klasse',
                                 'team_type',
                                 'vereniging')
                 .prefetch_related('feitelijke_leden')):

        if team.result_rank > 0:
            histcomp = teamtype_pk2histcomp[team.team_type.pk]
            ver = team.vereniging

            hist = HistKampTeam(
                        histcompetitie=histcomp,
                        rk_of_bk=HISTCOMP_BK,
                        klasse_teams=team.team_klasse.beschrijving,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        team_nr=team.volg_nr,
                        team_score=team.result_teamscore,
                        rank=team.result_rank)

            unsorted = list()
            for team_lid in team.feitelijke_leden.select_related('indiv_klasse', 'sporterboog__sporter').all():

                s1 = team_lid.result_bk_teamscore_1
                s2 = team_lid.result_bk_teamscore_2

                lid_nr = team_lid.sporterboog.sporter.lid_nr
                tup = (team_lid.indiv_klasse.beschrijving, lid_nr)
                hist_indiv = klasse_indiv_lid_nr2hist[tup]
                hist_indiv.teams_bk_score_1 = s1
                hist_indiv.teams_bk_score_2 = s2
                hist_indiv.save(update_fields=['teams_bk_score_1', 'teams_bk_score_2'])

                tup = (s1, s2, max(s1, s2), min(s1, s2), lid_nr, hist_indiv)
                unsorted.append(tup)
            # for
            unsorted.sort(reverse=True)     # hoogste eerst

            if len(unsorted) > 0:
                s1, s2, _, _, _, hist_indiv = unsorted[0]
                hist.score_lid_1 = s1 + s2
                hist.lid_1 = hist_indiv

            if len(unsorted) > 1:
                s1, s2, _, _, _, hist_indiv = unsorted[1]
                hist.score_lid_2 = s1 + s2
                hist.lid_2 = hist_indiv

            if len(unsorted) > 2:
                s1, s2, _, _, _, hist_indiv = unsorted[2]
                hist.score_lid_3 = s1 + s2
                hist.lid_3 = hist_indiv

            if len(unsorted) > 3:
                s1, s2, _, _, _, hist_indiv = unsorted[3]
                hist.score_lid_4 = s1 + s2
                hist.lid_4 = hist_indiv

            bulk.append(hist)
            aantal += 1

            if histcomp not in vlag_bk:
                vlag_bk.append(histcomp)
    # for

    HistKampTeam.objects.bulk_create(bulk)

    for histcomp in vlag_bk:
        histcomp.heeft_uitslag_bk = True
        histcomp.save(update_fields=['heeft_uitslag_bk'])
    # for

    print('[INFO] --> %s' % aantal)


# end of file
