# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.db.models import Q
from django.views.generic import ListView, TemplateView
from django.templatetags.static import static
from Plein.menu import menu_dynamics
from Sporter.models import Sporter
from .models import IndivRecord, BesteIndivRecords
from .forms import ZoekForm
from types import SimpleNamespace


TEMPLATE_RECORDS_OVERZICHT = 'records/records_overzicht.dtl'
TEMPLATE_RECORDS_SPECIFIEK = 'records/records_specifiek.dtl'
TEMPLATE_RECORDS_ZOEK = 'records/records_zoek.dtl'
TEMPLATE_RECORDS_VERBETERBAAR_KIES_DISC = 'records/verbeterbaar_kies_disc.dtl'
TEMPLATE_RECORDS_VERBETERBAAR_DISCIPLINE = 'records/verbeterbaar_discipline.dtl'


DISCIPLINE_TO_ICON = {
    'OD': static('plein/badge_nhb_outdoor.png'),
    '18': static('plein/badge_nhb_indoor.png'),
    '25': static('plein/badge_nhb_25m1p.png')
}

# vertaling van velden naar urlconf elementen en terug
disc2str = {'OD': 'Outdoor',
            '18': 'Indoor',
            '25': '25m 1pijl'}

gesl2str = {'M': 'Mannen',
            'V': 'Vrouwen'}

makl2str = {'R': 'Recurve',
            'C': 'Compound',
            'BB': 'Barebow',
            'IB': 'Instinctive bow',
            'LB': 'Longbow'}

lcat2str = {'M': 'Masters (50+)',
            'S': 'Senioren',
            'J': 'Junioren (t/m 20 jaar)',
            'C': 'Cadetten (t/m 17 jaar)',
            'U': 'Gecombineerd (bij para)'}     # alleen voor Outdoor

disc2url = {'OD': 'outdoor',
            '18': 'indoor',
            '25': '25m1pijl'}

gesl2url = {'M': 'mannen',
            'V': 'vrouwen'}

makl2url = {'R': 'recurve',
            'C': 'compound',
            'BB': 'barebow',
            'IB': 'instinctive-bow',
            'LB': 'longbow',
            'O': 'para-klassen'}

lcat2url = {'M': 'masters',
            'S': 'senioren',
            'J': 'junioren',
            'C': 'cadetten',
            'U': 'gecombineerd'}

sel2url4arg = {'disc': disc2url,
               'gesl': gesl2url,
               'makl': makl2url,
               'lcat': lcat2url}

url2disc = {v: k for k, v in disc2url.items()}
url2gesl = {v: k for k, v in gesl2url.items()}
url2makl = {v: k for k, v in makl2url.items()}
url2lcat = {v: k for k, v in lcat2url.items()}

url2sel4arg = {'disc': url2disc,
               'gesl': url2gesl,
               'makl': url2makl,
               'lcat': url2lcat}


class RecordsOverzichtView(ListView):
    """ Dit is de top-level pagina van de records met een overzicht van de meest
        recente records
    """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_OVERZICHT

    @staticmethod
    def set_url_specifiek(obj):
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr, 'discipline': obj.discipline})
        obj.icon = DISCIPLINE_TO_ICON[obj.discipline]

        if obj.is_world_record:
            obj.title_str = "Wereld Record"
        elif obj.is_european_record:
            obj.title_str = "Europees Record"
        else:
            obj.title_str = "Nederlands Record"

        # heren/dames
        obj.descr1_str = gesl2str[obj.geslacht] + " "

        # junioren, etc.
        lcat = lcat2str[obj.leeftijdscategorie]
        pos = lcat.find(' (')
        if pos > 0:
            lcat = lcat[:pos]
        obj.descr1_str += lcat

        # type wedstrijd
        obj.descr2_str = (disc2str[obj.discipline] +             # indoor/outdoor
                          " " + makl2str[obj.materiaalklasse] +  # longbow/recurve
                          " " + obj.soort_record)                # 70m (72p)

        # para
        if obj.para_klasse:
            obj.para_str = "Para " + obj.para_klasse
        else:
            obj.para_str = None

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # 10 nieuwste records (alle disciplines)
        # op datum (nieuwste boven) en volg_nr (hoogste boven)
        objs = IndivRecord.objects.all().order_by('-datum', '-volg_nr')[:10]
        for obj in objs:
            self.set_url_specifiek(obj)
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='records')
        return context


class RecordsIndivSpecifiekView(TemplateView):
    """ Deze view laat een specifiek record zijn aan de hand van het nummer
        Onder het record worden de relateerde records getoond.
    """
    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_SPECIFIEK

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def set_url_specifiek(obj):
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr, 'discipline': obj.discipline})

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        volg_nr = self.kwargs['nummer']     # parameter guaranteed by urlconf
        discipline = self.kwargs['discipline']

        # zoek het specifieke record erbij
        try:
            spec = IndivRecord.objects.get(volg_nr=volg_nr, discipline=discipline)
        except IndivRecord.DoesNotExist:
            # dat was geen valide record nummer
            raise Http404('Record niet gevonden')

        # voeg informatie toe voor de template
        spec.gesl_str = gesl2str[spec.geslacht]
        spec.disc_str = disc2str[spec.discipline]
        spec.lcat_str = lcat2str[spec.leeftijdscategorie]
        spec.makl_str = makl2str[spec.materiaalklasse]

        spec.op_pagina = "specifiek_record_%s-%s" % (discipline, volg_nr)

        # zoek de andere records die hier bij horen, aflopend gesorteerd op datum
        # hier zit ook het record zelf bij
        objs = IndivRecord.objects.filter(
                        geslacht=spec.geslacht,
                        discipline=spec.discipline,
                        leeftijdscategorie=spec.leeftijdscategorie,
                        materiaalklasse=spec.materiaalklasse,
                        soort_record=spec.soort_record,
                        para_klasse=spec.para_klasse).order_by('-datum')

        for obj in objs:
            obj.is_specifieke_record = (obj.volg_nr == spec.volg_nr)
            self.set_url_specifiek(obj)
        # for

        context['obj_record'] = spec
        context['object_list'] = objs

        menu_dynamics(self.request, context, actief='records')
        return context


class RecordsZoekView(ListView):
    """ Deze view laat de gebruiker een zoekterm invoeren/wijziging en toont de records
        waarin deze zoekterm voorkomt.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_ZOEK

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = ZoekForm()
        self.get_zoekterm = None

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # retourneer een QuerySet voor de template
        # onthoud zaken in de object instantie

        # haal de zoekterm op
        self.form = ZoekForm(self.request.GET)
        self.form.full_clean()  # vult cleaned_data
        try:
            self.get_zoekterm = self.form.cleaned_data['zoekterm']
        except KeyError:
            # zoekterm was te lang en is daarom niet opgeslagen
            self.get_zoekterm = ''

        if self.get_zoekterm:
            zoekterm = self.get_zoekterm

            try:
                filter_nr = int(zoekterm)
            except ValueError:
                filter_nr = 0

            if filter_nr and len(str(filter_nr)) == 6:
                # zoek het NHB lid met dit nummer
                try:
                    sporter = Sporter.objects.get(lid_nr=filter_nr)
                except Sporter.DoesNotExist:
                    # geen lid met dit nummer
                    # of slecht getal
                    pass
                else:
                    # zoek alle records van dit lid
                    return IndivRecord.objects.filter(sporter=sporter)
            else:
                return (IndivRecord
                        .objects
                        .filter(
                                Q(soort_record__icontains=zoekterm) |
                                Q(naam__icontains=zoekterm) |
                                Q(plaats__icontains=zoekterm) |
                                Q(land__icontains=zoekterm) |
                                Q(sporter__unaccented_naam__icontains=zoekterm))
                        .order_by('-datum',
                                  'soort_record'))[:settings.RECORDS_MAX_ZOEKRESULTATEN]

        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['have_searched'] = self.get_zoekterm != ""
        context['zoekterm'] = self.get_zoekterm
        context['records_zoek_url'] = reverse('Records:zoek')
        menu_dynamics(self.request, context, actief='records')
        return context


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
            obj.beschrijving = disc2str[obj.discipline]
            url_disc = disc2url[obj.discipline]
            obj.url = reverse('Records:indiv-verbeterbaar-disc', kwargs={'disc': url_disc})
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='records')
        return context


class RecordsVerbeterbaarInDiscipline(ListView):

    """ Deze view laat de gebruiker de lijst van verbeterbare NL records zien binnen een discipline """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_VERBETERBAAR_DISCIPLINE

    boogtype2filter = {'alles': '', 'recurve': 'R', 'compound': 'C', 'barebow': 'BB', 'longbow': 'LB', 'instinctive': 'IB'}
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
        for geslacht_key in self.geslacht2filter.keys():
            obj = SimpleNamespace()
            obj.button_str = geslacht_key
            if geslacht != geslacht_key:
                obj.url = self.maak_url(base_url, extra, 'geslacht', geslacht_key)
            else:
                obj.url = None
            context['geslacht'].append(obj)
        # for

        extra = list()
        if geslacht != 'alles':
            extra.append('geslacht=' + geslacht)
        if leeftijd != 'alles':
            extra.append('leeftijdsklasse=' + leeftijd)
        context['bogen'] = list()
        for boogtype_key in self.boogtype2filter.keys():
            obj = SimpleNamespace()
            obj.button_str = boogtype_key
            if boogtype != boogtype_key:
                obj.url = self.maak_url(base_url, extra, 'boog', boogtype_key)
            else:
                obj.url = None
            context['bogen'].append(obj)
        # for

        extra = list()
        if boogtype != 'alles':
            extra.append('boog=' + boogtype)
        if geslacht != 'alles':
            extra.append('geslacht=' + geslacht)
        context['leeftijd'] = list()
        for leeftijd_key in self.leeftijd2filter.keys():

            # skip de 'para' knop tenzij het voor Outdoor is
            if leeftijd_key == 'para' and discipline != 'OD':
                continue

            obj = SimpleNamespace()
            obj.button_str = leeftijd_key
            if leeftijd != leeftijd_key:
                obj.url = self.maak_url(base_url, extra, 'leeftijdsklasse', leeftijd_key)
            else:
                obj.url = None
            context['leeftijd'].append(obj)
        # for

        context['is_alles'] = (boogtype == geslacht == leeftijd)

        context['toon_para_kolom'] = False
        for obj in context['object_list']:
            if obj.para_klasse:
                context['toon_para_kolom'] = True
                break
        # for

        menu_dynamics(self.request, context, actief='records')
        return context

# end of file
