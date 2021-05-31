# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.urls import reverse
from django.http import HttpResponseRedirect
from Functie.rol import Rollen, rol_get_huidige
from .view_maand import get_url_huidige_maand


class KalenderLandingPageView(View):
    """ Deze pagina is puur voor het doorsturen naar een van de andere pagina's
        afhankelijk van de gekozen rol.
    """
    @staticmethod
    def get(request, *args, **kwargs):
        rol_nu = rol_get_huidige(request)

        if rol_nu == Rollen.ROL_BB:
            url = reverse('Kalender:manager')

        elif rol_nu == Rollen.ROL_HWL:
            url = reverse('Kalender:vereniging')

        else:
            url = get_url_huidige_maand()

        return HttpResponseRedirect(url)


# end of file
