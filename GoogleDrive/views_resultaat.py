# -*- coding: utf-8 -*-
#
#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige

TEMPLATE_GOOGLEDRIVE_RESULTAAT_GELUKT = 'googledrive/resultaat-gelukt.dtl'
TEMPLATE_GOOGLEDRIVE_RESULTAAT_MISLUKT = 'googledrive/resultaat-mislukt.dtl'


class ResultaatGeluktView(UserPassesTestMixin, TemplateView):

    """ Toon het resultaat van de OAuth aan de gebruiker en leg uit wat de vervolgstappen zijn. """

    # class variables shared by all instances
    template_name = TEMPLATE_GOOGLEDRIVE_RESULTAAT_GELUKT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_next'] = reverse('Competitie:kies')

        context['kruimels'] = (
            (None, 'Google Drive'),
        )

        return context


class ResultaatMisluktView(UserPassesTestMixin, TemplateView):

    """ Toon het resultaat van de OAuth aan de gebruiker en leg uit wat de vervolgstappen zijn. """

    # class variables shared by all instances
    template_name = TEMPLATE_GOOGLEDRIVE_RESULTAAT_MISLUKT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_next'] = reverse('Competitie:kies')

        context['kruimels'] = (
            (None, 'Google Drive'),
        )

        return context


# end of file
