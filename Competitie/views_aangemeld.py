# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import Resolver404, reverse
from django.views.generic import TemplateView
from django.utils import timezone
from Plein.menu import menu_dynamics
from NhbStructuur.models import NhbRayon, NhbRegio
from .models import LAAG_REGIO, Competitie, RegioCompetitieSchutterBoog


TEMPLATE_COMPETITIE_AANGEMELD_REGIO = 'competitie/lijst-aangemeld-regio.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


def maak_regiocomp_zoom_knoppen(context, comp_pk, rayon=None, regio=None):

    """ Maak de zoom knoppen structuur voor de regiocompetitie deelnemers lijst """

    if rayon != regio:
        context['zoom_alles_url'] = reverse('Competitie:lijst-regiocomp-alles', kwargs={'comp_pk': comp_pk})

    regios = (NhbRegio
              .objects
              .select_related('rayon')
              .filter(is_administratief=False))

    rayons = NhbRayon.objects.all()

    context['zoom_rayons'] = list()
    for obj in rayons:
        context['zoom_rayons'].append(obj)

        obj.title_str = 'Rayon %s' % obj.rayon_nr
        if obj != rayon:
            obj.zoom_url = reverse('Competitie:lijst-regiocomp-rayon',
                                   kwargs={'comp_pk': comp_pk, 'rayon_pk': obj.pk})

        obj.regios = list()
        for obj2 in regios:
            if obj2.rayon == obj:
                obj.regios.append(obj2)
                obj2.title_str = 'Regio %s' % obj2.regio_nr
                if obj2 != regio:
                    obj2.zoom_url = reverse('Competitie:lijst-regiocomp-regio',
                                            kwargs={'comp_pk': comp_pk, 'regio_pk': obj2.pk})
    # for


class LijstAangemeldRegiocompAllesView(TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    # TODO: toegang begrenzen tot <tbd> (mbv UserPassesTestMixin)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']
        try:
            context['competitie'] = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        context['object_list'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .select_related('klasse', 'klasse__indiv',
                                                  'deelcompetitie', 'deelcompetitie__nhb_regio',
                                                  'schutterboog', 'schutterboog__nhblid',
                                                  'schutterboog__nhblid__bij_vereniging')
                                  .filter(deelcompetitie__competitie=comp_pk,
                                          deelcompetitie__laag=LAAG_REGIO)
                                  .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in context['object_list']:
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        context['inhoud'] = 'landelijk'
        maak_regiocomp_zoom_knoppen(context, comp_pk)

        menu_dynamics(self.request, context, actief='competitie')
        return context


class LijstAangemeldRegiocompRayonView(TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    # TODO: toegang begrenzen tot <tbd> (mbv UserPassesTestMixin)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']
        try:
            context['competitie'] = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        rayon_pk = kwargs['rayon_pk']
        try:
            rayon = NhbRayon.objects.get(pk=rayon_pk)
        except NhbRayon.DoesNotExist:
            raise Resolver404()

        context['object_list'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .select_related('klasse', 'klasse__indiv',
                                                  'deelcompetitie', 'deelcompetitie__nhb_regio__rayon',
                                                  'schutterboog', 'schutterboog__nhblid', 'schutterboog__nhblid__bij_vereniging')
                                  .filter(deelcompetitie__competitie=comp_pk,
                                          deelcompetitie__laag=LAAG_REGIO,
                                          deelcompetitie__nhb_regio__rayon=rayon)
                                  .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in context['object_list']:
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        context['inhoud'] = 'in ' + str(rayon)
        maak_regiocomp_zoom_knoppen(context, comp_pk, rayon=rayon)

        menu_dynamics(self.request, context, actief='competitie')
        return context


class LijstAangemeldRegiocompRegioView(TemplateView):

    """ Toon een lijst van SchutterBoog die aangemeld zijn voor de regiocompetitie """

    template_name = TEMPLATE_COMPETITIE_AANGEMELD_REGIO

    # TODO: toegang begrenzen tot <tbd> (mbv UserPassesTestMixin)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        comp_pk = kwargs['comp_pk']
        try:
            context['competitie'] = Competitie.objects.get(pk=comp_pk)
        except Competitie.DoesNotExist:
            raise Resolver404()

        regio_pk = kwargs['regio_pk']
        try:
            regio = (NhbRegio
                     .objects
                     .select_related('rayon')
                     .get(pk=regio_pk))
        except NhbRegio.DoesNotExist:
            raise Resolver404()

        context['object_list'] = (RegioCompetitieSchutterBoog
                                  .objects
                                  .select_related('klasse', 'klasse__indiv', 'deelcompetitie', 'schutterboog', 'schutterboog__nhblid', 'schutterboog__nhblid__bij_vereniging')
                                  .filter(deelcompetitie__competitie=comp_pk,
                                          deelcompetitie__laag=LAAG_REGIO,
                                          deelcompetitie__nhb_regio=regio)
                                  .order_by('klasse__indiv__volgorde', 'aanvangsgemiddelde'))

        volgorde = -1
        for obj in context['object_list']:
            obj.team_ja_nee = JA_NEE[obj.inschrijf_voorkeur_team]
            if volgorde != obj.klasse.indiv.volgorde:
                obj.nieuwe_klasse = True
                volgorde = obj.klasse.indiv.volgorde
        # for

        context['inhoud'] = 'in ' + str(regio)
        maak_regiocomp_zoom_knoppen(context, comp_pk, regio=regio)

        menu_dynamics(self.request, context, actief='competitie')
        return context


# end of file
