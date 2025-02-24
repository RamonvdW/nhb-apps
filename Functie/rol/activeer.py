# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Ondersteuning voor de rollen binnen de applicatie """

from Account.models import Account
from Functie.definities import Rol
from Functie.models import Functie
from Functie.rol.beschrijving import rol_zet_beschrijving
from Functie.rol.bepaal import RolBepaler
from Functie.rol.huidige import rol_zet_huidige_rol, rol_zet_huidige_functie_pk
import logging

my_logger = logging.getLogger('MH.Functie')


def rol_activeer_rol(request, account: Account, rol: Rol):
    """ Activeer een andere rol, als dit toegestaan is.
        Geen foutmelding of exceptions als het niet mag.
    """

    akkoord = False

    if account.is_authenticated:
        if rol in (Rol.ROL_NONE, Rol.ROL_SPORTER):
            akkoord = True

        if rol == Rol.ROL_BB:
            if account.is_staff or account.is_BB:
                akkoord = True

        # alle andere rollen horen bij een functie
        # (onmogelijk om hier te komen)
        # else:
        #     # volledige analyse vereist
        #     rol_bepaler = RolBepaler(account)
        #     if rol_bepaler.mag_rol(rol):
        #         akkoord = True

    if akkoord:
        rol_zet_huidige_rol(request, rol)
        rol_zet_huidige_functie_pk(request, None)
        rol_zet_beschrijving(request, rol)

    # else: silently ignore


def rol_activeer_functie(request, account: Account, functie: Functie):
    """ Activeer een andere rol gebaseerd op een Functie.
        Geen foutmelding of exceptions als het niet mag.
    """

    if account.is_authenticated:
        rol_bepaler = RolBepaler(account)

        akkoord, rol = rol_bepaler.mag_functie(request, functie.pk)

        if akkoord:
            rol_zet_huidige_rol(request, rol)
            rol_zet_huidige_functie_pk(request, functie.pk)
            rol_zet_beschrijving(request, rol, functie=functie)

    # else: silently ignore


# end of file
