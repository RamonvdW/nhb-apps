# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponse, Http404
from django.views.generic import ListView, TemplateView
from django.db.models import Q
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige
from Sporter.models import Sporter
from .models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam
from .forms import FilterForm
from decimal import Decimal
from urllib.parse import quote_plus
import csv

TEMPLATE_HISTCOMP_ALLEJAREN = 'hist/histcomp_top.dtl'
TEMPLATE_HISTCOMP_INDIV = 'hist/histcomp_indiv.dtl'
TEMPLATE_HISTCOMP_TEAM = 'hist/histcomp_team.dtl'
TEMPLATE_HISTCOMP_INTERLAND = 'hist/interland.dtl'

RESULTS_PER_PAGE = 100

KLASSEN_VOLGORDE = ("Recurve", "Compound", "Barebow", "Instinctive", "Longbow")


MINIMALE_LEEFTIJD_JEUGD_INTERLAND = 13      # alles jonger wordt niet getoond
MAXIMALE_LEEFTIJD_JEUGD_INTERLAND = 20      # boven deze leeftijd Senior


class HistCompAlleJarenView(ListView):

    # class variables shared by all instances
    template_name = TEMPLATE_HISTCOMP_ALLEJAREN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.seizoen = ""

    @staticmethod
    def _zet_op_volgorde_klassen(objs_unsorted):
        # sorteer de klassen op de gewenste volgorde
        # deze routine lijkt een beetje omslachtig, maar dat komt omdat QuerySet geen remove heeft
        objs = list()
        for klas in KLASSEN_VOLGORDE:
            # zoek objecten met klassen die hier aan voldoen
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
        qset = (HistCompetitie
                .objects
                .exclude(is_openbaar=False)
                .order_by('-seizoen')
                .distinct('seizoen'))
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

        menu_dynamics_competitie(self.request, context, actief='histcomp')
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
        self.histcomp = None
        self.histcomp_pk = None

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

        menu_dynamics_competitie(self.request, context, actief='histcomp')
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
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def maak_data(self, context):

        # maak een cache aan van leden
        lid_nr2sporter = dict()  # [lid_nr] = Sporter
        for sporter in (Sporter
                        .objects
                        .filter(is_actief_lid=True)
                        .select_related('bij_vereniging')
                        .all()):
            lid_nr2sporter[sporter.lid_nr] = sporter
        # for

        context['jeugd_min'] = MINIMALE_LEEFTIJD_JEUGD_INTERLAND
        context['jeugd_max'] = MAXIMALE_LEEFTIJD_JEUGD_INTERLAND

        context['klassen'] = list()

        # zoek het nieuwste seizoen beschikbaar
        qset = HistCompetitie.objects.order_by('-seizoen').distinct('seizoen')
        if len(qset) > 0:
            # neem de data van het nieuwste seizoen
            context['seizoen'] = seizoen = qset[0].seizoen

            # bepaal het jaar waarin de wedstrijdleeftijd bepaald moet worden
            # dit is het tweede jaar van het seizoen
            context['wedstrijd_jaar'] = wedstrijd_jaar = int(seizoen.split('/')[1])

            for klasse in (HistCompetitie
                           .objects
                           .filter(comp_type='25', seizoen=seizoen, is_team=False)):
                context['klassen'].append(klasse)

                klasse.url_download = reverse('HistComp:interland-als-bestand',
                                              kwargs={'klasse_pk': klasse.pk})

                # zoek alle records erbij met minimaal 5 scores
                klasse.indiv = list()

                for indiv in (HistCompetitieIndividueel
                              .objects
                              .filter(histcompetitie=klasse,
                                      gemiddelde__gt=Decimal('0.000'))
                              .order_by('-gemiddelde')):

                    if indiv.tel_aantal_scores() >= 5:

                        # zoek de sporter erbij
                        try:
                            sporter = lid_nr2sporter[indiv.schutter_nr]
                        except KeyError:
                            sporter = None

                        if sporter:
                            indiv.sporter = sporter
                            indiv.wedstrijd_leeftijd = sporter.bereken_wedstrijdleeftijd(wedstrijd_jaar)
                            if indiv.wedstrijd_leeftijd >= MINIMALE_LEEFTIJD_JEUGD_INTERLAND:
                                if indiv.wedstrijd_leeftijd <= MAXIMALE_LEEFTIJD_JEUGD_INTERLAND:
                                    indiv.leeftijd_str = "%s (jeugd)" % indiv.wedstrijd_leeftijd
                                else:
                                    indiv.leeftijd_str = "Senior"

                                klasse.indiv.append(indiv)
            # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self.maak_data(context)

        menu_dynamics_competitie(self.request, context, actief='histcomp')
        return context


class InterlandAlsBestandView(InterlandView):

    """ Deze klasse wordt gebruikt om de interland deelnemers lijst
        te downloaden als csv bestand
    """

    def get(self, request, *args, **kwargs):

        try:
            klasse_pk = int(kwargs['klasse_pk'][:6])  # afkappen geeft beveiliging
            klasse = HistCompetitie.objects.get(pk=klasse_pk)
        except (ValueError, HistCompetitie.DoesNotExist):
            raise Http404('Klasse niet gevonden')

        context = dict()
        self.maak_data(context)

        indivs = None
        for context_klasse in context['klassen']:
            if context_klasse.pk == klasse.pk:
                indivs = context_klasse.indiv
                break   # from the for
        # for

        if indivs is None:
            raise Http404('Geen sporters gevonden')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="interland.csv"'

        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings
        writer.writerow(['Gemiddelde', 'Wedstrijdleeftijd', 'Geslacht', 'NHB nummer', 'Naam', 'Vereniging'])

        for indiv in indivs:
            writer.writerow([indiv.gemiddelde,
                             indiv.leeftijd_str,
                             indiv.sporter.geslacht,
                             indiv.sporter.lid_nr,
                             indiv.sporter.volledige_naam(),
                             indiv.sporter.bij_vereniging])
        # for

        return response

# end of file
