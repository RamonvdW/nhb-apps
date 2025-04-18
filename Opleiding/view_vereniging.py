# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Opleiding.definities import OPLEIDING_STATUS_TO_STR
from Opleiding.models import Opleiding

TEMPLATE_OPLEIDING_OVERZICHT_VERENIGING = 'opleiding/overzicht-vereniging.dtl'


class VerenigingOpleidingenView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL de opleidingen van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()
        context['ver'] = self.functie_nu.vereniging

        context['huidige_rol'] = rol_get_beschrijving(request)

        opleidingen = (Opleiding
                       .objects
                       .order_by('periode_begin',
                                 'periode_einde',
                                 'pk'))

        for opleiding in opleidingen:
            opleiding.status_str = OPLEIDING_STATUS_TO_STR[opleiding.status]
            opleiding.url_details = reverse('Opleiding:details',
                                            kwargs={'opleiding_pk': opleiding.pk})
            opleiding.url_aanmeldingen = reverse('Opleiding:aanmeldingen',
                                                 kwargs={'opleiding_pk': opleiding.pk})
        # for

        context['opleidingen'] = opleidingen

        context['url_mollie'] = reverse('Betaal:vereniging-instellingen')
        context['url_overboeking_ontvangen'] = reverse('Bestelling:overboeking-ontvangen')

        context['url_voorwaarden'] = settings.VERKOOPVOORWAARDEN_OPLEIDINGEN_URL

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (None, 'Opleidingen'),
        )

        return render(request, self.template_name, context)


# end of file
