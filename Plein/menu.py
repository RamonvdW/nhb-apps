# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Account.rol import Rollen, rol_get_huidige, rol_mag_wisselen, rol_get_beschrijving


ACTIEF_OPTIES = (
    'inloggen',
    'uitloggen',
    'privacy',
    'records',
    'logboek',
    'site-feedback-inzicht',
    'wissel-van-rol',
    'competitie'
)


def menu_dynamics(request, context, actief=None):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu item dat actief is.
    """
    if actief:
        assert (actief in ACTIEF_OPTIES), 'menu_dynamics: Onbekende actief waarde %s' % repr(actief)
        context['menu_actief'] = actief

    rol = rol_get_huidige(request)
    rol_beschrijving = rol_get_beschrijving(request)

    # zet context variabelen om aan te geven welke optionele delen van het menu getoond moeten worden
    if request.user.is_authenticated:
        # uitloggen
        context['menu_show_logout'] = True

        # wissel van rol
        if rol_mag_wisselen(request):
            context['menu_show_wisselvanrol'] = True

        # admin menu
        if rol == Rollen.ROL_IT:
            context['menu_show_admin'] = True

        # logboek en sitefeedback
        if rol in (Rollen.ROL_IT, Rollen.ROL_BB):
            context['menu_show_logboek'] = True
            context['menu_show_sitefeedback'] = True
    else:
        # inloggen
        context['menu_show_login'] = True

    context['menu_rol_beschrijving'] = rol_beschrijving

    context['wiki_url'] = settings.WIKI_URL

# end of file
