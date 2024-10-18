# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.conf import settings
from django.views.generic import ListView, TemplateView
from django.templatetags.static import static
from Records.definities import (disc2str, disc2url, url2disc,
                                gesl2str, gesl2url, url2gesl,
                                makl2str, makl2url, url2makl,
                                lcat2str, lcat2url, url2lcat)
from Records.models import IndivRecord, BesteIndivRecords
from types import SimpleNamespace


TEMPLATE_RECORDS_VERBETERBAAR_KIES_DISC = 'records/verbeterbaar_kies_disc.dtl'
TEMPLATE_RECORDS_VERBETERBAAR_DISCIPLINE = 'records/verbeterbaar.dtl'


DISCIPLINE_TO_ICON = {
    'OD': static('plein/badge_discipline_outdoor.png'),
    '18': static('plein/badge_discipline_indoor.png'),
    '25': static('plein/badge_discipline_25m1p.png')
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
            obj.url = reverse('Records:indiv-verbeterbaar-disc', kwargs={'disc': url_disc,
                                                                         'makl': 'alle',
                                                                         'lcat': 'alle',
                                                                         'gesl': 'alle'})
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (None, 'Verbeterbaar')
        )

        return context


class RecordsVerbeterbaarInDiscipline(TemplateView):

    """ Deze view laat de gebruiker de lijst van verbeterbare NL records zien binnen een discipline """

    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_VERBETERBAAR_DISCIPLINE

    @staticmethod
    def _maak_filter_makl(context, url_makl):
        gekozen_makl = ''
        if url_makl != 'alle':
            try:
                gekozen_makl = url2makl[url_makl]
            except KeyError:
                raise Http404('Slechte parameter')

        context['makl_filter'] = list()
        obj = SimpleNamespace(
                    opt_text='Alle',
                    sel='makl_alle',
                    selected=(gekozen_makl == ''),
                    url_part='alle')
        context['makl_filter'].append(obj)

        for makl_key, makl_value in makl2str.items():
            obj = SimpleNamespace(
                        opt_text=makl_value,
                        sel="makl_"+makl_key,
                        selected=(gekozen_makl == makl_key),
                        url_part=makl2url[makl_key])
            context['makl_filter'].append(obj)
        # for

        return gekozen_makl

    @staticmethod
    def _maak_filter_lcat(context, url_lcat, discipline):
        gekozen_lcat = ''
        if url_lcat != 'alle':
            try:
                gekozen_lcat = url2lcat[url_lcat]
            except KeyError:
                raise Http404('Slechte parameter')

        context['lcat_filter'] = list()
        obj = SimpleNamespace(
                    opt_text='Alle',
                    sel='lcat_alle',
                    selected=(gekozen_lcat == ''),
                    url_part='alle')
        context['lcat_filter'].append(obj)

        for lcat_key, lcat_value in lcat2str.items():

            # de 'gecombineerd (para)' optie alleen tonen voor outdoor
            if lcat_key == 'U' and discipline != 'OD':
                continue

            obj = SimpleNamespace(
                        opt_text=lcat_value,
                        sel='lcat_'+lcat_key,
                        selected=(gekozen_lcat == lcat_key),
                        url_part=lcat2url[lcat_key])
            context['lcat_filter'].append(obj)
        # for

        return gekozen_lcat

    @staticmethod
    def _maak_filter_gesl(context, url_gesl):
        gekozen_gesl = ''
        if url_gesl != 'alle':
            try:
                gekozen_gesl = url2gesl[url_gesl]
            except KeyError:
                raise Http404('Slechte parameter')

        context['gesl_filter'] = list()
        obj = SimpleNamespace(
                    opt_text='Alle',
                    sel='gesl_alle',
                    selected=(gekozen_gesl == ''),
                    url_part='alle')
        context['gesl_filter'].append(obj)

        for gesl_key, gesl_value in gesl2str.items():
            obj = SimpleNamespace(
                    opt_text=gesl_value,
                    sel='gesl_' + gesl_key,
                    selected=(gekozen_gesl == gesl_key),
                    url_part=gesl2url[gesl_key])
            context['gesl_filter'].append(obj)
        # for

        return gekozen_gesl

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        url_disc = self.kwargs['disc']
        try:
            discipline = url2disc[url_disc]
        except KeyError:
            raise Http404('Slechte parameter')

        context['beschrijving'] = disc2str[discipline]      # komt boven in de pagina

        gekozen_makl = self._maak_filter_makl(context, self.kwargs['makl'])
        gekozen_lcat = self._maak_filter_lcat(context, self.kwargs['lcat'], discipline)
        gekozen_gesl = self._maak_filter_gesl(context, self.kwargs['gesl'])

        context['url_filters'] = reverse('Records:indiv-verbeterbaar-disc',
                                         kwargs={'disc': url_disc,
                                                 'makl': '~1',
                                                 'lcat': '~2',
                                                 'gesl': '~3'})

        context['is_alles'] = (gekozen_makl == gekozen_gesl == gekozen_lcat)
        context['toon_para_kolom'] = False

        qset = (BesteIndivRecords
                .objects
                .filter(discipline=discipline)
                .exclude(beste=None)
                .select_related('beste')
                .order_by('volgorde'))

        if gekozen_makl:
            qset = qset.filter(materiaalklasse=gekozen_makl)

        if gekozen_lcat:
            qset = qset.filter(leeftijdscategorie=gekozen_lcat)

        if gekozen_gesl:
            qset = qset.filter(geslacht=gekozen_gesl)

        context['object_list'] = qset

        for obj in qset:
            obj.geslacht_str = gesl2str[obj.geslacht]
            obj.materiaalklasse_str = makl2str[obj.materiaalklasse]
            obj.leeftijdscategorie_str = lcat2str[obj.leeftijdscategorie]

            obj.url_details = reverse('Records:specifiek', kwargs={'discipline': obj.discipline,
                                                                   'nummer': obj.beste.volg_nr})

            if obj.para_klasse:
                context['toon_para_kolom'] = True
        # for

        aantal_gekozen = len(qset)
        context['lege_lijst'] = (aantal_gekozen == 0)
        context['aantal_regels'] = aantal_gekozen + 2

        context['url_spelden_procedures'] = settings.URL_SPELDEN_PROCEDURES
        context['url_record_formulier'] = settings.URL_RECORD_AANVRAAGFORMULIER

        context['robots'] = 'nofollow'   # prevent crawling filter result pages

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (reverse('Records:indiv-verbeterbaar'), 'Verbeterbaar'),
            (None, context['beschrijving'])
        )

        return context

# end of file
