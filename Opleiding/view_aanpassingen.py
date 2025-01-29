# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Opleiding.models import OpleidingInschrijving

TEMPLATE_OPLEIDING_AANPASSINGEN = 'opleiding/aanpassingen.dtl'


class AanpassingenView(UserPassesTestMixin, View):

    """ Via deze view kan de Manager Opleidingen de aanpassingen inzien die bij inschrijven opgegeven zijn:
            - geboorteplaats
        zodat deze overgenomen kan worden in het CRM
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_AANPASSINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_MO

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['huidige_rol'] = rol_get_beschrijving(request)

        context['inschrijvingen'] = inschrijvingen = list()

        for inschrijving in (OpleidingInschrijving
                             .objects
                             .exclude(aanpassing_geboorteplaats='')
                             .select_related('sporter')
                             .order_by('wanneer_aangemeld')):

            if inschrijving.sporter.geboorteplaats != inschrijving.aanpassing_geboorteplaats:
                inschrijvingen.append(inschrijving)
        # for

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (None, 'Aanpassingen')
        )

        return render(request, self.template_name, context)


# end of file
