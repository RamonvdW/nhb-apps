# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.conf import settings
from django.views.generic import TemplateView
from Account.models import get_account
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Instaptoets.operations import vind_toets
from Opleiding.definities import (OPLEIDING_STATUS_GEANNULEERD, OPLEIDING_STATUS_VOORBEREIDEN,
                                  OPLEIDING_STATUS_INSCHRIJVEN, OPLEIDING_STATUS_TO_STR)
from Opleiding.models import Opleiding, OpleidingDiploma
from Sporter.models import get_sporter

TEMPLATE_OPLEIDINGEN_OVERZICHT = 'opleiding/overzicht.dtl'
TEMPLATE_OPLEIDINGEN_DETAILS = 'opleiding/details.dtl'


class OpleidingenOverzichtView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_OVERZICHT

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        opleidingen = (Opleiding
                       .objects
                       .exclude(status=OPLEIDING_STATUS_VOORBEREIDEN)
                       .order_by('periode_begin', 'periode_einde'))     # recent bovenaan
        context['opleidingen'] = opleidingen

        enable_basiscursus = False
        for opleiding in opleidingen:
            opleiding.status_str = OPLEIDING_STATUS_TO_STR[opleiding.status]

            if opleiding.status != OPLEIDING_STATUS_GEANNULEERD:
                if opleiding.is_basiscursus:
                    enable_basiscursus = True
                    opleiding.url_details = reverse('Opleiding:basiscursus')
                else:
                    opleiding.url_details = reverse('Opleiding:details', kwargs={'opleiding_pk': opleiding.pk})
        # for

        if enable_basiscursus:
            # toon het grote kaartje
            context['url_basiscursus'] = reverse('Opleiding:basiscursus')

        context['url_opleidingen_main_site'] = settings.URL_OPLEIDINGEN

        account = get_account(self.request)
        if account.is_authenticated and not account.is_gast:
            context['is_ingelogd'] = True

            rol_nu = rol_get_huidige(self.request)
            if rol_nu == Rol.ROL_SPORTER:
                # pak de diploma's erbij
                sporter = get_sporter(account)

                # kijk of sporter bezig is met een instaptoets
                # zodat we meteen een kaartje aan kunnen bieden om hiermee verder te gaan
                toets = vind_toets(sporter)
                if toets and not toets.is_afgerond:
                    context['url_vervolg_instaptoets'] = reverse('Instaptoets:volgende-vraag')

                # now = timezone.now()
                diplomas = (OpleidingDiploma
                            .objects
                            .filter(sporter=sporter)
                            # .exclude(datum_einde__lt=now)
                            .order_by('-datum_begin'))      # nieuwste bovenaan

                context['diplomas'] = diplomas

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
            opleiding = Opleiding.objects.exclude(status=OPLEIDING_STATUS_VOORBEREIDEN).get(pk=opleiding_pk)
        except (IndexError, ValueError, TypeError, Opleiding.DoesNotExist):
            raise Http404('Slechte parameter')

        opleiding.is_geannuleerd = opleiding.status == OPLEIDING_STATUS_GEANNULEERD
        opleiding.kosten_str = format_bedrag_euro(opleiding.kosten_euro)

        context['opleiding'] = opleiding

        # TODO: is er een deadline voor inschrijven?
        context['toon_inschrijven'] = (opleiding.status == OPLEIDING_STATUS_INSCHRIJVEN)

        rol_kruimels = Rol.ROL_SPORTER    # voor de kruimels

        # om aan te melden is een account nodig
        # extern beheerder wedstrijden kan je niet voor aanmelden
        # een wedstrijd zonder sessie is een placeholder op de agenda
        account = get_account(self.request)
        if account.is_authenticated:
            if account.is_gast:
                context['toon_inschrijven'] = False
            else:
                rol_nu = rol_kruimels = rol_get_huidige(self.request)
                if rol_nu == Rol.ROL_SPORTER:
                    context['kan_aanmelden'] = True
                    # TODO: context['url_inschrijven_sporter'] = reverse('Plein:plein')
                else:
                    # beheerders (HWL 1368) niet het kaartje inschrijven tonen
                    context['toon_inschrijven'] = False
        else:
            context['hint_inloggen'] = True

        if rol_kruimels in (Rol.ROL_SEC, Rol.ROL_HWL):
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Opleiding:vereniging'), 'Opleidingen'),
                (None, opleiding.titel),
            )
        elif rol_kruimels == Rol.ROL_MO:
            context['kruimels'] = (
                (reverse('Opleiding:manager'), 'Opleidingen'),
                (None, opleiding.titel),
            )
        else:
            context['kruimels'] = (
                (reverse('Opleiding:overzicht'), 'Opleidingen'),
                (None, opleiding.titel),
            )

        return context

# end of file
