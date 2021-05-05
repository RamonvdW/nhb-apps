# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from .models import (KalenderWedstrijd,
                     WEDSTRIJD_DISCIPLINE_TO_STR, WEDSTRIJD_STATUS_TO_STR)

TEMPLATE_KALENDER_OVERZICHT_MANAGER = 'kalender/overzicht-manager.dtl'


class KalenderManagerView(UserPassesTestMixin, View):
    """ Via deze view kan de Manager Competitiezaken de wedstrijdkalender beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_OVERZICHT_MANAGER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BB

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        # pak de 50 meest recente wedstrijden
        wedstrijden = (KalenderWedstrijd
                       .objects
                       .order_by('-datum_begin')[:50])

        for wed in wedstrijden:
            wed.disc_str = WEDSTRIJD_DISCIPLINE_TO_STR[wed.discipline]
            wed.status_str = WEDSTRIJD_STATUS_TO_STR[wed.status]
            wed.url_wijzig = reverse('Kalender:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        menu_dynamics(self.request, context, actief='kalender')
        return render(request, self.template_name, context)


# end of file
