# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, gebruiker_is_scheids

TEMPLATE_OVERZICHT = 'scheidsrechter/overzicht.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        if self.rol_nu == Rol.ROL_CS:
            return True
        if self.rol_nu == Rol.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.rol_nu == Rol.ROL_SPORTER:
            context['url_korps'] = reverse('Scheidsrechter:korps')
            context['tekst_korps'] = "Bekijk de lijst van de scheidsrechters."

            context['url_beschikbaarheid'] = reverse('Scheidsrechter:beschikbaarheid-wijzigen')
            context['tekst_beschikbaarheid'] = "Pas je beschikbaarheid aan voor wedstrijden."

            context['rol'] = 'sporter / scheidsrechter'
        else:
            context['url_korps'] = reverse('Scheidsrechter:korps-met-contactgegevens')
            context['tekst_korps'] = "Bekijk de lijst van de scheidsrechters met contactgegevens."

            context['url_beschikbaarheid'] = reverse('Scheidsrechter:beschikbaarheid-inzien')
            context['tekst_beschikbaarheid'] = "Bekijk de opgegeven beschikbaarheid."

            context['rol'] = 'Commissie Scheidsrechters'

        context['url_handleiding_scheidsrechters'] = settings.URL_PDF_HANDLEIDING_SCHEIDSRECHTERS

        context['kruimels'] = (
            (None, 'Scheidsrechters'),
        )

        return context


# end of file
