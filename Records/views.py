# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import Resolver404, reverse
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from Plein.kruimels import make_context_broodkruimels
from NhbStructuur.models import NhbLid
from .models import IndivRecord
from .forms import ZoekForm

TEMPLATE_RECORDS_OVERZICHT = 'records/records_overzicht.dtl'
TEMPLATE_RECORDS_SPECIFIEK = 'records/records_specifiek.dtl'
TEMPLATE_RECORDS_INDIV_ZOOM1234 = 'records/records_indiv_zoom1234.dtl'
TEMPLATE_RECORDS_INDIV_ZOOM5 = 'records/records_indiv_zoom5.dtl'
TEMPLATE_RECORDS_ZOEK = 'records/records_zoek.dtl'


class RecordsOverzichtView(ListView):
    """ This class just provides broodkruimels for the otherwise static template. """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_OVERZICHT

    @staticmethod
    def set_url_specifiek(obj):
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr})

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        objs = IndivRecord.objects.all().order_by('-volg_nr')[:5]
        for obj in objs:
            self.set_url_specifiek(obj)
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        make_context_broodkruimels(context, 'Plein:plein', 'Records:overzicht')
        return context


class SelObject(object):
    """ Simple objects for giving to the template """

    def __init__(self):
        self.sel_url = self.sel_str = ""


def make_record_kruimels(params, sel_gesl, sel_disc, sel_lcat, sel_makl, rec_nr, gesl_str, disc_str, lcat_str, makl_str, type_str):

    kruimels = ['Plein:plein', 'Records:overzicht', 'Records:indiv']

    # url om geslacht te kiezen (0 filters)
    url_gesl = reverse('Records:indiv')

    if sel_gesl:
        # geslacht is gekozen
        # als je deze kruimel volgt wil je het geslacht weer in kunnen stellen
        kruimels.append((gesl_str, url_gesl))

        # url om discipline te kiezen (1 filter)
        sub_params = {k: params[k] for k in ('gesl',)}
        url_disc = reverse('Records:indiv-g', kwargs=sub_params)

        if sel_disc:
            # discipline is gekozen
            # als je deze kruimel volgt wil je een andere discipline kunnen kiezen
            kruimels.append((disc_str, url_disc))

            # url om leeftijdscategorie te kiezen (2 filters)
            sub_params = {k: params[k] for k in ('gesl', 'disc')}
            url_lcat = reverse('Records:indiv-gd', kwargs=sub_params)

            if sel_lcat:
                # leeftijdscategorie is gekozen
                # als je deze kruimel volgt wil je een andere leeftijdscategorie kunnen kiezen
                kruimels.append((lcat_str, url_lcat))

                # url om materiaalklasse te kunnen kiezen (3 filters)
                sub_params = {k: params[k] for k in ('gesl', 'disc', 'lcat')}
                url_makl = reverse('Records:indiv-gdl', kwargs=sub_params)

                if sel_makl:
                    # materiaalklasse is gekozen
                    # als je deze kruimel volgt wil je een andere materiaalklasse kunnen kiezen
                    kruimels.append((makl_str, url_makl))

                    # url om een het soort-record te kunnen kiezen (4 filters)
                    url_soortrec = reverse('Records:indiv-gdlm', kwargs=params)

                    if rec_nr:
                        # kruimel voor het specifieke record
                        # als je deze kruimel volgt wil je een andere soort-record kunnen kiezen
                        kruimels.append((type_str, url_soortrec))

    return kruimels


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
        self.kruimels = list()
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
           Voer de aanwezige filter delen toe aan self.kruimels
        """
        if self.sel_gesl:
            self.params['gesl'] = IndivRecord.gesl2url[self.sel_gesl]
        if self.sel_disc:
            self.params['disc'] = IndivRecord.disc2url[self.sel_disc]
        if self.sel_lcat:
            self.params['lcat'] = IndivRecord.lcat2url[self.sel_lcat]
        if self.sel_makl:
            self.params['makl'] = IndivRecord.makl2url[self.sel_makl]

        self.kruimels = make_record_kruimels(
                                self.params,
                                self.sel_gesl, self.sel_disc, self.sel_lcat, self.sel_makl,
                                None,       # rec_nr
                                self.gesl_str, self.disc_str, self.lcat_str, self.makl_str, '')

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
        make_context_broodkruimels(context, *self.kruimels)
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
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr})

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
        make_context_broodkruimels(context, *self.kruimels)
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

    @staticmethod
    def set_url_specifiek(obj):
        obj.url = reverse('Records:specifiek', kwargs={'nummer': obj.volg_nr})

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        volg_nr = self.kwargs['nummer']     # parameter guaranteed by urlconf

        # zoek het specifieke record erbij
        specifiek = IndivRecord.objects.filter(volg_nr=volg_nr)
        if len(specifiek) == 0:
            # dat was geen valide record nummer
            raise Resolver404()

        spec = specifiek[0]      # het volg_nr is nog niet altijd uniek, dus kies de eerste
        # voeg informatie toe voor de template
        spec.gesl_str = IndivRecord.gesl2str[spec.geslacht]
        spec.disc_str = IndivRecord.disc2str[spec.discipline]
        spec.lcat_str = IndivRecord.lcat2str[spec.leeftijdscategorie]
        if spec.materiaalklasse == 'O':
            spec.makl_str = spec.materiaalklasse_overig     # beschrijving voor de overige klasse
        else:
            spec.makl_str = IndivRecord.makl2str[spec.materiaalklasse]

        # kopieer de strings voor de kruimels
        self.gesl_str, self.disc_str, self.lcat_str, self.makl_str, self.type_str = spec.gesl_str, spec.disc_str, spec.lcat_str, spec.makl_str, spec.soort_record

        # stel de url parameters vast voor de broodkruimel urls
        self.params['gesl'] = IndivRecord.gesl2url[spec.geslacht]
        self.params['disc'] = IndivRecord.disc2url[spec.discipline]
        self.params['lcat'] = IndivRecord.lcat2url[spec.leeftijdscategorie]
        self.params['makl'] = IndivRecord.makl2url[spec.materiaalklasse]

        # zoek de andere records die hier bij horen, aflopend gesorteerd op datum
        # hier zit ook het record zelf bij
        hist = IndivRecord.objects.filter(
                        geslacht=spec.geslacht,
                        discipline=spec.discipline,
                        leeftijdscategorie=spec.leeftijdscategorie,
                        materiaalklasse=spec.materiaalklasse,
                        soort_record=spec.soort_record).order_by('-datum')

        objs = list()
        objs.append(spec)
        objs.extend(hist)
        for obj in hist:
            obj.is_specifieke_record = (obj.volg_nr == spec.volg_nr)
            self.set_url_specifiek(obj)
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # kruimel voor het specifieke record
        rec_nr = self.kwargs['nummer']

        kruimels = make_record_kruimels(
                                self.params,
                                1, 1, 1, 1,
                                rec_nr,
                                self.gesl_str, self.disc_str, self.lcat_str, self.makl_str,
                                self.type_str)

        make_context_broodkruimels(context, *kruimels)
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

        # haal de GET parameters uit de request
        self.form = ZoekForm(self.request.GET)

        if self.form.is_valid():
            self.get_zoekterm = self.form.cleaned_data['zoekterm']

            if self.get_zoekterm:
                try:
                    filter_nr = int(self.get_zoekterm)
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
                                    Q(soort_record__icontains=self.get_zoekterm) |
                                    Q(naam__icontains=self.get_zoekterm) |
                                    Q(plaats__icontains=self.get_zoekterm) |
                                    Q(land__icontains=self.get_zoekterm)).order_by('-datum')
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        make_context_broodkruimels(
            context,
            'Plein:plein',
            'Records:overzicht',
            'Records:zoek')
        return context

# end of file
