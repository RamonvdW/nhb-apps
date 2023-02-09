# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from Plein.menu import menu_dynamics
from Records.definities import (url2gesl, url2disc, url2lcat, url2makl, url2verb, url2para,
                                gesl2url, disc2url, lcat2url, makl2url, verb2url, para2url,
                                gesl2str, disc2str, lcat2str, makl2str, verb2str,
                                lcat2short)
from Records.models import IndivRecord
from types import SimpleNamespace


TEMPLATE_RECORDS_INDIV = 'records/records_indiv.dtl'


class RecordsIndivView(TemplateView):
    """ Deze view laat een specifiek record zijn aan de hand van het nummer
        Onder het record worden de relateerde records getoond.
    """
    # class variables shared by all instances
    template_name = TEMPLATE_RECORDS_INDIV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gesl_str = self.disc_str = self.lcat_str = self.makl_str = ''
        self.params = dict()
        self.spec = None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            gesl = url2gesl[self.kwargs['gesl']]
            disc = url2disc[self.kwargs['disc']]
            lcat = url2lcat[self.kwargs['lcat']]
            makl = url2makl[self.kwargs['makl']]
            verb = url2verb[self.kwargs['verb']]
            para = url2para[self.kwargs['para']]
            nr = int(self.kwargs['nummer'])
        except KeyError:
            # initieel zijn er geen parameters
            # ook bij gerommel terugvallen op initieel
            gesl = 'M'
            disc = 'OD'
            lcat = 'S'
            makl = 'R'
            verb = True
            para = ''
            nr = 0

        # in geval van para kijken we niet naar de lcat of disc
        if para:
            lcat = 'U'
            # para records alleen voor Outdoor en Indoor, dus wissel weg van 25m1pijl indien gekozen
            if disc == '25':
                disc = '18'
        else:
            if lcat == 'U':
                lcat = 'S'

        # voorbereiden voor alle reverse() aanroepen
        gesl_url = gesl2url[gesl]
        disc_url = disc2url[disc]
        lcat_url = lcat2url[lcat]
        makl_url = makl2url[makl]
        para_url = para2url[para]

        # zoek alle records die aan de 4-tuple of 5-tuple voldoen
        # dit minimaliseert het aantal database verzoeken dat we moeten doen
        alle = (IndivRecord
                .objects
                .filter(discipline=disc,
                        geslacht=gesl,
                        leeftijdscategorie=lcat,
                        materiaalklasse=makl,
                        para_klasse=para)
                .order_by('soort_record',
                          'volg_nr'))           # niet functioneel, wel handig voor test

        heeft_niet_verb = False
        for obj in alle:
            if not obj.verbeterbaar:
                heeft_niet_verb = True
                break
        # for

        if heeft_niet_verb:
            alle = alle.filter(verbeterbaar=verb)
        else:
            verb = True

        verb_url = verb2url[verb]

        # haal de record soorten uit de volledige lijst
        soort_nieuwste = dict()     # ["soort_record"] = IndivRecord()
        nieuwste_record = None
        spec = None
        for obj in alle:
            try:
                if obj.datum > soort_nieuwste[obj.soort_record].datum:
                    soort_nieuwste[obj.soort_record] = obj
            except KeyError:
                soort_nieuwste[obj.soort_record] = obj

            if not nieuwste_record or obj.datum > nieuwste_record.datum:
                nieuwste_record = obj

            if obj.volg_nr == nr:
                spec = obj
        # for

        context['soorten'] = soorten = list()
        for soort_record, obj in soort_nieuwste.items():
            obj.url = reverse('Records:indiv-all',
                              kwargs={'gesl': gesl_url,
                                      'disc': disc_url,
                                      'lcat': lcat_url,
                                      'makl': makl_url,
                                      'verb': verb_url,
                                      'para': para_url,
                                      'nummer': obj.volg_nr})
            obj.sel = 'soort_%s' % obj.pk
            soorten.append(obj)
        # for

        if not spec:
            # speciaal geval: pak het nieuwste record
            spec = nieuwste_record

        context['obj_record'] = spec

        for obj in soorten:
            if spec.soort_record == obj.soort_record:
                # deze is "gekozen" en moet dus disabled worden
                obj.is_gekozen = True
        # for

        context['toon_soorten'] = (len(soorten) > 0)

        # zoek nu de records die bij dit filter passen, aflopend gesorteerd op datum
        # (deze zitten in 'alle' maar dit is eenvoudiger tegen geringe database kosten)
        if spec:
            objs = (IndivRecord
                    .objects
                    .filter(geslacht=gesl,
                            discipline=disc,
                            leeftijdscategorie=lcat,
                            materiaalklasse=makl,
                            soort_record=spec.soort_record,
                            para_klasse=spec.para_klasse)
                    .order_by('-datum'))

            for obj in objs:
                obj.is_specifieke_record = (obj.volg_nr == spec.volg_nr)
                obj.url = reverse('Records:indiv-all',
                                  kwargs={'gesl': gesl_url,
                                          'disc': disc_url,
                                          'lcat': lcat_url,
                                          'makl': makl_url,
                                          'verb': verb_url,
                                          'para': para_url,
                                          'nummer': obj.volg_nr})
            # for
        else:
            objs = list()

        context['object_list'] = objs
        context['op_pagina'] = 'records-indiv'

        if spec:
            # voeg informatie toe voor de template
            spec.gesl_str = gesl2str[spec.geslacht]
            spec.disc_str = disc2str[spec.discipline]
            spec.lcat_str = lcat2str[spec.leeftijdscategorie]
            spec.makl_str = makl2str[spec.materiaalklasse]

            spec.url_specifiek = reverse('Records:specifiek',
                                         kwargs={'discipline': disc,        # let op: niet disc_url
                                                 'nummer': spec.volg_nr})

            context['op_pagina'] += "_%s-%s" % (spec.discipline, spec.volg_nr)

        nummer = 0

        # vul de filters
        context['gesl_filters'] = opties = list()
        for afk, url in gesl2url.items():
            optie = SimpleNamespace()
            optie.beschrijving = gesl2str[afk]
            optie.sel = 'gesl_' + afk
            optie.zoom_url = reverse('Records:indiv-all',
                                     kwargs={'gesl': url,
                                             'disc': disc_url,
                                             'lcat': lcat_url,
                                             'makl': makl_url,
                                             'verb': verb_url,
                                             'para': para_url,
                                             'nummer': nummer})
            optie.selected = (afk == gesl)
            opties.append(optie)
        # for

        context['disc_filters'] = opties = list()
        for afk, url in disc2url.items():

            # Para records zijn alleen ondersteund bij de Outdoor en Indoor
            if para and afk not in ('OD', '18'):
                continue

            optie = SimpleNamespace()
            optie.beschrijving = disc2str[afk]
            if afk != disc:
                optie.zoom_url = reverse('Records:indiv-all',
                                         kwargs={'gesl': gesl_url,
                                                 'disc': url,
                                                 'lcat': lcat_url,
                                                 'makl': makl_url,
                                                 'verb': verb_url,
                                                 'para': para_url,
                                                 'nummer': nummer})
            opties.append(optie)
        # for

        if not para:
            context['show_lcat'] = True

            context['lcat_filters'] = opties = list()
            for afk, url in lcat2url.items():
                # Gecombineerd (U) is automatisch, dus geen knop voor tonen
                if afk == 'U':
                    continue

                optie = SimpleNamespace()
                optie.beschrijving = lcat2short[afk]
                optie.sel = 'lcat_' + afk
                optie.selected = (lcat == afk)
                optie.zoom_url = reverse('Records:indiv-all',
                                         kwargs={'gesl': gesl_url,
                                                 'disc': disc_url,
                                                 'lcat': url,
                                                 'makl': makl_url,
                                                 'verb': verb_url,
                                                 'para': para_url,
                                                 'nummer': nummer})
                opties.append(optie)
            # for

        context['makl_filters'] = opties = list()
        for afk, url in makl2url.items():
            optie = SimpleNamespace()
            optie.beschrijving = makl2str[afk]
            optie.sel = 'makl_' + afk
            optie.selected = (afk == makl)
            optie.zoom_url = reverse('Records:indiv-all',
                                     kwargs={'gesl': gesl_url,
                                             'disc': disc_url,
                                             'lcat': lcat_url,
                                             'makl': url,
                                             'verb': verb_url,
                                             'para': para_url,
                                             'nummer': nummer})
            opties.append(optie)
        # for

        if heeft_niet_verb:
            context['toon_verb'] = True

            context['verb_filters'] = opties = list()
            for afk, url in verb2url.items():
                optie = SimpleNamespace()
                optie.beschrijving = verb2str[afk]
                optie.sel = 'verb_' + str(url)
                optie.selected = (verb == afk)
                optie.zoom_url = reverse('Records:indiv-all',
                                         kwargs={'gesl': gesl_url,
                                                 'disc': disc_url,
                                                 'lcat': lcat_url,
                                                 'makl': makl_url,
                                                 'verb': url,
                                                 'para': para_url,
                                                 'nummer': nummer})
                opties.append(optie)
            # for

        context['para_filters'] = opties = list()
        for afk, url in para2url.items():
            if afk == '':
                continue

            optie = SimpleNamespace()
            optie.beschrijving = afk
            optie.sel = 'para_' + afk
            optie.selected = (afk == para)
            optie.zoom_url = reverse('Records:indiv-all',
                                     kwargs={'gesl': gesl_url,
                                             'disc': disc_url,
                                             'lcat': lcat_url,
                                             'makl': makl_url,
                                             'verb': verb_url,
                                             'para': url,
                                             'nummer': nummer})
            opties.append(optie)
        # for

        # voeg de 'niet-para' knop toe
        optie = SimpleNamespace()
        optie.beschrijving = 'Niet-para'
        optie.sel = 'para_niet'
        optie.selected = (para == '')
        optie.zoom_url = reverse('Records:indiv-all',
                                 kwargs={'gesl': gesl_url,
                                         'disc': disc_url,
                                         'lcat': lcat_url,
                                         'makl': makl_url,
                                         'verb': verb_url,
                                         'para': para2url[''],
                                         'nummer': nummer})
        opties.insert(0, optie)

        context['kruimels'] = (
            (reverse('Records:overzicht'), 'Records'),
            (None, 'Filteren')
        )
        menu_dynamics(self.request, context)
        return context

# end of file
