# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from BasisTypen.definities import GESLACHT_VROUW
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Spelden.definities import (SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR, SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_VELD, SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
                                SPELD_CATEGORIE_WA_ARROWHEAD)
from Spelden.models import SpeldScore
from Spelden.operations import get_hall_of_fame, tel_hall_of_fame


TEMPLATE_PRESTATIESPELDEN_BEGIN = 'spelden/begin.dtl'
TEMPLATE_PRESTATIESPELDEN_HALL_OF_FAME = 'spelden/khsn-meesterspelden_hall-of-fame.dtl'
TEMPLATE_PRESTATIESPELDEN_MEESTERSPELDEN = 'spelden/khsn-meesterspelden.dtl'
TEMPLATE_PRESTATIESPELDEN_GRAADSPELDEN = 'spelden/khsn-graadspelden.dtl'
TEMPLATE_PRESTATIESPELDEN_TUSSENSPELDEN = 'spelden/khsn-tussenspelden.dtl'
TEMPLATE_PRESTATIESPELDEN_TARGET_AWARDS = 'spelden/wa-target-awards.dtl'
TEMPLATE_PRESTATIESPELDEN_STERSPELDEN = 'spelden/wa-sterspelden.dtl'
TEMPLATE_PRESTATIESPELDEN_ARROWHEAD = 'spelden/wa-arrowhead-spelden.dtl'


class BeginView(TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_BEGIN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (None, 'Spelden'),
        )

        return context


class HallOfFameView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_HALL_OF_FAME

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['leden_gm'], context['leden_ms'], context['leden_as'] = get_hall_of_fame()

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (reverse('Spelden:groep-meesterspelden'), 'Meesterspelden'),
            (None, 'Hall of Fame'),
        )
        return context


class MeesterspeldenView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_MEESTERSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['aantal_gm'], context['aantal_ms'], context['aantal_as'] = tel_hall_of_fame()

        context['url_hall_of_fame'] = reverse('Spelden:meesterspelden-hall-of-fame')

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Meesterspelden')
        )

        return context


class GraadspeldenView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_GRAADSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        qset = (SpeldScore
                .objects
                .filter(speld__categorie__in=(SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
                                              SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
                                              SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
                                              SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC))
                .select_related('speld',
                                'leeftijdsklasse')
                .order_by('speld__volgorde',
                          'leeftijdsklasse__wedstrijd_geslacht'))

        context['speld_scores'] = speld_scores = list()

        prev = None
        prev_discipline = ''
        for obj in qset:
            if obj.leeftijdsklasse.wedstrijd_geslacht == GESLACHT_VROUW:
                # toevoegen aan het vorige record
                prev.benodigde_score_vrouw = obj.benodigde_score
            else:
                if obj.speld.categorie == SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR:
                    obj.discipline = 'Indoor'
                elif obj.speld.categorie == SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR:
                    obj.discipline = 'Outdoor'
                elif obj.speld.categorie == SPELD_CATEGORIE_NL_GRAADSPELD_VELD:
                    obj.discipline = 'Veld'
                else:   # if SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC
                    obj.discipline = 'Short Metric'

                if obj.discipline != prev_discipline:
                    prev_discipline = obj.discipline
                    obj.break_discipline = True

                speld_scores.append(obj)
                prev = obj
        # for

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Graadspelden')
        )

        return context


class TussenspeldenView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_TUSSENSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        now = timezone.now()
        context['url_wedstrijdkalender'] = reverse('Kalender:simpel',
                                                   kwargs={'jaar_of_maand': 'jaar',
                                                           'maand': now.month,
                                                           'jaar': now.year})
        context['url_wedstrijdkalender'] += '?zoek=Outdoor'

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Tussenspelden')
        )

        return context


class TargetAwardsView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_TARGET_AWARDS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Target awards')
        )

        return context


class SterspeldenView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_STERSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Sterspelden')
        )

        return context


class ArrowheadView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_ARROWHEAD

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        qset = (SpeldScore
                .objects
                .filter(speld__categorie=SPELD_CATEGORIE_WA_ARROWHEAD)
                .select_related('leeftijdsklasse',
                                'boog_type',
                                'speld')
                .order_by('speld__volgorde',
                          'boog_type__volgorde',
                          'leeftijdsklasse__wedstrijd_geslacht'))

        context['ah_24'] = spelden = list()
        speld = None
        for obj in qset.filter(aantal_doelen=24):
            kleur = obj.speld.beschrijving.split()[-1]
            if speld is None or speld['kleur'] != kleur:
                speld = {
                    'kleur': kleur,
                    'R': dict(),
                    'C': dict(),
                    'BB': dict()
                }
                spelden.append(speld)

            scores = speld[obj.boog_type.afkorting]
            scores[obj.leeftijdsklasse.wedstrijd_geslacht] = obj.benodigde_score
        # for

        context['ah_48'] = spelden = list()
        speld = None
        for obj in qset.filter(aantal_doelen=48):
            kleur = obj.speld.beschrijving.split()[-1]
            if speld is None or speld['kleur'] != kleur:
                speld = {
                    'kleur': kleur,
                    'R': dict(),
                    'C': dict(),
                    'BB': dict()
                }
                spelden.append(speld)

            scores = speld[obj.boog_type.afkorting]
            scores[obj.leeftijdsklasse.wedstrijd_geslacht] = obj.benodigde_score
        # for

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Arrowhead spelden')
        )

        return context


# end of file
