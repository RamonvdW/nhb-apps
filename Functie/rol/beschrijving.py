# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Ondersteuning voor de rollen binnen de applicatie """

from Account.operations.session_vars import zet_sessionvar_if_changed
from Functie.definities import Rol
from Functie.models import Functie

SESSIONVAR_ROL_BESCHRIJVING = 'gebruiker_rol_beschrijving'


def rol_get_beschrijving(request):
    """ retourneer de rol die opgeslagen ligt in de sessie """
    try:
        return request.session[SESSIONVAR_ROL_BESCHRIJVING]
    except KeyError:
        return "?"


def rol_zet_beschrijving(request, rol, functie_pk=None, functie=None):
    """ Bepaal de beschrijving die bij de rol hoort
        en sla deze op in de sessie
        zodat rol_get_beschrijving deze op kan halen.
    """

    if not functie:
        if functie_pk:
            functie = Functie.objects.only('beschrijving').get(pk=functie_pk)

    if functie:
        functie_naam = functie.beschrijving
    else:
        functie_naam = ""

    if rol == Rol.ROL_BB:
        beschr = 'Manager MH'

    elif rol in (Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                 Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC,
                 Rol.ROL_MO, Rol.ROL_MWZ, Rol.ROL_MWW,
                 Rol.ROL_SUP):
        beschr = functie_naam

    elif rol == Rol.ROL_CS:
        beschr = 'Commissie Scheidsrechters'

    elif rol == Rol.ROL_SPORTER:
        beschr = 'Sporter'

    else:   # ook rol == None
        # dit komt alleen voor als account geen lid is maar wel OTP mag koppelen (is_staff of is_BB)
        beschr = 'Gebruiker'

    zet_sessionvar_if_changed(request, SESSIONVAR_ROL_BESCHRIJVING, beschr)

    return beschr


# end of file
