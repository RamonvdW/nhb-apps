# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.views.generic import TemplateView
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Instaptoets.operations import instaptoets_is_beschikbaar, vind_toets_prioriteer_geslaagd, toets_geldig
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN
from Opleiding.models import Opleiding
from Sporter.models import get_sporter

TEMPLATE_OPLEIDINGEN_BASISCURSUS = 'opleiding/basiscursus.dtl'


class BasiscursusView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_BASISCURSUS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        context['eis_percentage'] = settings.INSTAPTOETS_AANTAL_GOED_EIS

        opleiding = (Opleiding
                     .objects
                     .filter(is_basiscursus=True,
                             status=OPLEIDING_STATUS_INSCHRIJVEN)
                     .prefetch_related('momenten')
                     .order_by('periode_begin', 'periode_einde')       # meest recente cursus eerst
                     .first())

        momenten = list()
        for moment in opleiding.momenten.prefetch_related('locatie').order_by('datum'):
            locatie = moment.locatie
            if locatie:
                moment.omschrijving = locatie.plaats
                if not moment.omschrijving:
                    moment.omschrijving = locatie.naam
                momenten.append(moment)
        # for
        if len(momenten) > 0:
            context['momenten'] = momenten

        account = get_account(self.request)
        if account.is_authenticated:
            context['is_ingelogd'] = True

            if not account.is_gast and rol_get_huidige(self.request) == Rol.ROL_SPORTER:
                context['toon_inschrijven'] = True

                sporter = get_sporter(account)

                if sporter and instaptoets_is_beschikbaar():
                    context['url_instaptoets'] = reverse('Instaptoets:begin')

                    toets = vind_toets_prioriteer_geslaagd(sporter)
                    if toets:
                        context['toets'] = toets

                        is_geldig, dagen = toets_geldig(toets)
                        context['toets_is_geldig'] = is_geldig
                        context['toets_geldig_dagen'] = dagen

                        if is_geldig:
                            context['url_instaptoets'] = None
                            context['url_inschrijven'] = reverse('Opleiding:inschrijven-basiscursus')

                            if settings.IS_TEST_SERVER:
                                context['url_instaptoets_opnieuw'] = reverse('Instaptoets:begin')

        context['kruimels'] = (
            (reverse('Opleiding:overzicht'), 'Opleidingen'),
            (None, 'Basiscursus')
        )

        return context


# end of file
