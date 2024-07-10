# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Webwinkel.models import WebwinkelProduct


TEMPLATE_WEBWINKEL_MANAGER = 'webwinkel/manager.dtl'
TEMPLATE_WEBWINKEL_VOORRAAD = 'webwinkel/voorraad.dtl'


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

        context['url_overboeking'] = reverse('Bestel:overboeking-ontvangen')
        context['url_bestellingen'] = reverse('Bestel:activiteit') + '?webwinkel=on'
        context['url_voorraad'] = reverse('Webwinkel:voorraad')

        context['kruimels'] = (
            (None, 'Webwinkel'),
        )

        return context


class WebwinkelVoorraadView(UserPassesTestMixin, TemplateView):

    """ Via deze  view laten we de voorraad per product zien """
    # class variables shared by all instances

    template_name = TEMPLATE_WEBWINKEL_VOORRAAD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_MWW

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['voorraad'] = WebwinkelProduct.objects.order_by('volgorde')

        for product in context['voorraad']:
            product.is_extern = product.beschrijving.startswith('http')
        # for

        context['kruimels'] = (
            (reverse('Webwinkel:manager'), 'Webwinkel'),
            (None, 'Voorraad'),
        )

        return context


# end of file
