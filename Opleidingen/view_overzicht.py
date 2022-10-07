# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from Plein.menu import menu_dynamics


TEMPLATE_OPLEIDINGEN_OVERZICHT = 'opleidingen/overzicht.dtl'


class OpleidingenOverzichtView(TemplateView):

    template_name = TEMPLATE_OPLEIDINGEN_OVERZICHT

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (None, 'Opleidingen'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
