# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from django.shortcuts import render
from django.templatetags.static import static
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestel.operations.mandje import mandje_tel_inhoud
from Bestel.operations.mutaties import bestel_mutatieverzoek_webwinkel_keuze
from Functie.rol import Rollen, rol_get_huidige
from Plein.menu import menu_dynamics
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze


TEMPLATE_WEBWINKEL_MANAGER = 'webwinkel/manager.dtl'


class ManagerView(UserPassesTestMixin, TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_WEBWINKEL_MANAGER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_MWW

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (None, 'Webwinkel'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
