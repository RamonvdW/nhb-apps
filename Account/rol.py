# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de rollen binnen de NHB applicaties """

import enum
from Account.models import user_is_otp_verified, account_needs_otp


SESSIONVAR_ROL_HUIDIGE = 'gebruiker_rol_huidige'
SESSIONVAR_ROL_LIMIET = 'gebruiker_rol_limiet'
SESSIONVAR_ROL_MAG_WISSELEN = 'gebruiker_rol_mag_wisselen'


class Rollen(enum.IntEnum):
    """ definitie van de rollen met codes
        vertaling naar beschrijvingen in Plein.views
    """
    # rollen staan in prio volgorde
    # dus als je 3 hebt mag je kiezen uit 3 of hoger
    ROL_IT = 1
    ROL_BKO = 2
    ROL_RKO = 3
    ROL_RCL = 4
    ROL_CWZ = 5
    ROL_SCHUTTER = 6
    ROL_UNKNOWN = 99


url2rol = {
    'beheerder': Rollen.ROL_IT,
    'BKO': Rollen.ROL_BKO,
    'RKO': Rollen.ROL_RKO,
    'RCL': Rollen.ROL_RCL,
    'CWZ': Rollen.ROL_CWZ,
    'schutter': Rollen.ROL_SCHUTTER,
}

rol2url = {
    Rollen.ROL_IT: 'beheerder',
    Rollen.ROL_BKO: 'BKO',
    Rollen.ROL_RKO: 'RKO',
    Rollen.ROL_RCL: 'RCL',
    Rollen.ROL_CWZ: 'CWZ',
    Rollen.ROL_SCHUTTER: 'schutter',
}


def rol_zet_sessionvars_na_login(account, request):
    """ zet een paar session variabelen die gebruikt worden om de rol te beheren
        deze functie wordt aangeroepen vanuit de Account.LoginView

        session variables
            gebruiker_rol_mag_wisselen: gebruik van de Plein.WisselVanRolView
    """
    sessionvars = request.session

    sessionvars[SESSIONVAR_ROL_LIMIET] = Rollen.ROL_SCHUTTER
    sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = False

    rol = None
    if user_is_otp_verified(request):
        if account.is_staff:
            rol = Rollen.ROL_IT
        elif account.is_BKO:
            rol = Rollen.ROL_BKO
    #elif account.nhblid:
    #    rol = Rollen.ROL_SCHUTTER
    if rol:
        sessionvars[SESSIONVAR_ROL_LIMIET] = rol
        sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = True
    elif account_needs_otp(account):
        sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = True

    if rol == Rollen.ROL_IT:
        sessionvars[SESSIONVAR_ROL_HUIDIGE] = Rollen.ROL_BKO
    else:
        sessionvars[SESSIONVAR_ROL_HUIDIGE] = sessionvars[SESSIONVAR_ROL_LIMIET]

    return sessionvars  # allows unittest to do sessionvars.save()


def rol_zet_sessionvars_na_otp_controle(account, request):
    rol_zet_sessionvars_na_login(account, request)


def rol_get_limiet(request):
    try:
        return request.session[SESSIONVAR_ROL_LIMIET]
    except KeyError:
        pass
    return Rollen.ROL_UNKNOWN


def rol_get_huidige(request):
    try:
        return request.session[SESSIONVAR_ROL_HUIDIGE]
    except KeyError:
        pass
    return Rollen.ROL_UNKNOWN


def rol_is_BKO(request):
    """ Geeft True terug als de gebruiker BKO rechten heeft en op dit moment BKO als rol gekozen heeft
        Wordt gebruikt om specifieke content voor de BKO te tonen
    """
    return rol_get_huidige(request) == Rollen.ROL_BKO


def rol_is_bestuurder(request):
    """ Geeft True terug als de gebruiker een bestuurder is
        Wordt gebruikt om toegang tot bepaalde schermen te voorkomen
    """
    return rol_get_huidige(request) in (Rollen.ROL_IT, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)


def rol_mag_wisselen(request):
    """ Geeft True terug als deze gebruiker de wissel-van-rol getoond moet worden """
    try:
        return request.session[SESSIONVAR_ROL_MAG_WISSELEN]
    except KeyError:
        pass
    return False


def rol_activate(request, rolurl):
    """ Activeer een andere rol, als dit toegestaan is
        geen foutmelding of exceptions als het niet mag.
    """
    sessionvars = request.session

    try:
        rol = url2rol[rolurl]
    except KeyError:
        # print('rol %s not found in url2rol' % repr(rolurl))
        pass
    else:
        try:
            rol_limiet = request.session[SESSIONVAR_ROL_LIMIET]
        except KeyError:
            # should not have been called
            pass
        else:
            if rol == Rollen.ROL_IT and rol_limiet == Rollen.ROL_IT:
                sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol

            if rol == Rollen.ROL_BKO and rol_limiet <= Rollen.ROL_BKO:
                sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol

            #if rol == "RKO" and rol_limiet <= Rollen.ROL_RKO:
            #    sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol

            #if rol == "RCL" and rol_limiet <= Rollen.ROL_RCL:
            #    sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol

            #if rol == "CWZ" and rol_limiet <= Rollen.ROL_CWZ:
            #    sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol

            if rol == Rollen.ROL_SCHUTTER:
                sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol

    # not recognized --> no change
    return sessionvars  # allows unittest to do sessionvars.save()


# end of file
