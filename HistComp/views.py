# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import Resolver404, reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, TemplateView
from django.db.models import Q
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from NhbStructuur.models import NhbLid
from .models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam
from .forms import FilterForm
from Plein.menu import menu_dynamics
from decimal import Decimal

TEMPLATE_HISTCOMP_ALLEJAREN = 'hist/histcomp_top.dtl'
TEMPLATE_HISTCOMP_INDIV = 'hist/histcomp_indiv.dtl'
TEMPLATE_HISTCOMP_TEAM = 'hist/histcomp_team.dtl'
TEMPLATE_HISTCOMP_INTERLAND = 'hist/interland.dtl'

RESULTS_PER_PAGE = 100

KLASSEN_VOLGORDE = ("Recurve", "Compound", "Barebow", "Longbow", "Instinctive")


MINIMALE_LEEFTIJD_JEUGD_INTERLAND = 13      # alles jonger wordt niet getoond
MAXIMALE_LEEFTIJD_JEUGD_INTERLAND = 20      # boven deze leeftijd Senior


class HistCompAlleJarenView(ListView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_ALLEJAREN

    def _zet_op_volgorde_klassen(self, objs_unsorted):
        # sorteer de klassen op de gewenste volgorde
        # deze routine lijkt een beetje omslachtig, maar dat komt omdat QuerySet geen remove heeft
        objs = list()
        for klas in KLASSEN_VOLGORDE:
            # zoek objecten met klassen die hier aan voldoen
            transfer = list()
            for obj in objs_unsorted:
                if klas in obj.klasse:
                    objs.append(obj)
            # for
        # for
        # voeg de rest ongesorteerd toe
        for obj in objs_unsorted:
            if obj not in objs:
                objs.append(obj)
        # for
        return objs

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # zoek het nieuwste seizoen beschikbaar
        qset = HistCompetitie.objects.order_by('-seizoen').distinct('seizoen')
        if len(qset) == 0:
            # geen data beschikbaar
            self.seizoen = ""
            objs = list()
        else:
            # neem de data van het nieuwste seizoen
            self.seizoen = qset[0].seizoen
            objs_unsorted = HistCompetitie.objects.filter(seizoen=self.seizoen)
            objs = self._zet_op_volgorde_klassen(objs_unsorted)
            # bepaal voor elke entry een url om de uitslag te bekijken
            for obj in objs:
                if obj.is_team:
                    urlconf = 'HistComp:team'
                else:
                    urlconf = 'HistComp:indiv'
                obj.url = reverse(urlconf, kwargs={'histcomp_pk': obj.pk})
            # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['seizoen'] = self.seizoen

        if HistCompetitie.objects.filter(seizoen=self.seizoen, is_team=True).count() > 0:
            context['show_team'] = True

        menu_dynamics(self.request, context, 'histcomp')
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
    is_team = None                  # override in child class
    reverse_name = None             # override in child class
    query_class = None              # override in child class
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

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # retourneer een QuerySet voor de template
        # onthoud zaken in de object instantie

        # haal de GET parameters uit de request
        self.form = FilterForm(self.request.GET)
        self.histcomp_pk = self.kwargs['histcomp_pk']
        self.base_url = reverse('HistComp:indiv', kwargs={'histcomp_pk': self.histcomp_pk})
        # pak het HistCompetitie object erbij
        try:
            histcomp = HistCompetitie.objects.get(pk=self.histcomp_pk)
        except HistCompetitie.DoesNotExist:
            # foute histcomp_pk
            raise Resolver404()

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

                if self.is_team:
                    if filter_is_nr:
                        return self.query_class.objects.filter(
                            vereniging_nr__exact=self.get_filter,
                            histcompetitie=histcomp).order_by('rank')
                    else:
                        return self.query_class.objects.filter(
                            vereniging_naam__icontains=self.get_filter,
                            histcompetitie=histcomp).order_by('rank')
                else:
                    if filter_is_nr:
                        return self.query_class.objects.filter(
                                            vereniging_nr__exact=self.get_filter,
                                            histcompetitie=histcomp).order_by('rank')
                    else:
                        return self.query_class.objects.filter(
                                            Q(schutter_naam__icontains=self.get_filter) |
                                            Q(vereniging_naam__icontains=self.get_filter),
                                            histcompetitie=histcomp).order_by('rank')

        self.all_count = self.query_class.objects.filter(
                                histcompetitie=histcomp).count()

        return self.query_class.objects.filter(
                                histcompetitie=histcomp).order_by('rank')

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

        self.histcomp.comp_type_str = HistCompetitie.comptype2str[self.histcomp.comp_type]
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

        menu_dynamics(self.request, context, 'histcomp')
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


class InterlandView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de resultaten van de 25m1pijl die nodig zijn voor de Interland """

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_INTERLAND

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # maak een cache aan van nhb leden
        # we filteren hier niet op inactieve leden
        nhblid_dict = dict()  # [nhb_nr] = NhbLid
        for obj in NhbLid.objects.all():
            nhblid_dict[obj.nhb_nr] = obj
        # for

        # zoek het nieuwste seizoen beschikbaar
        qset = HistCompetitie.objects.order_by('-seizoen').distinct('seizoen')
        if len(qset) > 0:
            # neem de data van het nieuwste seizoen
            context['seizoen'] = seizoen = qset[0].seizoen
            context['klassen'] = list()

            # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
            # dit is het tweede jaar van het seizoen
            context['wedstrijd_jaar'] = wedstrijd_jaar = int(seizoen.split('/')[1])

            context['jeugd_min'] = MINIMALE_LEEFTIJD_JEUGD_INTERLAND
            context['jeugd_max'] = MAXIMALE_LEEFTIJD_JEUGD_INTERLAND

            for klasse in (HistCompetitie
                           .objects
                           .filter(comp_type='25', seizoen=seizoen, is_team=False)):
                context['klassen'].append(klasse)

                # zoek alle schutters erbij met minimaal 5 scores
                klasse.schutters = list()

                for obj in (HistCompetitieIndividueel
                            .objects
                            .filter(histcompetitie=klasse, gemiddelde__gt=Decimal('0.000'))
                            .order_by('-gemiddelde')):

                    if obj.tel_aantal_scores() >= 5:

                        # zoek het nhb lid erbij
                        try:
                            nhblid = nhblid_dict[obj.schutter_nr]
                        except KeyError:
                            nhblid = None
                        else:
                            if not nhblid.is_actief_lid:
                                nhblid = None

                        if nhblid:
                            obj.nhblid = nhblid
                            obj.wedstrijd_leeftijd = nhblid.bereken_wedstrijdleeftijd(wedstrijd_jaar)
                            if obj.wedstrijd_leeftijd >= MINIMALE_LEEFTIJD_JEUGD_INTERLAND:
                                obj.is_jeugd = (obj.wedstrijd_leeftijd <= MAXIMALE_LEEFTIJD_JEUGD_INTERLAND)
                                klasse.schutters.append(obj)
            # for

        menu_dynamics(self.request, context, actief='histcomp')
        return context

# end of file
