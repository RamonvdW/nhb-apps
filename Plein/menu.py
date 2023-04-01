# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import reverse
from Account.rechten import account_rechten_is_otp_verified
from Functie.definities import Rollen
from Functie.rol import rol_mag_wisselen, rol_get_huidige
from Bestel.operations.mandje import cached_aantal_in_mandje_get
from Taken.operations import aantal_open_taken


def menu_dynamics(request, context):
    """ Deze functie update the template context voor het dynamische gedrag van
        menu zoals de 'Andere rollen' en het menu-item dat actief is.
    """

    # test server banner tonen?
    context['is_test_server'] = settings.IS_TEST_SERVER

    # zet context variabelen om aan te geven welke optionele delen van het menu getoond moeten worden
    if request.user.is_authenticated:
        # gebruiker is ingelogd

        context['menu_url_uitloggen'] = reverse('Account:logout')

        # naam voor op de knop
        context['menu_voornaam'] = request.user.get_first_name()

        # mandje tonen?
        context['menu_mandje_aantal'] = cached_aantal_in_mandje_get(request)
        if context['menu_mandje_aantal'] > 0:
            # we zetten deze niet terug op False,
            # zodat views deze ook op True kunnen zetten (ook al is het mandje leeg)
            context['menu_toon_mandje'] = True

            # wissel van rol toegestaan?
        if rol_mag_wisselen(request):
            context['menu_url_wissel_van_rol'] = reverse('Functie:wissel-van-rol')

            if request.user.is_staff:
                if account_rechten_is_otp_verified(request):
                    context['menu_url_admin_site'] = reverse('admin:index')

            rol = rol_get_huidige(request)

            if rol == Rollen.ROL_SPORTER:
                context['menu_url_profiel'] = reverse('Sporter:profiel')
            else:
                # taken
                context['menu_aantal_open_taken'] = aantal_open_taken(request)
                context['menu_url_taken'] = reverse('Taken:overzicht')
        else:
            context['menu_url_profiel'] = reverse('Sporter:profiel')

    else:
        context['menu_url_inloggen'] = reverse('Account:login')

    # het label met de schermgrootte boven aan het scherm
    context['menu_toon_schermgrootte'] = settings.DEBUG


# end of file
