# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Account.leeftijdsklassen import get_leeftijdsklassen
from Account.rol import rol_is_BKO
from Competitie.models import get_competitie_fase


TEMPLATE_PLEIN = 'plein/plein.dtl'
TEMPLATE_PRIVACY = 'plein/privacy.dtl'
TEMPLATE_LEEFTIJDSKLASSEN = 'plein/leeftijdsklassen.dtl'

JA_NEE = {False: 'Nee', True: 'Ja'}


def site_root_view(request):
    """ simpele Django view functie om vanaf de top-level site naar het Plein te gaan """
    return redirect('Plein:plein')


class PleinView(TemplateView):
    """ Django class-based view voor het Plein """

    # class variables shared by all instances
    template_name = TEMPLATE_PLEIN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(self.request)
        if huidige_jaar:
            context['plein_is_nhb_lid'] = True
            context['plein_toon_leeftijdsklassen'] = True
            context['plein_is_jonge_schutter'] = is_jong
            context['plein_huidige_jaar'] = huidige_jaar
            context['plein_leeftijd'] = leeftijd
            context['plein_wlst'] = wlst
            context['plein_clst'] = clst
        else:
            context['plein_toon_leeftijdsklassen'] = False
            context['plein_is_nhb_lid'] = False

        if rol_is_BKO(self.request):
            context['show_bko'] = True
            fase18, comp18 = get_competitie_fase('18')
            fase25, comp25 = get_competitie_fase('25')
            comp18.fase = fase18
            comp25.fase = fase25
            comp18.is_afgesloten_str = JA_NEE[comp18.is_afgesloten]
            comp25.is_afgesloten_str = JA_NEE[comp25.is_afgesloten]
            context['bko_comp18'] = comp18
            context['bko_comp25'] = comp25
            context['bko_kan_competitie_aanmaken'] = (fase18 == 'A' and fase25 == 'A')
            if not context['bko_kan_competitie_aanmaken']:
                context['bko_kan_klassegrenzen_instellen_18'] = (fase18 == 'A1')
                context['bko_kan_klassegrenzen_instellen_25'] = (fase25 == 'A1')

        menu_dynamics(self.request, context)
        return context


class PrivacyView(TemplateView):

    """ Django class-based view voor het Privacy bericht """

    # class variables shared by all instances
    template_name = TEMPLATE_PRIVACY

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='privacy')
        return context


class LeeftijdsklassenView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN
    login_url = '/account/login/'       # no reverse call

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(self.request)
        return (leeftijd is not None)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar, leeftijd, is_jong, wlst, clst = get_leeftijdsklassen(self.request)
        context['plein_is_jonge_schutter'] = is_jong
        context['plein_huidige_jaar'] = huidige_jaar
        context['plein_leeftijd'] = leeftijd
        context['plein_wlst'] = wlst
        context['plein_clst'] = clst

        menu_dynamics(self.request, context)
        return context


# end of file
