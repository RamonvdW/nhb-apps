# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.rol import rol_get_huidige, Rollen

TEMPLATE_VOORDEEL_OVERZICHT = 'ledenvoordeel/overzicht.dtl'
TEMPLATE_VOORDEEL_WALIBI = 'ledenvoordeel/walibi.dtl'


class VoordeelOverzichtView(UserPassesTestMixin, TemplateView):

    """ Via deze view krijgen gebruikers (=ingelogde leden) de overzichtspagina met de voordelen te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_VOORDEEL_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if rol_get_huidige(self.request) != Rollen.ROL_SPORTER:
            return False

        if self.request.user.is_authenticated:
            account = get_account(self.request)
            if account.is_gast:
                return False

        return True

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (None, 'Ledenvoordeel'),
        )

        return context


class VoordeelWalibiView(UserPassesTestMixin, TemplateView):

    """ Via deze view krijgen gebruikers (=ingelogde leden) de overzichtspagina met de voordelen te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_VOORDEEL_WALIBI
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if rol_get_huidige(self.request) != Rollen.ROL_SPORTER:
            return False

        if self.request.user.is_authenticated:
            account = get_account(self.request)
            if account.is_gast:
                return False

        return True

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_walibi'] = settings.WALIBI_URL

        context['kruimels'] = (
            (reverse('Ledenvoordeel:overzicht'), 'Ledenvoordeel'),
            (None, 'Walibi'),
        )

        return context


# end of file
