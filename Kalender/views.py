# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import ListView
from Plein.menu import menu_dynamics

TEMPLATE_KALENDER_OVERZICHT = 'kalender/overzicht.dtl'


class KalenderOverzichtView(ListView):

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_OVERZICHT

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        menu_dynamics(self.request, context, 'kalender')
        return context


# end of file
