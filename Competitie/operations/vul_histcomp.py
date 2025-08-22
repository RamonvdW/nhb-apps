# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Competitie.definities import DEEL_RK, DEEL_BK, KAMP_RANK_BLANCO, KAMP_RANK_ALLEEN_TEAM, DEELNAME_NEE
from Competitie.models import (Competitie, CompetitieIndivKlasse,
                               RegiocompetitieSporterBoog, RegiocompetitieRondeTeam,
                               KampioenschapSporterBoog, KampioenschapTeam)
from HistComp.definities import (HISTCOMP_RK, HISTCOMP_BK,
                                 HISTCOMP_TITEL_NONE, HISTCOMP_TITEL_RK, HISTCOMP_TITEL_BK, HISTCOMP_TITEL_NK)
from HistComp.models import (HistCompSeizoen,
                             HistCompRegioIndiv, HistCompRegioTeam,
                             HistKampIndivRK, HistKampIndivBK, HistKampTeam)


def _maak_seizoen_str(comp: Competitie):
    return "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)


def _get_seizoen(comp: Competitie):
    seizoen = _maak_seizoen_str(comp)

    try:
        hist_seizoen = HistCompSeizoen.objects.get(seizoen=seizoen, comp_type=comp.afstand)
    except HistCompSeizoen.DoesNotExist:        # pragma: no cover
        hist_seizoen = None

    return hist_seizoen


def uitslag_regio_indiv_naar_histcomp(comp: Competitie):
    """ uitslag regiocompetitie individueel overnemen als nieuwe histcomp """

    seizoen = _maak_seizoen_str(comp)

    # verwijder seizoen als deze al bestaat
    HistCompSeizoen.objects.filter(seizoen=seizoen,
                                   comp_type=comp.afstand).delete()

    bogen = ",".join(list(comp.boogtypen.order_by('volgorde').values_list('afkorting', flat=True)))

    teamtypen = list(comp.teamtypen.order_by('volgorde').values_list('afkorting', flat=True))
    # replace: R2->R and BB2->BB
    teamtypen = [teamtype.replace('2', '') for teamtype in teamtypen]
    teamtypen = ",".join(teamtypen)

    hist_seizoen = HistCompSeizoen(
                        seizoen=seizoen,
                        comp_type=comp.afstand,
                        is_openbaar=False,
                        indiv_bogen=bogen,
                        team_typen=teamtypen)

    if comp.is_indoor():
        hist_seizoen.aantal_beste_scores = settings.COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG
    else:
        hist_seizoen.aantal_beste_scores = settings.COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG

    hist_seizoen.save()

    bulk = list()
    for boogtype in comp.boogtypen.all():

        klassen_pks = (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=comp,
                               boogtype=boogtype)
                       .values_list('pk', flat=True))

        # begin met de sporters met genoeg scores (>= aantal_beste_scores)
        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'regiocompetitie__regio',
                                      'indiv_klasse')
                      .exclude(totaal=0)
                      .filter(regiocompetitie__competitie=comp,
                              indiv_klasse__in=klassen_pks,
                              aantal_scores__gte=hist_seizoen.aantal_beste_scores)
                      .order_by('-gemiddelde'))     # hoogste boven

        regio_klasse2rank = dict()      # [regio_nr, indiv_klasse.pk] = (rank, totaal)
        for deelnemer in deelnemers:
            regio_nr = deelnemer.regiocompetitie.regio.regio_nr
            tup = (regio_nr, deelnemer.indiv_klasse.pk)
            try:
                rank, prev_totaal = regio_klasse2rank[tup]
            except KeyError:
                rank, prev_totaal = 0, 0

            if deelnemer.totaal != prev_totaal:
                rank += 1
            regio_klasse2rank[tup] = (rank, deelnemer.totaal)

            sporter = deelnemer.sporterboog.sporter
            ver = deelnemer.bij_vereniging
            hist = HistCompRegioIndiv(
                        seizoen=hist_seizoen,
                        indiv_klasse=deelnemer.indiv_klasse.beschrijving,
                        rank=rank,
                        sporter_lid_nr=sporter.lid_nr,
                        sporter_naam=sporter.volledige_naam(),
                        boogtype=boogtype.afkorting,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        regio_nr=deelnemer.regiocompetitie.regio.regio_nr,
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
            if len(bulk) >= 500:            # pragma: no cover
                HistCompRegioIndiv.objects.bulk_create(bulk)
                bulk = list()
        # for

        # aanvullen met sporters die niet genoeg scores hebben (< aantal_beste_scores)
        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'regiocompetitie__regio',
                                      'indiv_klasse')
                      .exclude(totaal=0)
                      .filter(regiocompetitie__competitie=comp,
                              indiv_klasse__in=klassen_pks,
                              aantal_scores__lt=hist_seizoen.aantal_beste_scores)
                      .order_by('-gemiddelde'))     # hoogste boven

        for deelnemer in deelnemers:
            regio_nr = deelnemer.regiocompetitie.regio.regio_nr
            tup = (regio_nr, deelnemer.indiv_klasse.pk)
            try:
                rank, prev_totaal = regio_klasse2rank[tup]
            except KeyError:
                rank = 0
                prev_totaal = 0

            if deelnemer.totaal != prev_totaal:
                rank += 1
            regio_klasse2rank[tup] = (rank, deelnemer.totaal)

            sporter = deelnemer.sporterboog.sporter
            ver = deelnemer.bij_vereniging
            hist = HistCompRegioIndiv(
                        seizoen=hist_seizoen,
                        indiv_klasse=deelnemer.indiv_klasse.beschrijving,
                        rank=rank,
                        sporter_lid_nr=sporter.lid_nr,
                        sporter_naam=sporter.volledige_naam(),
                        boogtype=boogtype.afkorting,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        regio_nr=deelnemer.regiocompetitie.regio.regio_nr,
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
            if len(bulk) >= 500:            # pragma: no cover
                HistCompRegioIndiv.objects.bulk_create(bulk)
                bulk = list()
        # for

    # for

    if len(bulk):       # pragma: no branch
        HistCompRegioIndiv.objects.bulk_create(bulk)


def uitslag_rk_indiv_naar_histcomp(comp: Competitie):
    """ uitslag rk individueel overnemen als histcomp
        maak voor elke sporter een HistCompKampioenschapIndiv record aan
    """

    hist_seizoen = _get_seizoen(comp)
    if not hist_seizoen:
        return

    beschrijving2boogtype_pk = dict()
    for boogtype in comp.boogtypen.all():
        beschrijving2boogtype_pk[boogtype.beschrijving] = boogtype.pk
    # for

    bulk = list()
    for deelnemer in (KampioenschapSporterBoog
                      .objects
                      .filter(kampioenschap__competitie=comp,
                              kampioenschap__deel=DEEL_RK)
                      .prefetch_related('kampioenschapteam_feitelijke_leden')
                      .select_related('sporterboog__sporter',
                                      'sporterboog__boogtype',
                                      'kampioenschap__rayon',
                                      'bij_vereniging',
                                      'indiv_klasse')):

        # sporters met rank=0 toch opnemen ivm mogelijk koppeling aan team
        is_in_team = deelnemer.kampioenschapteam_feitelijke_leden.count() > 0

        if 0 < deelnemer.result_rank <= KAMP_RANK_BLANCO or is_in_team:
            kampioenschap = deelnemer.kampioenschap
            sporter = deelnemer.sporterboog.sporter
            boogtype = deelnemer.sporterboog.boogtype
            ver = deelnemer.bij_vereniging

            if deelnemer.deelname == DEELNAME_NEE:
                deelnemer.result_rank = KAMP_RANK_ALLEEN_TEAM

            titel_code = HISTCOMP_TITEL_NONE
            if deelnemer.result_rank == 1:
                titel_code = HISTCOMP_TITEL_RK

            hist = HistKampIndivRK(
                            seizoen=hist_seizoen,
                            indiv_klasse=deelnemer.indiv_klasse.beschrijving,
                            sporter_lid_nr=sporter.lid_nr,
                            sporter_naam=sporter.volledige_naam(),
                            boogtype=boogtype.afkorting,
                            vereniging_nr=ver.ver_nr,
                            vereniging_naam=ver.naam,
                            vereniging_plaats=ver.plaats,
                            rayon_nr=kampioenschap.rayon.rayon_nr,
                            rank_rk=deelnemer.result_rank,
                            titel_code_rk=titel_code,
                            rk_score_is_blanco=(deelnemer.result_rank == KAMP_RANK_BLANCO),
                            rk_score_1=deelnemer.result_score_1,
                            rk_score_2=deelnemer.result_score_2,
                            rk_score_totaal=deelnemer.result_score_1 + deelnemer.result_score_2,
                            rk_counts=deelnemer.result_counts)
            bulk.append(hist)
    # for

    HistKampIndivRK.objects.bulk_create(bulk)

    hist_seizoen.heeft_uitslag_rk_indiv = True
    hist_seizoen.save(update_fields=['heeft_uitslag_rk_indiv'])


def uitslag_bk_indiv_naar_histcomp(comp: Competitie):
    """ uitslag bk individueel overnemen als histcomp """

    hist_seizoen = _get_seizoen(comp)
    if not hist_seizoen:
        return

    bulk = list()
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
            boogtype = deelnemer.sporterboog.boogtype
            ver = deelnemer.bij_vereniging

            titel_code = HISTCOMP_TITEL_NONE
            if deelnemer.result_rank == 1:
                titel = deelnemer.indiv_klasse.titel_bk
                if titel == 'Bondskampioen':
                    titel_code = HISTCOMP_TITEL_BK
                elif titel == 'Nederlands Kampioen':
                    titel_code = HISTCOMP_TITEL_NK

            hist = HistKampIndivBK(
                    seizoen=hist_seizoen,
                    bk_indiv_klasse=deelnemer.indiv_klasse.beschrijving,
                    sporter_lid_nr=sporter.lid_nr,
                    sporter_naam=sporter.volledige_naam(),
                    boogtype=boogtype.afkorting,
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam=ver.naam,
                    vereniging_plaats=ver.plaats,
                    rank_bk=deelnemer.result_rank,
                    titel_code_bk=titel_code,
                    bk_score_1=deelnemer.result_score_1,
                    bk_score_2=deelnemer.result_score_2,
                    bk_score_totaal=deelnemer.result_score_1 + deelnemer.result_score_2,
                    bk_counts=deelnemer.result_counts)
            bulk.append(hist)
    # for

    HistKampIndivBK.objects.bulk_create(bulk)
    del bulk

    hist_seizoen.heeft_uitslag_bk_indiv = True
    hist_seizoen.save(update_fields=['heeft_uitslag_bk_indiv'])


def uitslag_regio_teams_naar_histcomp(comp: Competitie):
    """ uitslag regiocompetitie teams overnemen als histcomp """

    hist_seizoen = _get_seizoen(comp)
    if not hist_seizoen:
        return

    bulk = list()
    prev_team = None
    hist = None
    unsorted = list()
    for ronde in (RegiocompetitieRondeTeam
                  .objects
                  .filter(team__regiocompetitie__competitie=comp)
                  .select_related('team',
                                  'team__regiocompetitie',
                                  'team__regiocompetitie__regio')
                  .order_by('team__vereniging',
                            'team__volg_nr',
                            'ronde_nr')):

        if ronde.team != prev_team:
            if hist:
                if hist.totaal_score == 0:
                    # helemaal geen scores niet opnemen in de uitslag
                    bulk.remove(hist)
                else:
                    tup = (hist.regio_nr, hist.totaal_punten, hist.totaal_score, len(unsorted), hist)
                    unsorted.append(tup)

            team = ronde.team
            ver = team.vereniging

            team_type = team.team_klasse.team_afkorting
            team_type = team_type.replace('2', '')      # BB2->BB, R2->R2

            hist = HistCompRegioTeam(
                        seizoen=hist_seizoen,
                        team_klasse=team.team_klasse.beschrijving,
                        team_type=team_type,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        regio_nr=team.regiocompetitie.regio.regio_nr,
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

    # laatste team toevoegen
    if hist:
        if hist.totaal_score == 0:
            # helemaal geen scores niet opnemen in de uitslag
            bulk.remove(hist)
        else:
            tup = (hist.regio_nr, hist.totaal_punten, hist.totaal_score, len(unsorted), hist)
            unsorted.append(tup)

    klasse_regio2rank = dict()
    unsorted.sort(reverse=True)     # hoogste punten eerst
    for tup in unsorted:
        hist = tup[-1]
        tup = (hist.regio_nr, hist.team_klasse)
        try:
            rank = klasse_regio2rank[tup]
        except KeyError:
            rank = 0
        rank += 1
        hist.rank = rank
        klasse_regio2rank[tup] = rank
    # for

    HistCompRegioTeam.objects.bulk_create(bulk)

    hist_seizoen.heeft_uitslag_regio_teams = True
    hist_seizoen.save(update_fields=['heeft_uitslag_regio_teams'])


def uitslag_rk_teams_naar_histcomp(comp: Competitie):
    """ uitslag rk teams overnemen als histcomp """

    hist_seizoen = _get_seizoen(comp)
    if not hist_seizoen:
        return

    indiv_klasse_lid_nr2hist = dict()
    for hist in HistKampIndivRK.objects.filter(seizoen=hist_seizoen):
        tup = (hist.indiv_klasse, hist.sporter_lid_nr, hist.boogtype)
        indiv_klasse_lid_nr2hist[tup] = hist
    # for

    bulk = list()
    for team in (KampioenschapTeam
                 .objects
                 .filter(kampioenschap__competitie=comp,
                         kampioenschap__deel=DEEL_RK)
                 .select_related('team_klasse',
                                 'team_type',
                                 'vereniging',
                                 'kampioenschap',
                                 'kampioenschap__rayon')
                 .prefetch_related('feitelijke_leden')):

        if team.result_rank > 0:
            ver = team.vereniging

            team_type = team.team_klasse.team_afkorting
            team_type = team_type.replace('2', '')      # BB2->BB, R2->R2

            titel_code = HISTCOMP_TITEL_NONE
            if team.result_rank == 1:
                titel_code = HISTCOMP_TITEL_RK

            hist = HistKampTeam(
                        seizoen=hist_seizoen,
                        rk_of_bk=HISTCOMP_RK,
                        rayon_nr=team.kampioenschap.rayon.rayon_nr,
                        teams_klasse=team.team_klasse.beschrijving,
                        team_type=team_type,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        team_nr=team.volg_nr,
                        team_score=team.result_teamscore,
                        rank=team.result_rank,
                        titel_code=titel_code)

            unsorted = list()
            for team_lid in team.feitelijke_leden.select_related('indiv_klasse', 'sporterboog__sporter').all():

                s1 = team_lid.result_rk_teamscore_1
                s2 = team_lid.result_rk_teamscore_2

                lid_nr = team_lid.sporterboog.sporter.lid_nr
                boogtype = team_lid.sporterboog.boogtype.afkorting
                tup = (team_lid.indiv_klasse.beschrijving, lid_nr, boogtype)
                try:
                    hist_indiv = indiv_klasse_lid_nr2hist[tup]
                except KeyError:
                    # sporter heeft niet individueel meegedaan
                    # maak een lege sporter aan
                    hist_indiv = HistKampIndivRK(
                                    seizoen=hist_seizoen,
                                    indiv_klasse='',
                                    sporter_lid_nr=lid_nr,
                                    sporter_naam=team_lid.sporterboog.sporter.volledige_naam(),
                                    boogtype=boogtype,
                                    vereniging_nr=ver.ver_nr,
                                    vereniging_naam=ver.naam,
                                    vereniging_plaats=ver.plaats,
                                    rayon_nr=team.kampioenschap.rayon.rayon_nr,
                                    rank_rk=0)
                    hist_indiv.save()

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
    # for

    HistKampTeam.objects.bulk_create(bulk)

    hist_seizoen.heeft_uitslag_rk_teams = True
    hist_seizoen.save(update_fields=['heeft_uitslag_rk_teams'])


def uitslag_bk_teams_naar_histcomp(comp: Competitie):
    """ uitslag bk teams overnemen als histcomp """

    hist_seizoen = _get_seizoen(comp)
    if not hist_seizoen:
        return

    indiv_klasse_lid_nr2hist = dict()
    for hist in HistKampIndivRK.objects.filter(seizoen=hist_seizoen):
        tup = (hist.indiv_klasse, hist.sporter_lid_nr, hist.boogtype)
        indiv_klasse_lid_nr2hist[tup] = hist
    # for

    bulk = list()
    for team in (KampioenschapTeam
                 .objects
                 .filter(kampioenschap__competitie=comp,
                         kampioenschap__deel=DEEL_BK)
                 .select_related('team_klasse',
                                 'team_type',
                                 'vereniging')
                 .prefetch_related('feitelijke_leden')):

        if team.result_rank > 0:
            ver = team.vereniging

            team_type = team.team_klasse.team_afkorting
            team_type = team_type.replace('2', '')      # BB2->BB, R2->R2

            titel_code = HISTCOMP_TITEL_NONE
            if team.result_rank == 1:
                titel = team.team_klasse.titel_bk
                if titel == 'Bondskampioen':
                    titel_code = HISTCOMP_TITEL_BK
                elif titel == 'Nederlands Kampioen':
                    titel_code = HISTCOMP_TITEL_NK

            hist = HistKampTeam(
                        seizoen=hist_seizoen,
                        rk_of_bk=HISTCOMP_BK,
                        teams_klasse=team.team_klasse.beschrijving,
                        team_type=team_type,
                        vereniging_nr=ver.ver_nr,
                        vereniging_naam=ver.naam,
                        vereniging_plaats=ver.plaats,
                        team_nr=team.volg_nr,
                        team_score=team.result_teamscore,
                        team_score_counts=team.result_counts,
                        rank=team.result_rank,
                        titel_code=titel_code)

            unsorted = list()
            for team_lid in team.feitelijke_leden.select_related('indiv_klasse',
                                                                 'sporterboog__sporter',
                                                                 'sporterboog__boogtype').all():
                s1 = team_lid.result_bk_teamscore_1
                s2 = team_lid.result_bk_teamscore_2

                sporter = team_lid.sporterboog.sporter
                lid_nr = sporter.lid_nr
                boogtype = team_lid.sporterboog.boogtype.afkorting
                tup = (team_lid.indiv_klasse.beschrijving, lid_nr, boogtype)
                try:
                    hist_indiv = indiv_klasse_lid_nr2hist[tup]
                except KeyError:
                    hist_indiv = None

                if not hist_indiv:
                    tup = ('', lid_nr)      # indien sporter niet individueel meegedaan heeft
                    try:
                        hist_indiv = indiv_klasse_lid_nr2hist[tup]
                    except KeyError:
                        hist_indiv = None

                if not hist_indiv:
                    # aanmaken
                    ver = team_lid.bij_vereniging
                    hist_indiv = HistKampIndivRK(
                                    seizoen=hist_seizoen,
                                    indiv_klasse='',
                                    sporter_lid_nr=lid_nr,
                                    sporter_naam=sporter.volledige_naam(),
                                    boogtype=boogtype,
                                    vereniging_nr=ver.ver_nr,
                                    vereniging_naam=ver.naam,
                                    vereniging_plaats=ver.plaats,
                                    rayon_nr=ver.regio.rayon_nr,
                                    rank_rk=0)
                    hist_indiv.save()
                    indiv_klasse_lid_nr2hist[tup] = hist_indiv

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
    # for

    HistKampTeam.objects.bulk_create(bulk)

    hist_seizoen.heeft_uitslag_bk_teams = True
    hist_seizoen.save(update_fields=['heeft_uitslag_bk_teams'])


# end of file
