# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# from django.shortcuts import render
from django.views.generic import TemplateView
from django import forms
from Plein.kruimels import make_context_broodkruimels
from Plein.menu import menu_dynamics
from django.shortcuts import redirect

TEMPLATE_PLEIN = 'plein/plein.dtl'
TEMPLATE_PRIVACY = 'plein/privacy.dtl'


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


# end of file
