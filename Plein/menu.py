# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Account.rol import Rollen, rol_get_huidige, rol_get_limiet


ACTIEF_OPTIES = (
    'inloggen',
    'privacy',
    'records',
    'logboek',
    'site-feedback-inzicht',
    'wissel-van-rol'
)


def menu_dynamics(request, context, actief=None):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu item dat actief is.
    """
    if actief:
        assert (actief in ACTIEF_OPTIES), 'menu_dynamics: Onbekende actief waarde %s' % repr(actief)
        context['menu_actief'] = actief

    rol = rol_get_huidige(request)
    rol_limiet = rol_get_limiet(request)

    # zet context variabele om aan te geven of de link naar de Admin site erbij mag
    # TODO: blijven doen met django authentication system?
    if request.user.is_authenticated:

        # uitloggen
        context['menu_show_logout'] = True

        # wissel van rol
        if rol_limiet != Rollen.ROL_UNKNOWN:
            context['menu_show_wisselvanrol'] = True

        # IT: admin menu
        if rol == Rollen.ROL_IT:
            context['menu_show_admin'] = True

        # BKO: logboek en sitefeedback
        if rol in (Rollen.ROL_IT, Rollen.ROL_BKO):
            context['menu_show_logboek'] = True
            context['menu_show_sitefeedback'] = True
    else:
        # inloggen
        context['menu_show_login'] = True

    if rol == Rollen.ROL_IT:
        context['menu_rol_beschrijving'] = 'IT beheerder'
    elif rol == Rollen.ROL_BKO:
        context['menu_rol_beschrijving'] = 'BKO'
    elif rol == Rollen.ROL_SCHUTTER:
        context['menu_rol_beschrijving'] = 'Schutter'


# end of file
