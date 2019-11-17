# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from Plein.menu import menu_dynamics
from Account.rol import Rollen, rol_get_huidige, rol_get_limiet, rol_activate, rol_mag_wisselen
from Account.leeftijdsklassen import get_leeftijdsklassen


TEMPLATE_PLEIN = 'plein/plein.dtl'
TEMPLATE_PRIVACY = 'plein/privacy.dtl'
TEMPLATE_WISSELVANROL = 'plein/wissel-van-rol.dtl'
TEMPLATE_LEEFTIJDSKLASSEN = 'plein/leeftijdsklassen.dtl'


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
            context['plein_toon_leeftijdsklassen'] = True
            context['plein_is_jonge_schutter'] = is_jong
            context['plein_huidige_jaar'] = huidige_jaar
            context['plein_leeftijd'] = leeftijd
            context['plein_wlst'] = wlst
            context['plein_clst'] = clst
        else:
            context['plein_toon_leeftijdsklassen'] = False

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


class WisselVanRolView(UserPassesTestMixin, ListView):

    """ Django class-based view om van rol te wisselen """

    # class variables shared by all instances
    template_name = TEMPLATE_WISSELVANROL

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_mag_wisselen(self.request)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        objs = list()

        rol = rol_get_limiet(self.request)

        if rol <= Rollen.ROL_IT:
            url = reverse('Plein:activeer-rol', kwargs={'rol': 'beheerder'})
            objs.append({ 'titel': 'IT beheerder', 'url': url})

        if rol <= Rollen.ROL_BKO:
            url = reverse('Plein:activeer-rol', kwargs={'rol': 'BKO'})
            objs.append({ 'titel': 'BK Organizator (BKO)', 'url': url})

        #if rol <= Rollen.ROL_RKO:
        #    objs.append('RKO rayon X')      # TODO: voor specifieke rayons

        #if rol <= Rollen.ROL_RCL:
        #    objs.append('RCL regio Y')      # TODO: voor specifieke regios

        #if rol <= Rollen.ROL_CWZ:
        #    objs.append('CWZ vereniging Z') # TODO: voor specifieke verenigingen

        if rol <= Rollen.ROL_SCHUTTER:
            url = reverse('Plein:activeer-rol', kwargs={'rol': 'schutter'})
            objs.append({ 'titel': 'Schutter', 'url': url})

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='wissel-van-rol')
        return context


class ActiveerRolView(UserPassesTestMixin, View):
    """ Django class-based view om een andere rol aan te nemen """

    # class variables shared by all instances

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_mag_wisselen(self.request)

    def get(self, request, *args, **kwargs):
        rol_activate(request, kwargs['rol'])
        return redirect('Plein:plein')


class LeeftijdsklassenView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
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
