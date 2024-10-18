# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from HistComp.definities import (HISTCOMP_BK, HISTCOMP_TYPE_18,
                                 HISTCOMP_TYPE2URL, URL2HISTCOMP_TYPE, HISTCOMP_TYPE2STR,
                                 HIST_BOOG_DEFAULT, HIST_BOOG2URL, URL2HIST_BOOG, HIST_BOOG2STR,
                                 HIST_TEAM_DEFAULT, HIST_TEAM2URL, URL2HIST_TEAM, HIST_TEAM2STR,
                                 HIST_KLASSE2VOLGORDE, HISTCOMP_TITEL2STR)
from HistComp.models import HistCompSeizoen, HistKampIndivBK, HistKampTeam
from types import SimpleNamespace


TEMPLATE_HISTCOMP_BK_INDIV = 'histcomp/uitslagen-bk-indiv.dtl'
TEMPLATE_HISTCOMP_BK_TEAMS = 'histcomp/uitslagen-bk-teams.dtl'


def maak_filter_boog_type(context, hist_seizoen):
    """ filter opties voor de bogen """

    gekozen_boog_type = context['boog_type']
    context['boog_filters'] = list()

    if hist_seizoen.indiv_bogen:
        afkortingen = hist_seizoen.indiv_bogen.split(',')
        for afkorting in afkortingen:
            opt = SimpleNamespace(
                    opt_text=HIST_BOOG2STR[afkorting],
                    sel='boog_' + afkorting,
                    selected=(afkorting == gekozen_boog_type),
                    url_part=HIST_BOOG2URL[afkorting])
            context['boog_filters'].append(opt)
        # for


def maak_filter_team_type(context, hist_seizoen):
    """ filter opties voor de team typen """

    gekozen_team_type = context['team_type']
    context['teamtype_filters'] = list()

    if hist_seizoen.team_typen:
        afkortingen = hist_seizoen.team_typen.split(',')
        for afkorting in afkortingen:
            opt = SimpleNamespace(
                    opt_text=HIST_TEAM2STR[afkorting],
                    sel='team_' + afkorting,
                    selected=(afkorting == gekozen_team_type),
                    url_part=HIST_TEAM2URL[afkorting])
            context['teamtype_filters'].append(opt)
        # for


class HistBkIndivView(TemplateView):

    """ Django class-based view voor de individuele uitslagen van de regiocompetitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_BK_INDIV

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        seizoenen = list(HistCompSeizoen
                         .objects
                         .exclude(is_openbaar=False)
                         .order_by('-seizoen')
                         .distinct('seizoen')
                         .values_list('seizoen', flat=True))

        if len(seizoenen) == 0:
            raise Http404('Geen data')

        # verplicht: seizoen
        seizoen_url = kwargs['seizoen'][:10]  # 20xx-20yy
        seizoen_str = seizoen_url.replace('-', '/')
        if seizoen_str not in seizoenen:
            seizoen_str = seizoenen[0]  # neem de nieuwste

        seizoen_url = seizoen_str.replace('/', '-')  # '2020-2021'
        context['seizoen'] = seizoen_str             # '2020/2021'
        context['seizoen_url'] = seizoen_url

        # verplicht: histcomp_type
        histcomp_type_url = kwargs['histcomp_type'][:10]  # indoor of 25m1pijl
        try:
            histcomp_type = URL2HISTCOMP_TYPE[histcomp_type_url]
        except KeyError:
            histcomp_type = HISTCOMP_TYPE_18

        context['histcomp_type'] = histcomp_type
        context['histcomp_type_url'] = histcomp_type_url = HISTCOMP_TYPE2URL[histcomp_type]

        hist_seizoen = HistCompSeizoen.objects.get(seizoen=seizoen_str, comp_type=histcomp_type)

        # verplicht: boog_type
        try:
            boog_type_url = kwargs['boog_type'][:20]     # afkappen voor de veiligheid
            boog_type = URL2HIST_BOOG[boog_type_url]
        except KeyError:
            boog_type = '?'

        if boog_type not in hist_seizoen.indiv_bogen:
            boog_type = HIST_BOOG_DEFAULT

        context['boog_type'] = boog_type        # 'R', etc.
        context['boog_type_url'] = boog_type_url = HIST_BOOG2URL[boog_type]

        # maak_filter_seizoen(context, seizoenen)
        # maak_filter_histcomp_type(context)
        maak_filter_boog_type(context, hist_seizoen)

        context['url_filters'] = reverse('HistComp:uitslagen-bk-indiv',
                                         kwargs={'seizoen': seizoen_url,
                                                 'histcomp_type': histcomp_type_url,
                                                 'boog_type': '~1'})

        # voor de header
        context['comp_beschrijving'] = '%s seizoen %s' % (HISTCOMP_TYPE2STR[histcomp_type], seizoen_str)
        context['boog_beschrijving'] = HIST_BOOG2STR[boog_type]

        uitslag = (HistKampIndivBK
                   .objects
                   .exclude(rank_bk=0)                  # 0 = niet meegedaan
                   .filter(seizoen=hist_seizoen,
                           boogtype=boog_type,
                           rank_bk__lte=100)
                   .order_by('bk_indiv_klasse',
                             'rank_bk',                 # laagste eerst
                             '-bk_score_totaal'))       # hoogste eerst

        teller = None
        subset = list()
        volgorde = 0
        unsorted = list()
        prev_klasse = None
        for indiv in uitslag:
            if prev_klasse != indiv.bk_indiv_klasse:
                if len(subset) > 0:
                    teller.aantal_in_groep = len(subset) + 2
                    tup = (volgorde, subset[0].pk, subset)
                    unsorted.append(tup)
                    subset = list()

                indiv.break_klasse = True
                teller = indiv

                volgorde = HIST_KLASSE2VOLGORDE[indiv.bk_indiv_klasse]
                prev_klasse = indiv.bk_indiv_klasse

            indiv.naam_str = '[%s] %s' % (indiv.sporter_lid_nr, indiv.sporter_naam)

            indiv.ver_str = "[%s] %s" % (indiv.vereniging_nr, indiv.vereniging_naam)
            if indiv.vereniging_plaats:
                indiv.ver_str += ' (%s)' % indiv.vereniging_plaats

            indiv.scores_str_1 = "%s (%s+%s)" % (indiv.bk_score_totaal,
                                                 indiv.bk_score_1,
                                                 indiv.bk_score_2)
            indiv.scores_str_2 = indiv.bk_counts

            indiv.titel = HISTCOMP_TITEL2STR[indiv.titel_code_bk]

            subset.append(indiv)
        # for

        if len(subset) > 0:
            teller.aantal_in_groep = len(subset) + 2
            tup = (volgorde, subset[0].pk, subset)
            unsorted.append(tup)

        unsorted.sort()
        context['uitslag'] = uitslag = list()
        for _, _, subset in unsorted:
            uitslag.extend(subset)
        # for

        if len(uitslag) > 0:
            indiv = uitslag[0]
            indiv.is_eerste_groep = True

        context['heeft_deelnemers'] = len(uitslag) > 0

        context['canonical'] = reverse('HistComp:uitslagen-bk-indiv',       # TODO: keep?
                                       kwargs={'seizoen': seizoen_url,
                                               'histcomp_type': histcomp_type_url,
                                               'boog_type': boog_type_url})

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        url_top = reverse('HistComp:seizoen-top', kwargs={'seizoen': seizoen_url, 'histcomp_type': histcomp_type_url})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (url_top, 'Uitslag vorig seizoen'),
            (None, 'Uitslagen BK individueel')
        )

        return context


class HistBkTeamsView(TemplateView):

    """ Django class-based view voor de individuele uitslagen van de regiocompetitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_BK_TEAMS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        seizoenen = list(HistCompSeizoen
                         .objects
                         .exclude(is_openbaar=False)
                         .order_by('-seizoen')
                         .distinct('seizoen')
                         .values_list('seizoen', flat=True))

        if len(seizoenen) == 0:
            raise Http404('Geen data')

        # verplicht: seizoen
        seizoen_url = kwargs['seizoen'][:10]  # 20xx-20yy
        seizoen_str = seizoen_url.replace('-', '/')
        if seizoen_str not in seizoenen:
            seizoen_str = seizoenen[0]  # neem de nieuwste

        seizoen_url = seizoen_str.replace('/', '-')  # '2020-2021'
        context['seizoen'] = seizoen_str             # '2020/2021'
        context['seizoen_url'] = seizoen_url

        # verplicht: histcomp_type
        histcomp_type_url = kwargs['histcomp_type'][:10]  # indoor of 25m1pijl
        try:
            histcomp_type = URL2HISTCOMP_TYPE[histcomp_type_url]
        except KeyError:
            histcomp_type = HISTCOMP_TYPE_18

        context['histcomp_type'] = histcomp_type
        context['histcomp_type_url'] = histcomp_type_url = HISTCOMP_TYPE2URL[histcomp_type]

        hist_seizoen = HistCompSeizoen.objects.get(seizoen=seizoen_str, comp_type=histcomp_type)

        # verplicht: team_type
        try:
            team_type_url = kwargs['team_type'][:20]     # afkappen voor de veiligheid
            team_type = URL2HIST_TEAM[team_type_url]
        except KeyError:
            team_type = '?'

        if team_type not in hist_seizoen.team_typen:
            team_type = HIST_TEAM_DEFAULT

        context['team_type'] = team_type        # 'R', etc.
        context['team_type_url'] = team_type_url = HIST_TEAM2URL[team_type]

        # maak_filter_seizoen(context, seizoenen)
        # maak_filter_histcomp_type(context)
        maak_filter_team_type(context, hist_seizoen)

        context['url_filters'] = reverse('HistComp:uitslagen-bk-teams',
                                         kwargs={'seizoen': seizoen_url,
                                                 'histcomp_type': histcomp_type_url,
                                                 'team_type': '~1'})

        # voor de header
        context['comp_beschrijving'] = '%s seizoen %s' % (HISTCOMP_TYPE2STR[histcomp_type], seizoen_str)
        context['team_beschrijving'] = HIST_TEAM2STR[team_type]

        teller = None
        subset = list()
        volgorde = 0
        unsorted = list()
        prev_klasse = None
        for team in (HistKampTeam
                     .objects
                     .filter(seizoen=hist_seizoen,
                             rk_of_bk=HISTCOMP_BK,
                             team_type=team_type)
                     .select_related('lid_1', 'lid_2', 'lid_3', 'lid_4')
                     .order_by('teams_klasse',
                               'rank')):            # laagste eerst

            if team.teams_klasse != prev_klasse:
                if len(subset) > 0:
                    teller.aantal_in_groep = len(subset) + 2
                    tup = (volgorde, subset[0].pk, subset)
                    unsorted.append(tup)
                    subset = list()

                team.break_klasse = True
                teller = team

                volgorde = HIST_KLASSE2VOLGORDE[team.teams_klasse]
                prev_klasse = team.teams_klasse

            team.ver_str = '[%s] %s' % (team.vereniging_nr, team.vereniging_naam)
            if team.vereniging_plaats:
                team.ver_str += ' (%s)' % team.vereniging_plaats

            team.deelnemers = [team.lid_1, team.lid_2, team.lid_3, team.lid_4]
            deelnemer_scores = [team.score_lid_1, team.score_lid_2, team.score_lid_3, team.score_lid_4]
            for lid in team.deelnemers:
                if lid:
                    lid.naam_str = '[%s] %s' % (lid.sporter_lid_nr, lid.sporter_naam)
                    lid.team_score = deelnemer_scores.pop(0)
            # for

            # verwijder lege posities
            team.deelnemers = [lid for lid in team.deelnemers if lid]

            # sorteer aflopen op prestatie
            team.deelnemers.sort(key=lambda x: x.team_score, reverse=True)  # hoogste score eerst

            team.titel = HISTCOMP_TITEL2STR[team.titel_code]

            subset.append(team)
        # for

        if len(subset) > 0:
            teller.aantal_in_groep = len(subset) + 2
            tup = (volgorde, subset[0].pk, subset)
            unsorted.append(tup)

        unsorted.sort()
        context['uitslag'] = uitslag = list()
        for _, _, subset in unsorted:
            uitslag.extend(subset)
        # for

        if len(uitslag) > 0:
            team = uitslag[0]
            team.is_eerste_groep = True

        context['heeft_teams'] = len(uitslag) > 0

        context['canonical'] = reverse('HistComp:uitslagen-bk-teams',       # TODO: keep?
                                       kwargs={'seizoen': seizoen_url,
                                               'histcomp_type': histcomp_type_url,
                                               'team_type': team_type_url})

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        url_top = reverse('HistComp:seizoen-top', kwargs={'seizoen': seizoen_url, 'histcomp_type': histcomp_type_url})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (url_top, 'Uitslag vorig seizoen'),
            (None, 'Uitslagen BK teams')
        )

        return context


# end of file
