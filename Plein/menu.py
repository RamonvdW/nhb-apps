# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from Functie.rol import Rollen, rol_get_huidige, rol_mag_wisselen, rol_get_beschrijving


ACTIEF_OPTIES = (
    'inloggen',
    'uitloggen',
    'hetplein',
    'privacy',
    'records',
    'logboek',
    'site-feedback-inzicht',
    'wissel-van-rol',
    'competitie',
    'histcomp',
    'schutter',
    'vereniging',
    'handleiding'
)


ROL2HANDLEIDING_PAGINA = {
    Rollen.ROL_BB: settings.HANDLEIDING_BB,
    Rollen.ROL_BKO: settings.HANDLEIDING_BKO,
    Rollen.ROL_RKO: settings.HANDLEIDING_RKO,
    Rollen.ROL_RCL: settings.HANDLEIDING_RCL,
    Rollen.ROL_HWL: settings.HANDLEIDING_HWL,
    Rollen.ROL_WL:  settings.HANDLEIDING_WL,
    #Rollen.ROL_SEC: settings.HANDLEIDING_SEC,
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
                handleiding_pagina = ROL2HANDLEIDING_PAGINA[rol]
            except KeyError:
                handleiding_pagina = settings.HANDLEIDING_TOP
                context['handleiding_titel'] = 'Handleiding'        # ipv 'Hoofdpagina'
            else:
                context['handleiding_titel'] = handleiding_pagina.replace('_', ' ')

            if settings.ENABLE_WIKI:
                context['handleiding_url'] = settings.WIKI_URL + '/' + handleiding_pagina
            else:
                context['handleiding_url'] = reverse('Handleiding:' + handleiding_pagina)

        # admin menu
        if rol == Rollen.ROL_IT:
            context['menu_show_admin'] = True

        # logboek en site feedback
        if rol in (Rollen.ROL_IT, Rollen.ROL_BB):
            context['menu_show_logboek'] = True
            context['menu_show_sitefeedback'] = True

        if rol == Rollen.ROL_SCHUTTER:
            context['menu_show_schutter'] = True

        if rol in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL):
            context['menu_show_vereniging'] = True
    else:
        # inloggen
        context['menu_show_login'] = True

    context['menu_rol_beschrijving'] = rol_get_beschrijving(request)
    context['is_debug'] = settings.DEBUG


# end of file
