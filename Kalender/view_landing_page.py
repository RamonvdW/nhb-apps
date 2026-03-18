# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import View
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Kalender.view_helpers import get_url_eerstvolgende_maand_met_wedstrijd, get_url_kalender_jaaroverzicht_vanaf_datum


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


class KalenderLandingPageJaarView(View):
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
            # geef url met jaaroverzicht
            now = timezone.now()
            url = get_url_kalender_jaaroverzicht_vanaf_datum(now)

        return HttpResponseRedirect(url)


class KalenderLandingPageDisciplineView(View):
    """ Deze pagina is voor het doorsturen naar het jaaroverzicht met een voorgeselecteerd discipline filter.
    """
    @staticmethod
    def get(request, *args, **kwargs):

        # geef basis url met jaaroverzicht
        now = timezone.now()
        url = get_url_kalender_jaaroverzicht_vanaf_datum(now)

        url += 'alle/'      # soort (IFAA, WA A-status, etc.)

        if request.user.is_authenticated:
            # ingelogd, dus filter op gekozen bogen van de gebruiker
            url += 'mijn/'
        else:
            url += 'alle/'

        discipline = kwargs['discipline'].lower()
        if discipline not in ('indoor', 'outdoor', '25m1pijl', 'clout', 'veld', 'run-archery', '3d'):
            discipline = 'alle'

        url += discipline + '/'

        return HttpResponseRedirect(url)


# end of file
