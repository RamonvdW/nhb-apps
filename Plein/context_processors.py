# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import reverse
from Account.models import get_account
from Account.operations.otp import otp_is_controle_gelukt
from Functie.definities import Rollen
from Functie.rol import rol_mag_wisselen, rol_get_huidige
from Bestel.operations.mandje import cached_aantal_in_mandje_get
from Taken.operations import aantal_open_taken


def site_layout(request):
    """ Deze functie geeft context variabelen terug die gebruikt worden in site_layout.dtl
        zoals voor het menu.
    """

    context = dict()

    # test server banner tonen?
    context['is_test_server'] = settings.IS_TEST_SERVER

    # zet context variabelen om aan te geven welke optionele delen van het menu getoond moeten worden
    if request.user.is_authenticated:
        # gebruiker is ingelogd

        context['menu_url_uitloggen'] = reverse('Account:logout')

        # naam voor op de knop
        account = get_account(request)
        context['menu_voornaam'] = account.get_first_name()

        # mandje tonen?
        context['menu_mandje_aantal'] = cached_aantal_in_mandje_get(request)
        if context['menu_mandje_aantal'] > 0:
            # we zetten deze niet terug op False,
            # zodat views deze ook op True kunnen zetten (ook al is het mandje leeg)
            context['menu_toon_mandje'] = True

            # wissel van rol toegestaan?
        if rol_mag_wisselen(request):
            context['menu_url_wissel_van_rol'] = reverse('Functie:wissel-van-rol')

            if account.is_staff:
                if otp_is_controle_gelukt(request):
                    context['menu_url_admin_site'] = reverse('admin:index')

            rol = rol_get_huidige(request)

            if rol == Rollen.ROL_SPORTER:
                context['menu_url_profiel'] = reverse('Sporter:profiel')
                context['menu_url_bondspas'] = reverse('Bondspas:toon-bondspas')
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

    # subset of volledige fonts gebruiken in site_layout_fonts.dtl?
    context['font_use_subset_files'] = settings.USE_SUBSET_FONT_FILES

    return context


# end of file
