# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.urls import reverse
from django.http import HttpResponseRedirect
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Kalender.view_maand import get_url_eerstvolgende_maand_met_wedstrijd


class KalenderLandingPageView(View):
    """ Deze pagina is puur voor het doorsturen naar een van de andere pagina's
        afhankelijk van de gekozen rol.
    """
    @staticmethod
    def get(request, *args, **kwargs):
        rol_nu = rol_get_huidige(request)

        if rol_nu == Rol.ROL_BB:
            url = reverse('Wedstrijden:manager')

        elif rol_nu == Rol.ROL_HWL:
            url = reverse('Wedstrijden:vereniging')

        else:
            url = get_url_eerstvolgende_maand_met_wedstrijd()

        return HttpResponseRedirect(url)


# end of file
