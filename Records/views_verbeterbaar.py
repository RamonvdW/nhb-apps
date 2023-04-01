# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView
from django.templatetags.static import static
from Plein.menu import menu_dynamics
from Records.definities import disc2str, disc2url, url2disc, gesl2str, makl2str, lcat2str
from Records.models import IndivRecord, BesteIndivRecords
from types import SimpleNamespace


TEMPLATE_RECORDS_VERBETERBAAR_KIES_DISC = 'records/verbeterbaar_kies_disc.dtl'
TEMPLATE_RECORDS_VERBETERBAAR_DISCIPLINE = 'records/verbeterbaar_discipline.dtl'


DISCIPLINE_TO_ICON = {
    'OD': static('plein/badge_nhb_outdoor.png'),
    '18': static('plein/badge_nhb_indoor.png'),
    '25': static('plein/badge_nhb_25m1p.png')
}


class RecordsVerbeterbaarKiesDisc(ListView):

    """ Deze view laat de gebruiker een discipline kiezen """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_VERBETERBAAR_KIES_DISC

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        objs = (IndivRecord
                .objects
                .distinct('discipline')
                .order_by('discipline'))

        for obj in objs:
            obj.titel = disc2str[obj.discipline]
            obj.img_src = DISCIPLINE_TO_ICON[obj.discipline]
            obj.tekst = "Toon alle verbeterbare records van de discipline %s." % obj.titel

            url_disc = disc2url[obj.discipline]
            obj.url = reverse('Records:indiv-verbeterbaar-disc', kwargs={'disc': url_disc})
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (None, 'Verbeterbaar')
        )

        menu_dynamics(self.request, context)
        return context


class RecordsVerbeterbaarInDiscipline(ListView):

    """ Deze view laat de gebruiker de lijst van verbeterbare NL records zien binnen een discipline """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_VERBETERBAAR_DISCIPLINE

    boogtype2filter = {'alles': '', 'recurve': 'R', 'compound': 'C', 'barebow': 'BB', 'longbow': 'LB', 'traditional': 'TR'}
    geslacht2filter = {'alles': '', 'man': 'M', 'vrouw': 'V'}
    leeftijd2filter = {'alles': '', 'para': 'U', 'master': 'M', 'senior': 'S', 'junior': 'J', 'cadet': 'C'}

    def dispatch(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen voor get_queryset
            hier is het mogelijk om een redirect te doen.
        """
        url_disc = self.kwargs['disc']
        try:
            _ = url2disc[url_disc]      # check dat deze aanwezig is
            _ = self.boogtype2filter[request.GET.get('boog', 'alles')]
            _ = self.geslacht2filter[request.GET.get('geslacht', 'alles')]
            _ = self.leeftijd2filter[request.GET.get('leeftijdsklasse', 'alles')]
        except KeyError:
            return HttpResponseRedirect(reverse('Records:indiv-verbeterbaar'))

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        url_disc = self.kwargs['disc']
        discipline = url2disc[url_disc]

        filter_boogtype = self.boogtype2filter[self.request.GET.get('boog', 'alles')]
        filter_geslacht = self.geslacht2filter[self.request.GET.get('geslacht', 'alles')]
        filter_leeftijd = self.leeftijd2filter[self.request.GET.get('leeftijdsklasse', 'alles')]

        objs = (BesteIndivRecords
                .objects
                .filter(discipline=discipline)
                .exclude(beste=None)
                .select_related('beste')
                .order_by('volgorde'))

        if filter_geslacht:
            objs = objs.filter(geslacht=filter_geslacht)

        if filter_boogtype:
            objs = objs.filter(materiaalklasse=filter_boogtype)

        if filter_leeftijd:
            objs = objs.filter(leeftijdscategorie=filter_leeftijd)

        for obj in objs:
            obj.geslacht_str = gesl2str[obj.geslacht]
            obj.materiaalklasse_str = makl2str[obj.materiaalklasse]
            obj.leeftijdscategorie_str = lcat2str[obj.leeftijdscategorie]

            obj.url_details = reverse('Records:specifiek', kwargs={'discipline': obj.discipline,
                                                                   'nummer': obj.beste.volg_nr})
        # for

        return objs

    @staticmethod
    def maak_url(base_url, extra, param_type, param):
        extra = extra[:]
        if param != 'alles':
            extra.append('%s=%s' % (param_type, param))
        if len(extra):
            extra.sort()
            return base_url + '?' + '&'.join(extra)
        return base_url

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        url_disc = self.kwargs['disc']
        discipline = url2disc[url_disc]
        context['beschrijving'] = disc2str[discipline]

        boogtype = self.request.GET.get('boog', 'alles')
        geslacht = self.request.GET.get('geslacht', 'alles')
        leeftijd = self.request.GET.get('leeftijdsklasse', 'alles')

        base_url = reverse('Records:indiv-verbeterbaar-disc', kwargs={'disc': url_disc})

        extra = list()
        if boogtype != 'alles':
            extra.append('boog=' + boogtype)
        if leeftijd != 'alles':
            extra.append('leeftijdsklasse=' + leeftijd)

        context['geslacht'] = list()
        for geslacht_key, geslacht_filter in self.geslacht2filter.items():
            obj = SimpleNamespace()
            obj.sel = 'geslacht_' + geslacht_filter
            try:
                obj.beschrijving = gesl2str[geslacht_filter]
            except KeyError:
                obj.beschrijving = 'Alle'
            if geslacht == geslacht_key:
                obj.selected = True
            obj.url = self.maak_url(base_url, extra, 'geslacht', geslacht_key)
            context['geslacht'].append(obj)
        # for

        extra = list()
        if geslacht != 'alles':
            extra.append('geslacht=' + geslacht)
        if leeftijd != 'alles':
            extra.append('leeftijdsklasse=' + leeftijd)

        context['bogen'] = list()
        for boogtype_key, boogtype_filter in self.boogtype2filter.items():
            obj = SimpleNamespace()
            obj.sel = "boog_" + boogtype_filter
            try:
                obj.beschrijving = makl2str[boogtype_filter]
            except KeyError:
                obj.beschrijving = 'Alle'
            if boogtype == boogtype_key:
                obj.selected = True
            obj.url = self.maak_url(base_url, extra, 'boog', boogtype_key)
            context['bogen'].append(obj)
        # for

        extra = list()
        if boogtype != 'alles':
            extra.append('boog=' + boogtype)
        if geslacht != 'alles':
            extra.append('geslacht=' + geslacht)

        context['leeftijd'] = list()
        for leeftijd_key, leeftijd_filter in self.leeftijd2filter.items():

            # skip de 'para' knop tenzij het voor Outdoor is
            if leeftijd_key == 'para' and discipline != 'OD':
                continue

            obj = SimpleNamespace()
            obj.sel = 'lcat_' + leeftijd_filter
            try:
                obj.beschrijving = lcat2str[leeftijd_filter]
            except KeyError:
                obj.beschrijving = 'Alle'
            if leeftijd == leeftijd_key:
                obj.selected = True
            obj.url = self.maak_url(base_url, extra, 'leeftijdsklasse', leeftijd_key)
            context['leeftijd'].append(obj)
        # for

        context['is_alles'] = (boogtype == geslacht == leeftijd)

        context['toon_para_kolom'] = False
        for obj in context['object_list']:
            if obj.para_klasse:
                context['toon_para_kolom'] = True
                break
        # for

        context['aantal_regels'] = len(context['object_list']) + 2

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (reverse('Records:indiv-verbeterbaar'), 'Verbeterbaar'),
            (None, context['beschrijving'])
        )

        menu_dynamics(self.request, context)
        return context

# end of file
