# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from django.shortcuts import render
from django.templatetags.static import static
from django.views.generic import TemplateView
from Account.models import get_account
from Bestel.operations.mandje import mandje_tel_inhoud
from Bestel.operations.mutaties import bestel_mutatieverzoek_webwinkel_keuze
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from types import SimpleNamespace


TEMPLATE_PRESTATIESPELDEN_BEGIN = 'spelden/begin.dtl'
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

        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (None, 'Spelden'),
        )

        return context


class GraadspeldenView(TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_GRAADSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Graadspelden')
        )

        return context


class TussenspeldenView(TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_TUSSENSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        now = timezone.now()
        context['url_wedstrijdkalender'] = reverse('Kalender:jaar',
                                                   kwargs={'maand': now.month,
                                                           'jaar': now.year,
                                                           'soort': 'khsn',
                                                           'bogen': 'alle'})
        context['url_wedstrijdkalender'] += '?zoek=Outdoor'

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Tussenspelden')
        )

        return context


class TargetAwardsView(TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_TARGET_AWARDS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Target awards')
        )

        return context


class SterspeldenView(TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_STERSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Sterspelden')
        )

        return context


class ArrowheadView(TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_ARROWHEAD

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if rol_get_huidige(self.request) == Rollen.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (reverse('Spelden:begin'), 'Spelden'),
            (None, 'Arrowhead spelden')
        )

        return context


# end of file
