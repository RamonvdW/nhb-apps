# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from Account.models import get_account
from Opleidingen.models import OpleidingDiploma
from Sporter.models import get_sporter

TEMPLATE_OPLEIDINGEN_OVERZICHT = 'opleidingen/overzicht.dtl'


class OpleidingenOverzichtView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_OVERZICHT

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        account = get_account(self.request)
        if account.is_authenticated and not account.is_gast:

            # pak de diploma's erbij
            sporter = get_sporter(account)
            #now = timezone.now()

            diplomas = (OpleidingDiploma
                        .objects
                        .filter(sporter=sporter)
                        #.exclude(datum_einde__lt=now)
                        .order_by('-datum_begin'))      # nieuwste bovenaan

            context['diplomas'] = diplomas

            context['url_basiscursus'] = reverse('Opleidingen:basiscursus')

        context['kruimels'] = (
            (None, 'Opleidingen'),
        )

        return context


# end of file
