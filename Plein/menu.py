# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


def menu_dynamics(request, context, actief=None):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu item dat actief is.
    """
    if actief:
        assert (actief in ('inloggen', 'privacy', 'records', 'site-feedback-inzicht')), 'menu_dynamics: Onbekende actief waarde %s' % repr(actief)
        context['menu_actief'] = actief

    # zet context variabele om aan te geven of de link naar de Admin site erbij mag
    # TODO: blijven doen met django authentication system?
    if request.user.is_authenticated:
        context['menu_show_logout'] = True
        if request.user.is_superuser:
            context['menu_show_admin'] = True
    else:
        context['menu_show_login'] = True

    # TODO: rol-selectie opties

# end of file
