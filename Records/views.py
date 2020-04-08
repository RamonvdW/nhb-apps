# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.staticfiles.templatetags.staticfiles import static
from Plein.menu import menu_dynamics
from NhbStructuur.models import NhbLid
from .models import IndivRecord
from .forms import ZoekForm

TEMPLATE_RECORDS_OVERZICHT = 'records/records_overzicht.dtl'
TEMPLATE_RECORDS_SPECIFIEK = 'records/records_specifiek.dtl'
TEMPLATE_RECORDS_INDIV_ZOOM1234 = 'records/records_indiv_zoom1234.dtl'
TEMPLATE_RECORDS_INDIV_ZOOM5 = 'records/records_indiv_zoom5.dtl'
TEMPLATE_RECORDS_ZOEK = 'records/records_zoek.dtl'


DISCIPLINE_TO_ICON = {
    'OD': static('plein/badge_nhb_outdoor.png'),
    '18': static('plein/badge_nhb_indoor.png'),
    '25': static('plein/badge_nhb_25m1p.png')
}


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

        # heren/dames
        obj.descr1_str = IndivRecord.gesl2str[obj.geslacht] + " "

        # junioren, etc.
        obj.descr1_str += IndivRecord.lcat2str[obj.leeftijdscategorie]

        # type wedstrijd
        obj.descr2_str = (IndivRecord.disc2str[obj.discipline] +             # indoor/outdoor
                          " " + IndivRecord.makl2str[obj.materiaalklasse] +  # longbow/recurve
                          " " + obj.soort_record)                            # 70m (72p)

        # recurve etc.
        if obj.para_klasse:
            obj.descr2_str += " para " + obj.para_klasse


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


class SelObject(object):
    """ Simple objects for giving to the template """

    def __init__(self):
        self.sel_url = self.sel_str = ""


class RecordsIndivZoomBaseView(ListView):

    # class variables shared by all instances
    # (none)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sel_gesl = None  # geslacht
        self.sel_disc = None  # discipline
        self.sel_makl = None  # materiaalklasse
        self.sel_lcat = None  # leeftijdscategorie

        self.disc_str = self.gesl_str = self.makl_str = self.lcat_str = None
        self.url = None
        self.params = dict()        # url representatie voor gesl/disc/lcat/makl

    def get_arg(self, arg_name):
        """ Kijk of urlconf een specifieke parameter uit de url doorgegeven heeft aan deze view.
            Elke parameter heeft een eigen vertaaltabel van/naar url tekst.

            Geeft terug: valide parameter waarde, beschrijvende tekst
                         of None, None als de parameter niet aanwezig was

            Exceptie Resolved404 als een niet ondersteune parameter waarde in de url stond

            Voorbeeld: arg_name='makl'; parameter 'makl'='recurve'
                       --> retourneert 'R', 'Recurve'
        """
        url2sel = IndivRecord.url2sel4arg[arg_name]     # specifieke url vertaaltabel voor deze parameter
        try:
            url_part = self.kwargs[arg_name]
        except KeyError:
            pass        # parameter was niet aanwezig
        else:
            try:
                sel = url2sel[url_part]                         # kijk of het een ondersteunde url tekst is
                sel2str = IndivRecord.sel2str4arg[arg_name]     # zoek de beschrijvende tekst erbij
                return sel, sel2str[sel]
            except KeyError:
                # niet ondersteunde url tekst --> geef een foutmelding
                raise Resolver404()
        # de url parameter was niet aanwezig
        return None, None

    def set_sel(self):
        """Deze view wordt gebruikt voor meerdere url patronen, dus het aantal parameters varieert.
           Pas een aantal object variabelen aan voor de doorgegeven parameters.
        """
        self.sel_gesl, self.gesl_str = self.get_arg('gesl')
        self.sel_disc, self.disc_str = self.get_arg('disc')
        self.sel_lcat, self.lcat_str = self.get_arg('lcat')
        self.sel_makl, self.makl_str = self.get_arg('makl')

    def set_urls(self):
        """Vertaal de opgegeven filter delen naar hun url representatie en sla deze op in self.params
        """
        if self.sel_gesl:
            self.params['gesl'] = IndivRecord.gesl2url[self.sel_gesl]
        if self.sel_disc:
            self.params['disc'] = IndivRecord.disc2url[self.sel_disc]
        if self.sel_lcat:
            self.params['lcat'] = IndivRecord.lcat2url[self.sel_lcat]
        if self.sel_makl:
            self.params['makl'] = IndivRecord.makl2url[self.sel_makl]

    def make_items(self, objs, arg, url_name, keys):
        """ Deze functie voegt een aantal filter opties toe aan de objects list die aan de template gegeven wordt.
            De keuzes zijn hard-coded en komen uit het model.
            Input:
                objs: list waar de objecten aan toegevoegd kunnen worden
                arg: 'gesl', 'disc', 'lcat' of 'makl'
                url_name: moet een 'name' matchen in de urlconf, voor de reverse-lookup
                keys: de parameters om door te geven aan de reverse-lookup. De waarden worden uit self.params gehaald.
        """
        sel2str = IndivRecord.sel2str4arg[arg]
        sel2url = IndivRecord.sel2url4arg[arg]
        for sel, sel_str in sel2str.items():
            self.params[arg] = sel2url[sel]
            sub_params = { k: self.params[k] for k in keys}
            obj = SelObject()
            obj.sel_url = reverse(url_name, kwargs=sub_params)
            obj.sel_str = sel_str
            objs.append(obj)
        # for


class RecordsIndivZoom1234View(RecordsIndivZoomBaseView):
    """ Deze view helpt om in te zoomen op een subset van de records aan de hand van 4 vaste filters.
        Er zijn 4 filters: geslacht, discipline, leeftijdscategorie, materiaalklasse (in die volgordee)
        Er wordt een keuzelijst getoont voor het eerstvolgende nog niet aanwezige filter.
        Als alle filters aanwezig zijn gebruikt de url redirector RecordsIndivView.
    """
    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_INDIV_ZOOM1234

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        self.set_sel()
        self.set_urls()

        # decide the selection options to show
        objs = list()
        if not self.sel_gesl:
            self.make_items(objs, 'gesl', 'Records:indiv-g', ('gesl',))
        elif not self.sel_disc:
            self.make_items(objs, 'disc', 'Records:indiv-gd', ('gesl', 'disc'))
        elif not self.sel_lcat:
            self.make_items(objs, 'lcat', 'Records:indiv-gdl', ('gesl', 'disc', 'lcat'))
        elif not self.sel_makl:
            self.make_items(objs, 'makl', 'Records:indiv-gdlm', ('gesl', 'disc', 'lcat', 'makl'))
        # else:  alle 4 de selectiecriteria aanwezig kan niet (urlconf pakt dan RecordsIndivZoom5View)
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='records')
        return context


class RecordsIndivZoom5View(RecordsIndivZoomBaseView):
    """ Deze wordt gebruikt voor het 5e filter: het soort record.
        Voor alle soorten records die bestaan (onder de 4 gekozen filters).
    """
    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_INDIV_ZOOM5

    @staticmethod
    def set_url_specifiek(obj):
        """ Deze functie voegt een URL toe aan een object, voor gebruik in de template. """
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr, 'discipline': obj.discipline})

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        self.set_sel()
        self.set_urls()

        # vind de verschillende afstanden waarop records bestaan
        soorten = IndivRecord.objects.filter(
                            geslacht=self.sel_gesl,
                            discipline=self.sel_disc,
                            leeftijdscategorie=self.sel_lcat,
                            materiaalklasse=self.sel_makl).\
                                    distinct('soort_record').\
                                    order_by('-soort_record').\
                                    values_list('soort_record', flat=True)

        # voor elk van de afstandard (soort records) zoek het meest recente (dus beste) record op
        objs = list()
        for soort in soorten:
            best = IndivRecord.objects.filter(
                            geslacht=self.sel_gesl,
                            discipline=self.sel_disc,
                            leeftijdscategorie=self.sel_lcat,
                            materiaalklasse=self.sel_makl,
                            soort_record=soort).\
                                    order_by('-datum')[0:0+1]
            objs.extend(best)
        # for

        # voeg een url toe aan elk object
        for obj in objs:
            self.set_url_specifiek(obj)
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['discipline'] = self.disc_str
        context['geslacht'] = self.gesl_str
        context['materiaalklasse'] = self.makl_str
        context['leeftijdscategorie'] = self.lcat_str
        menu_dynamics(self.request, context, actief='records')
        return context


class RecordsIndivSpecifiekView(ListView):
    """ Deze view laat een specifiek record zijn aan de hand van het nummer
        Onder het record worden de relateerde records getoond.
    """
    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_SPECIFIEK

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gesl_str = self.disc_str = self.lcat_str = self.makl_str = ''
        self.params = dict()
        self.spec = None

    @staticmethod
    def set_url_specifiek(obj):
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr, 'discipline': obj.discipline})

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        volg_nr = self.kwargs['nummer']     # parameter guaranteed by urlconf
        discipline = self.kwargs['discipline']

        # zoek het specifieke record erbij
        try:
            spec = IndivRecord.objects.get(volg_nr=volg_nr, discipline=discipline)
        except ObjectDoesNotExist:
            # dat was geen valide record nummer
            # TODO: consider to make more user friendly
            raise Resolver404()

        # voeg informatie toe voor de template
        spec.gesl_str = IndivRecord.gesl2str[spec.geslacht]
        spec.disc_str = IndivRecord.disc2str[spec.discipline]
        spec.lcat_str = IndivRecord.lcat2str[spec.leeftijdscategorie]
        spec.makl_str = IndivRecord.makl2str[spec.materiaalklasse]

        spec.op_pagina = "specifiek record: %s-%s" % (discipline, volg_nr)

        self.spec = spec

        # stel de url parameters vast voor de broodkruimel urls
        self.params['gesl'] = IndivRecord.gesl2url[spec.geslacht]
        self.params['disc'] = IndivRecord.disc2url[spec.discipline]
        self.params['lcat'] = IndivRecord.lcat2url[spec.leeftijdscategorie]
        self.params['makl'] = IndivRecord.makl2url[spec.materiaalklasse]

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

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['obj_record'] = self.spec
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
        self.get_zoekterm = self.form.cleaned_data['zoekterm']

        if self.get_zoekterm:
            zoekterm = self.get_zoekterm

            try:
                filter_nr = int(zoekterm)
                filter_is_nr = True
            except ValueError:
                filter_is_nr = False

            if filter_is_nr and len(str(filter_nr)) == 6:
                # zoek het NHB lid met dit nummber
                try:
                    lid = NhbLid.objects.get(nhb_nr=filter_nr)
                except NhbLid.DoesNotExist:
                    # geen lid met dit nummer
                    # of slecht getal
                    pass
                else:
                    # zoek alle records van dit lid
                    return IndivRecord.objects.filter(nhb_lid=lid)
            else:
                return IndivRecord.objects.filter(
                                Q(soort_record__icontains=zoekterm) |
                                Q(naam__icontains=zoekterm) |
                                Q(plaats__icontains=zoekterm) |
                                Q(land__icontains=zoekterm)).order_by('-datum', 'soort_record')[:settings.RECORDS_MAX_ZOEKRESULTATEN]

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

# end of file
