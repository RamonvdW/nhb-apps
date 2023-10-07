# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from Registreer.operations import registratie_gast_is_open


TEMPLATE_REGISTREER_BEGIN = 'registreer/begin.dtl'


class RegistreerBeginView(TemplateView):
    """
        Deze view geeft de landing page voor het aanmaken van een account en
        verwijst naar de verschillende procedures voor leden en gast-accounts.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_REGISTREER_BEGIN

    def dispatch(self, request, *args, **kwargs):
        # wegsturen als je al ingelogd bent
        if request.user.is_authenticated:
            return redirect('Plein:plein')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['gast_is_open'] = registratie_gast_is_open()

        context['url_registreer_nhb'] = reverse('Registreer:lid')
        context['url_registreer_gast'] = reverse('Registreer:gast')

        context['kruimels'] = (
            (None, 'Account aanmaken'),
        )

        return context


# end of file
