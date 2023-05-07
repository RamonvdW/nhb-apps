# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from HistComp.definities import HISTCOMP_TYPE2URL, URL2HISTCOMP_TYPE, HISTCOMP_TYPE_18, HISTCOMP_TYPE
from HistComp.models import HistCompetitie, HistCompRegioIndiv
from HistComp.forms import FilterForm
from Plein.menu import menu_dynamics
from urllib.parse import quote_plus
from types import SimpleNamespace

TEMPLATE_HISTCOMP_ALLEJAREN = 'hist/histcomp_top.dtl'
TEMPLATE_HISTCOMP_INDIV = 'hist/histcomp_indiv.dtl'

RESULTS_PER_PAGE = 100

KLASSEN_VOLGORDE = ("Recurve", "Compound", "Barebow", "Instinctive bow", "Instinctive Bow", "Traditional", "Longbow")


def maak_filter_seizoen(context, seizoenen):
    """ Maak het seizoenen filter
        Vult in:
            context['filter_seizoenen']
    """
    seizoen = context['seizoen']
    histcomp_type_url = context['histcomp_type_url']

    context['filter_seizoenen'] = list()
    for opt in seizoenen:
        opt_url = opt.replace('/', '-')
        url = reverse('HistComp:seizoen-top', kwargs={'seizoen': opt_url, 'histcomp_type': histcomp_type_url})
        obj = SimpleNamespace(
            beschrijving='Seizoen %s' % opt,
            sel=opt_url,
            selected=(opt == seizoen),
            zoom_url=url)
        context['filter_seizoenen'].append(obj)
    # for


def maak_filter_histcomp_type(context, **kwargs):
    """ Maak het competitie type filter (Indoor / 25m1pijl)
        Vult in:
            context['filter_histcomp_type']
    """
    seizoen_url = context['seizoen_url']
    histcomp_type_url = context['histcomp_type_url']

    context['filter_histcomp_type'] = list()
    for opt_sel, opt_descr in HISTCOMP_TYPE:
        opt_url = HISTCOMP_TYPE2URL[opt_sel]
        url = reverse('HistComp:seizoen-top', kwargs={'seizoen': seizoen_url, 'histcomp_type': opt_url})
        obj = SimpleNamespace(
            beschrijving=opt_descr,
            sel=opt_sel,
            selected=(opt_url == histcomp_type_url),
            zoom_url=url)
        context['filter_histcomp_type'].append(obj)
    # for


class HistCompTop(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_ALLEJAREN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        seizoenen = list(HistCompetitie
                         .objects
                         .exclude(is_openbaar=False)
                         .order_by('-seizoen')
                         .distinct('seizoen')
                         .values_list('seizoen', flat=True))

        if len(seizoenen) == 0:
            # geen data beschikbaar
            context['titel'] = 'Uitslag eerder seizoen'
            context['geen_data'] = True
        else:
            seizoen = seizoenen[0]  # neem de nieuwste
            if 'seizoen' in kwargs:
                seizoen_url = kwargs['seizoen'][:10]  # 20xx-20yy
                seizoen = seizoen_url.replace('-', '/')
                if seizoen not in seizoenen:
                    seizoen = seizoenen[0]  # neem de nieuwste

            context['seizoen'] = seizoen
            context['seizoen_url'] = seizoen_url =seizoen.replace('/', '-')

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

            if seizoen == seizoenen[0]:
                context['titel'] = 'Uitslag vorig seizoen'
            else:
                context['titel'] = 'Uitslag eerder seizoen'

            default_boog = 'r'
            default_team = 'r'

            histcomp_indiv = HistCompetitie.objects.get(seizoen=seizoen, comp_type=histcomp_type, is_team=False, beschrijving__icontains='Recurve')

            context['url_regio_indiv'] = reverse('HistComp:uitslagen-regio-indiv',
                                                 kwargs={'seizoen': seizoen_url,
                                                         'histcomp_type': histcomp_type_url,
                                                         'comp_boog': default_boog})

            if histcomp_indiv.heeft_uitslag_rk:
                context['url_rayon_indiv'] = reverse('HistComp:uitslagen-rk-indiv',
                                                     kwargs={'seizoen': seizoen_url,
                                                             'histcomp_type': histcomp_type_url,
                                                             'comp_boog': default_boog})

            if histcomp_indiv.heeft_uitslag_bk:
                context['url_bond_indiv'] = reverse('HistComp:uitslagen-bk-indiv',
                                                    kwargs={'seizoen': seizoen_url,
                                                            'histcomp_type': histcomp_type_url,
                                                            'comp_boog': default_boog})

            try:
                histcomp_teams = HistCompetitie.objects.get(seizoen=seizoen, comp_type=histcomp_type, is_team=True, beschrijving__contains='Recurve')
            except HistCompetitie.DoesNotExist:
                pass
            else:
                context['url_regio_teams'] = reverse('HistComp:uitslagen-regio-teams',
                                                     kwargs={'seizoen': seizoen_url,
                                                             'histcomp_type': histcomp_type_url,
                                                             'team_type': default_team})

                if histcomp_teams.heeft_uitslag_rk:
                    context['url_rayon_teams'] = reverse('HistComp:uitslagen-rk-teams',
                                                         kwargs={'seizoen': seizoen_url,
                                                                 'histcomp_type': histcomp_type_url,
                                                                 'team_type': default_team})

                if histcomp_teams.heeft_uitslag_bk:
                    context['url_bond_teams'] = reverse('HistComp:uitslagen-bk-teams',
                                                        kwargs={'seizoen': seizoen_url,
                                                                'histcomp_type': histcomp_type_url,
                                                                'team_type': default_team})

        context['waarom'] = "Geen gegevens"

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Uitslag vorig seizoen')
        )

        menu_dynamics(self.request, context)
        return context


class HistCompIndivView(ListView):
    """ View to handle database queries, filtering, pagination en load-all button.
    """

    # class variables shared by all instances
    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_INDIV

    paginate_by = RESULTS_PER_PAGE  # enable Paginator built into ListView
    # ordering = ['rank']    # only works when pagination is active

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_count = 0
        self.base_url = ""
        self.form = FilterForm()
        self.get_filter = None
        self.comp_type = None
        self.klasse = None
        self.jaar = None
        self.histcomp = None

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # retourneer een QuerySet voor de template
        # onthoud zaken in de object instantie

        # haal de GET parameters uit de request
        self.form = FilterForm(self.request.GET)

        try:
            histcomp_pk = int(self.kwargs['histcomp_pk'][:6])       # afkappen voor de veiligheid
        except (ValueError, TypeError):
            # foute histcomp_pk
            raise Http404('Competitie niet gevonden')

        # zoek het HistCompetitie object erbij
        try:
            histcomp = HistCompetitie.objects.get(pk=histcomp_pk)
        except HistCompetitie.DoesNotExist:
            # foute histcomp_pk
            raise Http404('Competitie niet gevonden')

        self.histcomp = histcomp
        self.base_url = reverse('HistComp:indiv', kwargs={'histcomp_pk': histcomp.pk})

        if self.form.is_valid():
            self.get_filter = self.form.cleaned_data['filter']

            # disable pagination when all data is requested
            if self.form.cleaned_data['all']:
                self.paginate_by = 0

            if self.get_filter:
                try:
                    filter_nr = int(self.get_filter)
                    filter_is_nr = True
                except ValueError:
                    filter_is_nr = False

                if filter_is_nr:
                    if filter_nr < 100000:
                        return HistCompRegioIndiv.objects.filter(
                                            vereniging_nr__exact=filter_nr,
                                            histcompetitie=histcomp).order_by('rank')
                    else:
                        return HistCompRegioIndiv.objects.filter(
                                            sporter_lid_nr__exact=filter_nr,
                                            histcompetitie=histcomp).order_by('rank')
                else:
                    return HistCompRegioIndiv.objects.filter(
                                        Q(sporter_naam__icontains=self.get_filter) |
                                        Q(vereniging_naam__icontains=self.get_filter),
                                        histcompetitie=histcomp).order_by('rank')

        self.all_count = HistCompRegioIndiv.objects.filter(histcompetitie=histcomp).count()

        return HistCompRegioIndiv.objects.filter(histcompetitie=histcomp).order_by('rank')

    def _make_link_urls(self, context):
        # voorbereidingen voor een regel met volgende/vorige links
        # en rechtstreekse links naar een 10 pagina's
        links = list()

        base_url = self.base_url + '?'
        if self.get_filter:
            base_url += 'filter=%s' % quote_plus(self.get_filter)

        num_pages = context['paginator'].num_pages
        page_nr = context['page_obj'].number

        # previous
        if page_nr > 1:
            tup = ('vorige', base_url + '&page=%s' % (page_nr - 1))
            links.append(tup)
        else:
            tup = ('vorige_disable', '')
            links.append(tup)

        # block van 10 pagina's; huidige pagina in het midden
        range_start = page_nr - 5
        range_end = range_start + 9
        if range_start < 1:
            range_end += (1 - range_start)  # 1-0=1, 1--1=2, 1--2=3, etc.
            range_start = 1
        if range_end > num_pages:
            range_end = num_pages
        for pgnr in range(range_start, range_end+1):
            tup = ('%s' % pgnr, base_url + '&page=%s' % pgnr)
            links.append(tup)
        # for

        # next
        if page_nr < num_pages:
            tup = ('volgende', base_url + '&page=%s' % (page_nr + 1))
            links.append(tup)
        else:
            tup = ('volgende_disable', '')
            links.append(tup)

        return links

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self.histcomp.comp_type_str = COMP_TYPE_STR[self.histcomp.comp_type]
        context['histcomp'] = self.histcomp
        context['form'] = self.form
        context['filter_url'] = self.base_url
        context['zoekterm'] = self.get_filter

        if context['is_paginated']:
            context['page_links'] = self._make_link_urls(context)
            context['active'] = str(context['page_obj'].number)

        if self.get_filter:
            # als een filter actief is, toon de 'clear' knop
            context['unfiltered_url'] = self.base_url
        elif self.paginate_by > 0:
            # geen filter, wel paginering
            # toon de "laad alle ## records" knop
            context['all_url'] = self.base_url + '?all=1'
            context['all_count'] = self.all_count
        # else: we laten de 'all' lijst zien dus laat de 'all' knop weg

        for obj in context['object_list']:
            obj.sporter_lid_nr_str = str(obj.sporter_lid_nr)
        # for

        context['aantal_regels'] = 2 + len(context['object_list'])

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('HistComp:top'), 'Uitslag vorig seizoen'),
            (None, COMP_TYPE_STR[self.histcomp.comp_type]),
            (None, self.histcomp.beschrijving)
        )

        menu_dynamics(self.request, context)
        return context


# end of file
