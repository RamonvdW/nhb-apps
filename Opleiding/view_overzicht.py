# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from Account.models import get_account
from Betaal.format import format_bedrag_euro
from Opleiding.definities import OPLEIDING_STATUS_GEANNULEERD, OPLEIDING_STATUS_VOORBEREID
from Opleiding.models import Opleiding, OpleidingDiploma
from Sporter.models import get_sporter

TEMPLATE_OPLEIDINGEN_OVERZICHT = 'opleidingen/overzicht.dtl'
TEMPLATE_OPLEIDINGEN_DETAILS = 'opleidingen/details.dtl'


class OpleidingenOverzichtView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_OVERZICHT

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        opleidingen = (Opleiding
                       .objects
                       .exclude(status=OPLEIDING_STATUS_VOORBEREID)
                       .order_by('periode_jaartal', 'periode_kwartaal'))     # recent bovenaan
        context['opleidingen'] = opleidingen

        enable_basiscursus = False
        for opleiding in opleidingen:
            if opleiding.status == OPLEIDING_STATUS_GEANNULEERD:
                opleiding.titel = '[GEANNULEERD] ' + opleiding.titel
            else:
                if opleiding.is_basiscursus:
                    enable_basiscursus = True
                    opleiding.url_details = reverse('Opleiding:inschrijven-basiscursus')
                else:
                    opleiding.url_details = reverse('Opleiding:details', kwargs={'opleiding_pk': opleiding.pk})
        # for

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

            if enable_basiscursus:
                context['url_basiscursus'] = reverse('Opleiding:basiscursus')

        context['kruimels'] = (
            (None, 'Opleidingen'),
        )

        return context


class OpleidingDetailsView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_DETAILS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            opleiding_pk = kwargs['opleiding_pk'][:6]     # afkappen voor de veiligheid
            opleiding_pk = int(opleiding_pk)
            opleiding = Opleiding.objects.exclude(status=OPLEIDING_STATUS_VOORBEREID).get(pk=opleiding_pk)
        except (IndexError, ValueError, TypeError, Opleiding.DoesNotExist):
            raise Http404('Slechte parameter')

        opleiding.is_geannuleerd = opleiding.status == OPLEIDING_STATUS_GEANNULEERD
        opleiding.kosten_str = format_bedrag_euro(opleiding.kosten_euro)

        context['opleiding'] = opleiding

        # TODO: is er een deadline voor inschrijven?
        context['toon_inschrijven'] = True

        # om aan te melden is een account nodig
        # extern beheerder wedstrijden kan je niet voor aanmelden
        # een wedstrijd zonder sessie is een placeholder op de agenda
        if self.request.user.is_authenticated:
            context['kan_aanmelden'] = True
            context['url_inschrijven_sporter'] = reverse('Plein:plein')
        else:
            context['hint_inloggen'] = True

        context['kruimels'] = (
            (reverse('Opleiding:overzicht'), 'Opleidingen'),
            (None, opleiding.titel),
        )

        return context


# end of file
