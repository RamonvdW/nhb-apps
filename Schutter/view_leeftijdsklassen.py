# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from .leeftijdsklassen import get_sessionvars_leeftijdsklassen
import logging


TEMPLATE_LEEFTIJDSKLASSEN = 'schutter/leeftijdsklassen.dtl'

my_logger = logging.getLogger('NHBApps.Schutter')


class LeeftijdsklassenView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol == Rollen.ROL_SCHUTTER

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(self.request)
        context['plein_is_jonge_schutter'] = is_jong
        context['plein_huidige_jaar'] = huidige_jaar
        context['plein_leeftijd'] = leeftijd
        context['plein_wlst'] = wlst
        context['plein_clst'] = clst

        menu_dynamics(self.request, context)
        return context


# end of file
