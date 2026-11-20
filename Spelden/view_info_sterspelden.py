# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView

TEMPLATE_PRESTATIESPELDEN_STERSPELDEN = 'spelden/wa-sterspelden.dtl'


class SterspeldenView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_STERSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
        #     context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Sterspelden')
        )

        return context


# end of file
