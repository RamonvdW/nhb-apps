# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from HistComp.forms import FilterForm
from Plein.menu import menu_dynamics
from urllib.parse import quote_plus

TEMPLATE_HISTCOMP_ALLEJAREN = 'hist/histcomp_top.dtl'
TEMPLATE_HISTCOMP_INDIV = 'hist/histcomp_indiv.dtl'

RESULTS_PER_PAGE = 100

KLASSEN_VOLGORDE = ("Recurve", "Compound", "Barebow", "Instinctive bow", "Instinctive Bow", "Traditional", "Longbow")

COMP_TYPE_STR = {
    '18': 'Indoor',
    '25': '25m 1pijl'
}


class HistCompTop(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_ALLEJAREN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek het nieuwste seizoen beschikbaar
        qset = (HistCompetitie
                .objects
                .exclude(is_openbaar=False)     # False vanaf einde regiocompetitie tot afsluiten BK/competitie
                .order_by('-seizoen')
                .distinct('seizoen'))

        if len(qset) == 0:
            context['geen_data'] = True
        else:
            # neem de data van het nieuwste seizoen
            context['seizoen'] = seizoen = qset[0].seizoen

            qset = HistCompetitie.objects.filter(seizoen=seizoen, is_team=False).distinct('comp_type', 'klasse')

            gevonden = dict()       # [(comp_type, klasse)] = HistCompetitie
            for obj in qset:
                tup = (obj.comp_type, obj.klasse)
                gevonden[tup] = obj
            # for

            context['bogen_indiv_18'] = bogen_indiv_18 = list()
            context['bogen_indiv_25'] = bogen_indiv_25 = list()

            for klasse in KLASSEN_VOLGORDE:

                try:
                    histcomp = gevonden[('18', klasse)]
                except KeyError:
                    pass
                else:
                    tup = (klasse, reverse('HistComp:indiv', kwargs={'histcomp_pk': histcomp.pk}))
                    bogen_indiv_18.append(tup)

                try:
                    histcomp = gevonden[('25', klasse)]
                except KeyError:
                    pass
                else:
                    tup = (klasse, reverse('HistComp:indiv', kwargs={'histcomp_pk': histcomp.pk}))
                    bogen_indiv_25.append(tup)
            # for

        context['show_team'] = False

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
        self.histcomp_pk = None

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # retourneer een QuerySet voor de template
        # onthoud zaken in de object instantie

        # haal de GET parameters uit de request
        self.form = FilterForm(self.request.GET)
        self.histcomp_pk = self.kwargs['histcomp_pk'][:6]       # afkappen voor de veiligheid
        self.base_url = reverse('HistComp:indiv', kwargs={'histcomp_pk': self.histcomp_pk})
        # pak het HistCompetitie object erbij
        try:
            histcomp = HistCompetitie.objects.get(pk=self.histcomp_pk)
        except HistCompetitie.DoesNotExist:
            # foute histcomp_pk
            raise Http404('Competitie niet gevonden')

        self.histcomp = histcomp

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
                        return HistCompetitieIndividueel.objects.filter(
                                            vereniging_nr__exact=filter_nr,
                                            histcompetitie=histcomp).order_by('rank')
                    else:
                        return HistCompetitieIndividueel.objects.filter(
                                            schutter_nr__exact=filter_nr,
                                            histcompetitie=histcomp).order_by('rank')
                else:
                    return HistCompetitieIndividueel.objects.filter(
                                        Q(schutter_naam__icontains=self.get_filter) |
                                        Q(vereniging_naam__icontains=self.get_filter),
                                        histcompetitie=histcomp).order_by('rank')

        self.all_count = HistCompetitieIndividueel.objects.filter(histcompetitie=histcomp).count()

        return HistCompetitieIndividueel.objects.filter(histcompetitie=histcomp).order_by('rank')

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
            obj.schutter_nr_str = str(obj.schutter_nr)
        # for

        context['aantal_regels'] = 2 + len(context['object_list'])

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('HistComp:top'), 'Uitslag vorig seizoen'),
            (None, COMP_TYPE_STR[self.histcomp.comp_type]),
            (None, self.histcomp.klasse)
        )

        menu_dynamics(self.request, context)
        return context


# end of file
