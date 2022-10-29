# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Plein.menu import menu_dynamics


TEMPLATE_WEBWINKEL_PROTOTYPE = 'webwinkel/prototype.dtl'


class PrototypeView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de inschrijvingen voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_WEBWINKEL_PROTOTYPE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu == Rollen.ROL_MWW

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (None, 'Webwinkel'),
        )

        menu_dynamics(self.request, context)
        return context

# end of file
