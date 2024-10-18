# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from HistComp.definities import (HISTCOMP_TYPE, HISTCOMP_TYPE_18,
                                 HISTCOMP_TYPE2URL, URL2HISTCOMP_TYPE,
                                 HIST_BOOG2URL, HIST_BOOG_DEFAULT,
                                 HIST_TEAM2URL, HIST_TEAM_DEFAULT)
from HistComp.models import HistCompSeizoen
from types import SimpleNamespace

TEMPLATE_HISTCOMP_TOP = 'histcomp/uitslagen-top.dtl'


def maak_filter_seizoen(context, seizoenen):
    """ Maak het seizoenen filter
        Vult in:
            context['filter_seizoenen']
    """
    seizoen = context['seizoen']

    context['filter_seizoenen'] = list()
    for opt in seizoenen:
        opt_url = opt.replace('/', '-')
        obj = SimpleNamespace(
                    beschrijving='Seizoen %s' % opt,
                    sel=opt_url,
                    selected=(opt == seizoen),
                    url_part=opt_url)
        context['filter_seizoenen'].append(obj)
    # for


def maak_filter_histcomp_type(context):
    """ Maak het competitie type filter (Indoor / 25m1pijl)
        Vult in:
            context['filter_histcomp_type']
    """
    histcomp_type_url = context['histcomp_type_url']

    context['filter_histcomp_type'] = list()
    for opt_sel, opt_descr in HISTCOMP_TYPE:
        opt_url = HISTCOMP_TYPE2URL[opt_sel]
        obj = SimpleNamespace(
                    beschrijving=opt_descr,
                    sel=opt_sel,
                    selected=(opt_url == histcomp_type_url),
                    url_part=opt_url)
        context['filter_histcomp_type'].append(obj)
    # for


class HistCompTop(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_TOP

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # maak een lijst met seizoen labels, zoals ['2020/2021', '2021/2022']
        seizoenen = list(HistCompSeizoen
                         .objects
                         .exclude(is_openbaar=False)
                         .order_by('-seizoen')
                         .distinct('seizoen')
                         .values_list('seizoen', flat=True))

        if len(seizoenen) == 0:
            # geen data beschikbaar
            context['geen_data'] = True
        else:
            seizoen = seizoenen[0]  # neem de nieuwste
            if 'seizoen' in kwargs:
                seizoen_url = kwargs['seizoen'][:10]  # 20xx-20yy
                seizoen = seizoen_url.replace('-', '/')
                if seizoen not in seizoenen:
                    seizoen = seizoenen[0]  # neem de nieuwste

            context['seizoen'] = seizoen                                        # '2020/2021'
            context['seizoen_url'] = seizoen_url = seizoen.replace('/', '-')    # '2020-2021'

            histcomp_type = HISTCOMP_TYPE_18
            if 'histcomp_type' in kwargs:
                histcomp_type_url = kwargs['histcomp_type'][:10]  # indoor of 25m1pijl
                try:
                    histcomp_type = URL2HISTCOMP_TYPE[histcomp_type_url]
                except KeyError:
                    histcomp_type = HISTCOMP_TYPE_18

            context['histcomp_type'] = histcomp_type
            context['histcomp_type_url'] = histcomp_type_url = HISTCOMP_TYPE2URL[histcomp_type]

            maak_filter_seizoen(context, seizoenen)
            maak_filter_histcomp_type(context)

            context['url_filters'] = reverse('HistComp:seizoen-top',
                                             kwargs={'seizoen': '~1',
                                                     'histcomp_type': '~2'})

            default_boog_url = HIST_BOOG2URL[HIST_BOOG_DEFAULT]
            default_team_url = HIST_TEAM2URL[HIST_TEAM_DEFAULT]

            hist_seizoen = HistCompSeizoen.objects.get(seizoen=seizoen, comp_type=histcomp_type)

            context['url_regio_indiv'] = reverse('HistComp:uitslagen-regio-indiv',
                                                 kwargs={'seizoen': seizoen_url,
                                                         'histcomp_type': histcomp_type_url,
                                                         'boog_type': default_boog_url})

            if hist_seizoen.heeft_uitslag_rk_indiv:
                context['url_rayon_indiv'] = reverse('HistComp:uitslagen-rk-indiv',
                                                     kwargs={'seizoen': seizoen_url,
                                                             'histcomp_type': histcomp_type_url,
                                                             'boog_type': default_boog_url})

            if hist_seizoen.heeft_uitslag_bk_indiv:
                context['url_bond_indiv'] = reverse('HistComp:uitslagen-bk-indiv',
                                                    kwargs={'seizoen': seizoen_url,
                                                            'histcomp_type': histcomp_type_url,
                                                            'boog_type': default_boog_url})

            if hist_seizoen.heeft_uitslag_regio_teams:
                context['url_regio_teams'] = reverse('HistComp:uitslagen-regio-teams',
                                                     kwargs={'seizoen': seizoen_url,
                                                             'histcomp_type': histcomp_type_url,
                                                             'team_type': default_team_url})

            if hist_seizoen.heeft_uitslag_rk_teams:
                context['url_rayon_teams'] = reverse('HistComp:uitslagen-rk-teams',
                                                     kwargs={'seizoen': seizoen_url,
                                                             'histcomp_type': histcomp_type_url,
                                                             'team_type': default_team_url})

            if hist_seizoen.heeft_uitslag_bk_teams:
                context['url_bond_teams'] = reverse('HistComp:uitslagen-bk-teams',
                                                    kwargs={'seizoen': seizoen_url,
                                                            'histcomp_type': histcomp_type_url,
                                                            'team_type': default_team_url})

        context['waarom'] = "Geen gegevens"

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Uitslag vorig seizoen')
        )

        return context


# end of file
