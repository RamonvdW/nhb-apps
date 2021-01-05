# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from Functie.rol import Rollen, rol_get_huidige, rol_mag_wisselen, rol_get_beschrijving
from Taken.taken import aantal_open_taken


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
    'taken',
    'kalender'
)


def menu_dynamics(request, context, actief=None):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu item dat actief is.
    """
    if actief:
        assert (actief in ACTIEF_OPTIES), 'menu_dynamics: Onbekende actief waarde %s' % repr(actief)
        context['menu_actief'] = actief

    context['is_test_server'] = settings.ENABLE_WIKI

    rol = rol_get_huidige(request)

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

        # logboek en site feedback
        if rol in (Rollen.ROL_IT, Rollen.ROL_BB):
            context['menu_show_logboek'] = True
            context['menu_show_sitefeedback'] = True
            context['menu_show_kalender'] = True

        if rol == Rollen.ROL_SCHUTTER:
            context['menu_show_schutter'] = True

        if rol in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL):
            context['menu_show_vereniging'] = True

        if rol in (Rollen.ROL_IT, Rollen.ROL_BB,
                   Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL,
                   Rollen.ROL_HWL):
            context['menu_show_taken'] = True
            context['menu_aantal_open_taken'] = aantal_open_taken(request)
    else:
        # inloggen
        context['menu_show_login'] = True

    context['menu_rol_beschrijving'] = rol_get_beschrijving(request)
    context['is_debug'] = settings.DEBUG


# end of file
