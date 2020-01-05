# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# from django.shortcuts import render
from django.urls import Resolver404, reverse
from django.views.generic import ListView
from django.db.models import Q
from .models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam
from .forms import FilterForm
from Plein.menu import menu_dynamics

TEMPLATE_HISTCOMP_ALLEJAREN = 'hist/histcomp_allejaren.dtl'
TEMPLATE_HISTCOMP_INDIV = 'hist/histcomp_indiv.dtl'
TEMPLATE_HISTCOMP_TEAM = 'hist/histcomp_team.dtl'

RESULTS_PER_PAGE = 100


class HistCompAlleJarenView(ListView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_ALLEJAREN
    queryset = HistCompetitie.objects.all()

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context)#, 'histcomp')
        return context


class HistCompBaseView(ListView):
    """ Base view to handle database queries, filtering, pagination,
        en load-all button.

        Mandatory class variables to set:
            reverse_name: HistComp:indiv or HistComp:team
            is_team: True or False
            query_class: HistCompetitieIndividueel or HistCompetitieTeam
    """

    # class variables shared by all instances
    is_team = None          # override in child class
    reverse_name = None     # override in child class
    query_class = None      # override in child class
    paginate_by = 100       # enable Paginator built into ListView
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

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # retourneer een QuerySet voor de template
        # onthoud zaken in de object instantie

        # haal de GET parameters uit de request
        self.form = FilterForm(self.request.GET)
        self.jaar = self.kwargs['jaar']
        self.comp_type = self.kwargs['comp_type']
        self.klasse = self.kwargs['klasse']

        self.base_url = reverse(self.reverse_name,
                                kwargs={
                                    'jaar': self.jaar,
                                    'comp_type': self.comp_type,
                                    'klasse': self.klasse})

        # vind het HistCompetitie object
        objs = HistCompetitie.objects.filter(
                                    jaar=self.jaar,
                                    comp_type=self.comp_type,
                                    klasse=self.klasse,
                                    is_team=self.is_team)
        if len(objs) < 1:
            return list()       # return empty iterable
        histcompetitie = objs[0]

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

                if self.is_team:
                    if filter_is_nr:
                        return self.query_class.objects.filter(
                            vereniging_nr__exact=self.get_filter,
                            histcompetitie=histcompetitie).order_by('subklasse', 'rank')
                    else:
                        return self.query_class.objects.filter(
                            vereniging_naam__icontains=self.get_filter,
                            histcompetitie=histcompetitie).order_by('subklasse', 'rank')
                else:
                    if filter_is_nr:
                        return self.query_class.objects.filter(
                                            Q(schutter_nr__exact=self.get_filter) |
                                            Q(vereniging_nr__exact=self.get_filter),
                                            histcompetitie=histcompetitie).order_by('subklasse', 'rank')
                    else:
                        return self.query_class.objects.filter(
                                            Q(schutter_naam__icontains=self.get_filter) |
                                            Q(vereniging_naam__icontains=self.get_filter),
                                            histcompetitie=histcompetitie).order_by('subklasse', 'rank')

        self.all_count = self.query_class.objects.filter(
                                histcompetitie=histcompetitie).count()

        return self.query_class.objects.filter(
                                histcompetitie=histcompetitie).order_by('subklasse', 'rank')

    def _make_link_urls(self, context):
        # voorbereidingen voor een regel met volgende/vorige links
        # en rechtstreekse links naar een 10 pagina's
        links = list()

        base_url = self.base_url + '?'
        if self.get_filter:
            base_url += 'filter=%s' % self.get_filter

        num_pages = context['paginator'].num_pages
        page_nr = context['page_obj'].number

        # previous
        if page_nr > 1:
            tup = ('vorige', base_url + '&page=%s' % (page_nr - 1))
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

        return links

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['comp_type'] = self.comp_type
        try:
            context['comp_type_str'] = dict(HistCompetitie.COMP_TYPE)[self.comp_type]
        except KeyError:
            raise Resolver404()

        context['jaar'] = self.jaar
        context['klasse'] = self.klasse
        context['form'] = self.form
        context['filter_url'] = self.base_url

        if context['is_paginated']:
            context['page_links'] = self._make_link_urls(context)
        if self.get_filter:
            # als een filter actief is, toon de 'clear' knop
            context['unfiltered_url'] = self.base_url
        elif self.paginate_by > 0:
            # geen filter, wel paginering
            # toon de "laad alle ## records" knop
            context['all_url'] = self.base_url + '?all=1'
            context['all_count'] = self.all_count
        # else: we laten de 'all' lijst zien dus laat de 'all' knop weg

        menu_dynamics(request, context)#, 'histcomp')
        return context


class HistCompIndivView(HistCompBaseView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_INDIV
    reverse_name = 'HistComp:indiv'
    query_class = HistCompetitieIndividueel
    is_team = False


class HistCompTeamView(HistCompBaseView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_TEAM
    reverse_name = 'HistComp:team'
    query_class = HistCompetitieTeam
    is_team = True

# end of file
