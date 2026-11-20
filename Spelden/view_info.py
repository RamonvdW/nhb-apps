# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

TEMPLATE_PRESTATIESPELDEN_TUSSENSPELDEN = 'spelden/khsn-tussenspelden.dtl'


class TussenspeldenView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_TUSSENSPELDEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        context['url_wedstrijdkalender'] = reverse('Kalender:alles',
                                                   kwargs={'jaar_of_maand': 'jaar',
                                                           'jaar': now.year,
                                                           'maand': now.month,
                                                           'soort': 'wa-a',     # World Archery, A-status
                                                           'bogen': 'mijn',
                                                           'discipline': 'outdoor'})

        context['kruimels'] = (
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Tussenspelden')
        )

        return context


# end of file
