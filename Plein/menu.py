# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Functie.rol import Rollen, rol_get_huidige, rol_mag_wisselen, rol_get_beschrijving
from Taken.taken import aantal_open_taken

ACTIEF_OPTIES = (
    'hetplein',
    'schutter-profiel',
    'vereniging',
    'competitie',
    'records',
    'kalender',
    'taken',
    'wissel-van-rol',
)


def menu_dynamics(request, context, actief='hetplein'):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu item dat actief is.
    """

    # welke regel van het menu op laten lichten?
    context['menu_actief'] = actief
    if not (actief in ACTIEF_OPTIES or actief.startswith('competitie-')):
        raise AssertionError("menu_dynamics: Onbekende 'actief' waarde: %s" % repr(actief))

    # test server banner tonen?
    context['is_test_server'] = settings.IS_TEST_SERVER

    # zet context variabelen om aan te geven welke optionele delen van het menu getoond moeten worden
    context['toon_kalender'] = False
    if request.user.is_authenticated:

        # sidenav naam
        context['menu_toon_naam'] = True

        # wissel van rol toegestaan?
        if rol_mag_wisselen(request):
            rol = rol_get_huidige(request)

            context['toon_kalender'] = False

            # sidenav rol
            context['menu_rol_beschrijving'] = rol_get_beschrijving(request)

            # activeer menu 'wissel van rol'
            context['menu_show_wisselvanrol'] = True

            # admin menu
            if rol == Rollen.ROL_IT:
                context['menu_show_admin'] = True

            if rol in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL):
                context['menu_toon_vereniging'] = True

            if rol == Rollen.ROL_SCHUTTER:
                context['menu_toon_schutter_profiel'] = True

            if rol in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_SEC):     # TODO: ook WL uitsluiten?
                context['toon_kalender'] = False

            # taken
            if rol in (Rollen.ROL_IT, Rollen.ROL_BB,
                       Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL,
                       Rollen.ROL_HWL):
                context['menu_show_taken'] = True
                context['menu_aantal_open_taken'] = aantal_open_taken(request)
        else:
            context['menu_toon_schutter_profiel'] = True

    # het label met de scherm grootte boven aan het scherm
    context['toon_schermgrootte'] = settings.DEBUG


# end of file
