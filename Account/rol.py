# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de rollen binnen de NHB applicaties """

from django.contrib.auth.models import Group
from Account.models import user_is_otp_verified, account_needs_otp
from Competitie.models import deelcompetitie_met_functie
import enum


SESSIONVAR_ROL_HUIDIGE = 'gebruiker_rol_huidige'
SESSIONVAR_ROL_GROUP = 'gebruiker_rol_group'
SESSIONVAR_ROL_LIMIET = 'gebruiker_rol_limiet'
SESSIONVAR_ROL_MAG_WISSELEN = 'gebruiker_rol_mag_wisselen'
SESSIONVAR_ROL_BESCHRIJVING = 'gebruiker_rol_beschrijving'


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
    'gebruiker': Rollen.ROL_UNKNOWN
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
    if account.nhblid:
        rol = Rollen.ROL_SCHUTTER

    if user_is_otp_verified(request):
        if account.is_staff:
            rol = Rollen.ROL_IT
        elif account.is_BKO:
            rol = Rollen.ROL_BKO
        else:
            # analyseer de functies van dit account voor bepalen van verdere rollen
            for group in request.user.groups.all():
                if group.name.startswith("BKO "):
                    if rol is None or rol > Rollen.ROL_BKO:
                        rol = Rollen.ROL_BKO
                elif group.name.startswith("RKO "):
                    if rol is None or rol > Rollen.ROL_RKO:
                        rol = Rollen.ROL_RKO
                elif group.name.startswith("RCL "):
                    if rol in None or rol > Rollen.ROL_RCL:
                        rol = Rollen.ROL_RCL
                elif group.name.startswith("CWZ "):
                    if rol is None:
                        rol = Rollen.ROL_CWZ
            # for

    if rol:
        sessionvars[SESSIONVAR_ROL_LIMIET] = rol
        sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = True
    elif account_needs_otp(account):
        sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = True

    if rol in (Rollen.ROL_IT, Rollen.ROL_BKO):
        sessionvars[SESSIONVAR_ROL_HUIDIGE] = Rollen.ROL_BKO
    else:
        sessionvars[SESSIONVAR_ROL_HUIDIGE] = Rollen.ROL_SCHUTTER

    sessionvars[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(rol)
    sessionvars[SESSIONVAR_ROL_GROUP] = None

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

def rol_get_beschrijving(request):
    try:
        return request.session[SESSIONVAR_ROL_BESCHRIJVING]
    except KeyError:
        return "?"

def rol_bepaal_beschrijving(rol):
    if rol == Rollen.ROL_IT:
        beschr = 'IT beheerder'
    elif rol == Rollen.ROL_BKO:
        beschr = 'BKO'
    elif rol == Rollen.ROL_RKO:
        beschr = 'RKO'
    elif rol == Rollen.ROL_RCL:
        beschr = 'RCL'
    elif rol == Rollen.ROL_CWZ:
        beschr = 'CWZ'
    elif rol == Rollen.ROL_SCHUTTER:
        beschr = 'Schutter'
    else:   # ook rol == None
        # dit komt alleen voor als account geen nhblid is maar wel OTP mag koppelen (is_staff of is_BKO)
        beschr = "Gebruiker"
    return beschr

def rol_is_BKO(request):
    """ Geeft True terug als de gebruiker BKO rechten heeft en op dit moment BKO als rol gekozen heeft
        Wordt gebruikt om specifieke content voor de BKO te tonen
    """
    return rol_get_huidige(request) == Rollen.ROL_BKO

def rol_is_RKO(request):
    """ Geeft True terug als de gebruiker RKO rechten heeft en op dit moment RKO als rol gekozen heeft
        Wordt gebruikt om specifieke content voor de RKO te tonen
    """
    return rol_get_huidige(request) == Rollen.ROL_RKO

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

def rol_get_functie(request):
    try:
        group_pk = request.session[SESSIONVAR_ROL_GROUP]
    except KeyError:
        pass
    else:
        try:
            group = Group.objects.get(pk=group_pk)
        except Group.DoesNotExist:
            pass
        else:
            return group
    return None

# TODO: ongewenste dependency op DeelCompetitie
def rol_get_deelcompetitie(request):
    group = rol_get_functie(request)
    deelcomp = None
    if group:
        deelcomps = group.deelcompetitie_set.all()
        if len(deelcomps):
            deelcomp = deelcomps[0]
    return deelcomp

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

            if rol in (Rollen.ROL_SCHUTTER, Rollen.ROL_UNKNOWN):
                sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol

        sessionvars[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(rol)
        sessionvars[SESSIONVAR_ROL_GROUP] = None

    # not recognized --> no change
    return sessionvars  # allows unittest to do sessionvars.save()


def rol_activate_functie(request, group_pk):
    """ Activeer een andere rol gebaseerd op een Functie
        geen foutmelding of exceptions als het niet mag.
    """
    sessionvars = request.session

    # controleer dat de group bestaat
    try:
        group = Group.objects.get(pk=group_pk)
    except Group.DoesNotExist:
        pass
    else:
        # controleer dat de gebruiker in deze group zit
        try:
            account = group.user_set.get(pk=request.user.pk)
        except Account.DoesNotExist:
            pass
        else:
            # groep bestaat en account is gekoppeld aan deze groep
            # zoek de functie die naar deze groep verwijst
            # TODO: dependency op Competitie is ongewenst
            deelcomp = deelcompetitie_met_functie(group)
            if deelcomp:
                rol = deelcomp.bepaal_rol(Rollen)
                if rol:
                    # volledig correcte wissel - sla alles nu op
                    sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol
                    sessionvars[SESSIONVAR_ROL_GROUP] = group.pk
                    sessionvars[SESSIONVAR_ROL_BESCHRIJVING] = deelcomp.get_rol_str()

    # not recognized --> no change
    return sessionvars  # allows unittest to do sessionvars.save()

# end of file
