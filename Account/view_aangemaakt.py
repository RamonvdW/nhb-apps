# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from Plein.menu import menu_dynamics


TEMPLATE_AANGEMAAKT = 'account/email_aangemaakt.dtl'


class AangemaaktView(TemplateView):
    """ Deze view geeft de laatste feedback naar de gebruiker
        nadat het account volledig aangemaakt is.
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # informatie doorgifte van de registratie view naar deze view
        # gaat via server-side session-variabelen
        try:
            login_naam = request.session['login_naam']
            partial_email = request.session['partial_email']
        except KeyError:
            # url moet direct gebruikt zijn
            raise PermissionDenied()

        # geef de data door aan de template
        context = {'login_naam': login_naam,
                   'partial_email': partial_email}
        menu_dynamics(request, context)

        return render(request, TEMPLATE_AANGEMAAKT, context)


# end of file
