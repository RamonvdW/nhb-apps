# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import reverse
from Functie.rol import Rollen, rol_mag_wisselen, rol_get_huidige
from Taken.taken import aantal_open_taken

# ACTIEF_OPTIES = (
#     'hetplein',
#     'sporter-profiel',
#     'vereniging',
#     'competitie',
#     'records',
#     'kalender',
#     'taken',
#     'wissel-van-rol',
# )


def menu_dynamics(request, context, actief='hetplein'):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu item dat actief is.
    """

    # # welke regel van het menu op laten lichten?
    # context['menu_actief'] = actief
    # if not (actief in ACTIEF_OPTIES or actief.startswith('competitie-')):
    #     raise AssertionError("menu_dynamics: Onbekende 'actief' waarde: %s" % repr(actief))

    # test server banner tonen?
    context['is_test_server'] = settings.IS_TEST_SERVER

    # zet context variabelen om aan te geven welke optionele delen van het menu getoond moeten worden
    if request.user.is_authenticated:
        # gebruiker is ingelogd

        context['menu_url_uitloggen'] = reverse('Account:logout')
        context['menu_url_profiel'] = reverse('Sporter:profiel')

        # naam voor op de knop
        context['menu_voornaam'] = request.user.get_first_name()

        # wissel van rol toegestaan?
        if rol_mag_wisselen(request):
            context['menu_url_wissel_van_rol'] = reverse('Functie:wissel-van-rol')

            if request.user.is_staff:
                context['menu_url_admin_site'] = reverse('admin:index')

            rol = rol_get_huidige(request)

            # taken
            if rol in (Rollen.ROL_BB,
                       Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL,
                       Rollen.ROL_HWL):
                context['menu_aantal_open_taken'] = aantal_open_taken(request)
                context['menu_url_taken'] = reverse('Taken:overzicht')
        else:
            context['menu_toon_sporter_profiel'] = True

    else:
        context['menu_url_inloggen'] = reverse('Account:login')

    # het label met de scherm grootte boven aan het scherm
    context['menu_toon_schermgrootte'] = settings.DEBUG


# end of file
