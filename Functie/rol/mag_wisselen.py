# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Ondersteuning voor de rollen binnen de applicatie """

from django.contrib.sessions.backends.db import SessionStore
from Account.operations.session_vars import zet_sessionvar_if_changed
from Account.models import AccountSessions

SESSIONVAR_ROL_MAG_WISSELEN_BOOL = 'gebruiker_rol_mag_wisselen_bool'


def rol_zet_mag_wisselen(request, mag_wisselen: bool):
    """ Sla op of de gebruiker toegang heeft tot wissel-van-rol """

    zet_sessionvar_if_changed(request, SESSIONVAR_ROL_MAG_WISSELEN_BOOL, mag_wisselen)


def rol_mag_wisselen(request):
    """ Geeft True terug als deze gebruiker de wissel-van-rol getoond moet worden """
    try:
        check = request.session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL]
    except KeyError:
        check = False

    return check


def rol_zet_mag_wisselen_voor_account(account):
    """ Deze functie geeft een nieuwe beheerder direct toegang tot Wissel van rol.

        Aangezien dit om performance redenen onthouden wordt in de sessie van de gebruiker,
        moeten we op zoek naar alle sessie(s) en daar een aanpassing in doen.
    """

    # doorloop alle bekende sessies van deze gebruiker
    for obj in (AccountSessions
                .objects
                .filter(account=account)):
        session = SessionStore(obj.session.session_key)
        try:
            mag_wisselen = session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL]
        except KeyError:
            # expired sessions do not have keys
            pass
        else:
            if not mag_wisselen:
                # wijziging
                session[SESSIONVAR_ROL_MAG_WISSELEN_BOOL] = True
                session.save()
    # for


# end of file
