# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from Functie.rol import Rollen, rol_get_huidige
from Mandje.models import MandjeInhoud
from Plein.menu import menu_dynamics


TEMPLATE_MANDJE_TOON_INHOUD = 'mandje/toon-inhoud.dtl'


class ToonInhoudMandje(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker de inhoud van zijn mandje zien """

    # class variables shared by all instances
    template_name = TEMPLATE_MANDJE_TOON_INHOUD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        account = self.request.user

        inhoud = (MandjeInhoud
                  .objects
                  .filter(account=account)
                  .select_related('inschrijving'))

        context['inhoud'] = inhoud

        context['kruimels'] = (
            (None, 'Mandje'),
        )

        menu_dynamics(self.request, context)
        return context

# end of file
