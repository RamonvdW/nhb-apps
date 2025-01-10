# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Instaptoets.operations import instaptoets_is_beschikbaar, vind_toets, toets_geldig
from Sporter.models import get_sporter

TEMPLATE_OPLEIDINGEN_BASISCURSUS = 'opleidingen/basiscursus.dtl'


class BasiscursusView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDINGEN_BASISCURSUS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sporter = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # instaptoets alleen aan leden tonen
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            account = get_account(self.request)
            if not account.is_gast:
                self.sporter = get_sporter(account)
                return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        context['eis_percentage'] = settings.INSTAPTOETS_AANTAL_GOED_EIS

        if instaptoets_is_beschikbaar():
            context['url_instaptoets'] = reverse('Instaptoets:begin')

            toets = vind_toets(self.sporter)
            if toets:
                context['toets'] = toets

                is_geldig, dagen = toets_geldig(toets)
                context['toets_is_geldig'] = is_geldig
                if is_geldig:
                    context['url_instaptoets'] = None

        context['kruimels'] = (
            (reverse('Opleidingen:overzicht'), 'Opleidingen'),
            (None, 'Basiscursus')
        )

        return context


# end of file