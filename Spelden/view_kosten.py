# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.views.generic import TemplateView
from Betaal.format import format_bedrag_euro
from decimal import Decimal

TEMPLATE_PRESTATIESPELDEN_KOSTEN = 'spelden/kosten.dtl'


class KostenView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_KOSTEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['prijs_wa_speld'] = format_bedrag_euro(Decimal(settings.SPELD_PRIJS_WA), gratis=True)
        context['prijs_khsn_speld'] = format_bedrag_euro(Decimal(settings.SPELD_PRIJS_KHSN), gratis=True)
        context['prijs_vervang'] = format_bedrag_euro(Decimal(settings.SPELD_PRIJS_VERVANG), gratis=True)

        context['kruimels'] = (
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Prijslijst')
        )

        return context


# end of file
