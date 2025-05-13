# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import Http404
from django.db.models import Q
from django.views.generic import ListView, TemplateView
from Records.definities import disc2str, gesl2str, makl2str, lcat2str
from Records.models import IndivRecord, AnderRecord
from Records.forms import ZoekForm
from Site.core.static import static_safe
from Sporter.models import Sporter


TEMPLATE_RECORDS_OVERZICHT = 'records/records_overzicht.dtl'
TEMPLATE_RECORDS_SPECIFIEK = 'records/records_specifiek.dtl'
TEMPLATE_RECORDS_ZOEK = 'records/records_zoek.dtl'


class RecordsOverzichtView(ListView):
    """ Dit is de top-level pagina van de records met een overzicht van de meest
        recente records
    """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_OVERZICHT

    @staticmethod
    def set_url_specifiek(obj):
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr, 'discipline': obj.discipline})

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
        disc2img = {
            'OD': static_safe('plein/badge_discipline_outdoor.png'),
            '18': static_safe('plein/badge_discipline_indoor.png'),
            '25': static_safe('plein/badge_discipline_25m1p.png')
        }

        # 10 nieuwste records (alle disciplines)
        # op datum (nieuwste boven) en volg_nr (hoogste boven)
        objs = IndivRecord.objects.all().order_by('-datum', '-volg_nr')[:10]
        for obj in objs:
            self.set_url_specifiek(obj)
            obj.img = disc2img[obj.discipline]
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['andere_records'] = AnderRecord.objects.order_by('-volgorde')       # hoogste eerst

        context['kruimels'] = (
            (None, 'Records'),
        )

        return context


class RecordsIndivSpecifiekView(TemplateView):
    """ Deze view laat een specifiek record zijn aan de hand van het nummer
        Onder het record worden de gerelateerde records getoond.
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

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (None, 'Details')
        )

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
                # zoek het lid met dit nummer
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

        return list()

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['have_searched'] = self.get_zoekterm != ""
        context['zoekterm'] = self.get_zoekterm
        context['records_zoek_url'] = reverse('Records:zoek')

        for obj in context['object_list']:
            obj.para_str = ''
            if obj.para_klasse:
                obj.para_str = ' - para: ' + obj.para_klasse
        # for

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (None, 'Zoeken')
        )

        return context

# end of file
