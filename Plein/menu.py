# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Functie.rol import Rollen, rol_get_huidige, rol_mag_wisselen, rol_get_beschrijving


ACTIEF_OPTIES = (
    'inloggen',
    'uitloggen',
    'privacy',
    'records',
    'logboek',
    'site-feedback-inzicht',
    'wissel-van-rol',
    'competitie',
    'histcomp',
    'schutter'
)


WIKI = {
    Rollen.ROL_BKO: (settings.WIKI_URL_BKO, 'Handleiding BKO'),
    Rollen.ROL_RKO: (settings.WIKI_URL_RKO, 'Handleiding RKO'),
    Rollen.ROL_RCL: (settings.WIKI_URL_RCL, 'Handleiding RCL'),
    Rollen.ROL_CWZ: (settings.WIKI_URL_CWZ, 'Handleiding CWZ'),
}


def menu_dynamics(request, context, actief=None):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu item dat actief is.
    """
    if actief:
        assert (actief in ACTIEF_OPTIES), 'menu_dynamics: Onbekende actief waarde %s' % repr(actief)
        context['menu_actief'] = actief

    rol = rol_get_huidige(request)

    # zet context variabelen om aan te geven welke optionele delen van het menu getoond moeten worden
    if request.user.is_authenticated:
        # uitloggen
        context['menu_show_logout'] = True

        # wissel van rol
        if rol_mag_wisselen(request):
            context['menu_show_wisselvanrol'] = True

            try:
                context['wiki_url'], context['wiki_titel'] = WIKI[rol]
            except KeyError:
                context['wiki_url'] = settings.WIKI_URL_TOP
                context['wiki_titel'] = 'Handleiding'

        # admin menu
        if rol == Rollen.ROL_IT:
            context['menu_show_admin'] = True

        # logboek en site feedback
        if rol in (Rollen.ROL_IT, Rollen.ROL_BB):
            context['menu_show_logboek'] = True
            context['menu_show_sitefeedback'] = True

        if rol == Rollen.ROL_SCHUTTER:
            context['menu_show_schutter'] = True

    else:
        # inloggen
        context['menu_show_login'] = True

    context['menu_rol_beschrijving'] = rol_get_beschrijving(request)


# end of file
