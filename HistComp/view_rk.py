# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Geo.models import Rayon
from HistComp.definities import (HISTCOMP_RK, HISTCOMP_TYPE_18,
                                 HISTCOMP_TYPE2URL, URL2HISTCOMP_TYPE, HISTCOMP_TYPE2STR,
                                 HIST_BOOG_DEFAULT, HIST_BOOG2URL, URL2HIST_BOOG, HIST_BOOG2STR,
                                 HIST_TEAM_DEFAULT, HIST_TEAM2URL, URL2HIST_TEAM, HIST_TEAM2STR,
                                 HIST_KLASSE2VOLGORDE, HISTCOMP_TITEL2STR)
from HistComp.models import HistCompSeizoen, HistKampIndivRK, HistKampTeam
from Sporter.operations import get_request_rayon_nr
from types import SimpleNamespace


TEMPLATE_HISTCOMP_RK_INDIV = 'histcomp/uitslagen-rk-indiv.dtl'
TEMPLATE_HISTCOMP_RK_TEAMS = 'histcomp/uitslagen-rk-teams.dtl'


def maak_filter_rayon_nr(context):
    """ filter opties voor het rayon nummer """

    gekozen_rayon_nr = context['rayon_nr']

    rayons = (Rayon
              .objects
              .order_by('rayon_nr'))

    context['rayon_filters'] = rayons
    for rayon in rayons:
        rayon.sel = 'rayon_%s' % rayon.rayon_nr
        rayon.opt_text = 'Rayon %s' % rayon.rayon_nr
        if rayon.rayon_nr == gekozen_rayon_nr:
            context['rayon'] = rayon
            rayon.selected = True

        rayon.url_part = str(rayon.rayon_nr)
    # for


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


class HistRkIndivView(TemplateView):

    """ Django class-based view voor de individuele uitslagen van de regiocompetitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_RK_INDIV

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

        # optioneel: rayon nummer
        try:
            rayon_nr = kwargs['rayon_nr'][:3]    # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except (KeyError, TypeError, IndexError):
            rayon_nr = 0

        if not (1 <= rayon_nr <= 4):
            # kies automatisch een regio nummer aan de hand van de vereniging van de sporter of de gekozen rol
            rayon_nr = get_request_rayon_nr(self.request)

        context['rayon_nr'] = rayon_nr
        context['rayon'] = None         # wordt ingevuld door maak_filter_rayon

        # maak_filter_seizoen(context, seizoenen)
        # maak_filter_histcomp_type(context)
        maak_filter_boog_type(context, hist_seizoen)
        maak_filter_rayon_nr(context)

        context['url_filters'] = reverse('HistComp:uitslagen-rk-indiv-n',
                                         kwargs={'seizoen': seizoen_url,
                                                 'histcomp_type': histcomp_type_url,
                                                 'boog_type': '~1',
                                                 'rayon_nr': '~2'})
        # voor de header
        context['comp_beschrijving'] = '%s seizoen %s' % (HISTCOMP_TYPE2STR[histcomp_type], seizoen_str)
        context['boog_beschrijving'] = HIST_BOOG2STR[boog_type]

        uitslag = (HistKampIndivRK
                   .objects
                   .filter(seizoen=hist_seizoen,
                           rayon_nr=rayon_nr,
                           boogtype=boog_type,
                           rank_rk__lte=100)
                   .exclude(rank_rk=0)                  # 0 = niet meegedaan
                   .order_by('indiv_klasse',
                             'rank_rk',                 # laagste eerst
                             '-rk_score_totaal'))       # hoogste eerst

        teller = None
        subset = list()
        volgorde = 0
        unsorted = list()
        prev_klasse = None
        for indiv in uitslag:
            if prev_klasse != indiv.indiv_klasse:
                if len(subset) > 0:
                    teller.aantal_in_groep = len(subset) + 2
                    tup = (volgorde, subset[0].pk, subset)
                    unsorted.append(tup)
                    subset = list()

                indiv.break_klasse = True
                teller = indiv

                volgorde = HIST_KLASSE2VOLGORDE[indiv.indiv_klasse]
                prev_klasse = indiv.indiv_klasse

            indiv.naam_str = '[%s] %s' % (indiv.sporter_lid_nr, indiv.sporter_naam)

            indiv.ver_str = "[%s] %s" % (indiv.vereniging_nr, indiv.vereniging_naam)
            if indiv.vereniging_plaats:
                indiv.ver_str += ' (%s)' % indiv.vereniging_plaats

            if indiv.rk_score_is_blanco:
                indiv.scores_str_1 = '-'
                indiv.scores_str_2 = '(blanco)'
                indiv.rank_rk = ''

            else:
                indiv.scores_str_1 = "%s (%s+%s)" % (indiv.rk_score_totaal,
                                                     indiv.rk_score_1,
                                                     indiv.rk_score_2)
                indiv.scores_str_2 = indiv.rk_counts

            indiv.titel = HISTCOMP_TITEL2STR[indiv.titel_code_rk]

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

        context['canonical'] = reverse('HistComp:uitslagen-rk-indiv-n',
                                       kwargs={'seizoen': seizoen_url,
                                               'histcomp_type': histcomp_type_url,
                                               'boog_type': boog_type_url,
                                               'rayon_nr': rayon_nr})

        url_top = reverse('HistComp:seizoen-top', kwargs={'seizoen': seizoen_url, 'histcomp_type': histcomp_type_url})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (url_top, 'Uitslag vorig seizoen'),
            (None, 'Uitslagen RK individueel')
        )

        return context


class HistRkTeamsView(TemplateView):

    """ Django class-based view voor de individuele uitslagen van de regiocompetitie in 1 regio """

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_RK_TEAMS

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

        # optioneel: rayon nummer
        try:
            rayon_nr = kwargs['rayon_nr'][:3]    # afkappen voor de veiligheid
            rayon_nr = int(rayon_nr)
        except (KeyError, TypeError, IndexError):
            rayon_nr = 0

        if not (1 <= rayon_nr <= 4):
            # kies automatisch een regio nummer aan de hand van de vereniging van de sporter of de gekozen rol
            rayon_nr = get_request_rayon_nr(self.request)

        context['rayon_nr'] = rayon_nr
        context['rayon'] = None         # wordt ingevuld door maak_filter_rayon

        # maak_filter_seizoen(context, seizoenen)
        # maak_filter_histcomp_type(context)
        maak_filter_team_type(context, hist_seizoen)
        maak_filter_rayon_nr(context)

        context['url_filters'] = reverse('HistComp:uitslagen-rk-teams-n',
                                         kwargs={'seizoen': seizoen_url,
                                                 'histcomp_type': histcomp_type_url,
                                                 'team_type': '~1',
                                                 'rayon_nr': '~2'})

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
                             rk_of_bk=HISTCOMP_RK,
                             team_type=team_type,
                             rayon_nr=rayon_nr)
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

        context['canonical'] = reverse('HistComp:uitslagen-rk-teams-n',
                                       kwargs={'seizoen': seizoen_url,
                                               'histcomp_type': histcomp_type_url,
                                               'team_type': team_type_url,
                                               'rayon_nr': rayon_nr})

        url_top = reverse('HistComp:seizoen-top', kwargs={'seizoen': seizoen_url, 'histcomp_type': histcomp_type_url})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (url_top, 'Uitslag vorig seizoen'),
            (None, 'Uitslagen RK teams')
        )

        return context

# end of file
