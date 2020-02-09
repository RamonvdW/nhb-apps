# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de rollen binnen de NHB applicaties """

from django.contrib.auth.models import Group
from Account.models import user_is_otp_verified, account_needs_otp, account_needs_vhpg
import enum


SESSIONVAR_ROL_PALLET_VAST = 'gebruiker_rol_pallet_vast'
SESSIONVAR_ROL_PALLET_FUNCTIES = 'gebruiker_rol_pallet_functies'
SESSIONVAR_ROL_MAG_WISSELEN = 'gebruiker_rol_mag_wisselen'
SESSIONVAR_ROL_HUIDIGE = 'gebruiker_rol_huidige'
SESSIONVAR_ROL_HUIDIGE_FUNCTIE = 'gebruiker_rol_functie'
SESSIONVAR_ROL_BESCHRIJVING = 'gebruiker_rol_beschrijving'


class Rollen(enum.IntEnum):
    """ definitie van de rollen met codes
        vertaling naar beschrijvingen in Plein.views
    """
    # rollen staan in prio volgorde
    # dus als je 3 hebt mag je kiezen uit 3 of hoger
    ROL_IT = 1          # IT beheerder
    ROL_BB = 2          # Coordinator bondsburo
    ROL_BKO = 3         # BK organisator, specifieke competitie
    ROL_RKO = 4         # RK organisator, specifieke competitie en rayon
    ROL_RCL = 5         # Regiocompetitieleider, specifieke competitie en regio
    ROL_CWZ = 6         # Coordinator wedstrijdzaken verenining, alle competities
    ROL_SCHUTTER = 7    # Individuele schutter en NHB lid
    ROL_NONE = 99       # geen rol


url2rol = {
    'beheerder': Rollen.ROL_IT,
    'BB': Rollen.ROL_BB,
    'BKO': Rollen.ROL_BKO,
    'RKO': Rollen.ROL_RKO,
    'RCL': Rollen.ROL_RCL,
    'CWZ': Rollen.ROL_CWZ,
    'schutter': Rollen.ROL_SCHUTTER,
    'geen': Rollen.ROL_NONE
}

rol2url = {
    Rollen.ROL_IT: 'beheerder',
    Rollen.ROL_BB: 'BB',
    Rollen.ROL_BKO: 'BKO',
    Rollen.ROL_RKO: 'RKO',
    Rollen.ROL_RCL: 'RCL',
    Rollen.ROL_CWZ: 'CWZ',
    Rollen.ROL_SCHUTTER: 'schutter',
    Rollen.ROL_NONE: 'geen',
}


rol_expandeer_functies = list()

def rol_zet_plugins(expandeer_functie):
    rol_expandeer_functies.append(expandeer_functie)


def rol_zet_sessionvars_na_login(account, request):
    """ zet een paar session variabelen die gebruikt worden om de rol te beheren
        deze functie wordt aangeroepen vanuit de Account.LoginView

        session variables
            gebruiker_rol_mag_wisselen: gebruik van de Plein.WisselVanRolView
    """
    sessionvars = request.session

    rollen_vast = list()            # list of rol
    rollen_functies = list()        # list of tuple(rol, group_pk)

    show_vhpg, _ = account_needs_vhpg(account)
    if user_is_otp_verified(request) and not show_vhpg:
        if account.is_staff:
            rollen_vast.append(Rollen.ROL_IT)
            rollen_vast.append(Rollen.ROL_NONE)      # special case

        if account.is_staff or account.is_BKO:
            rollen_vast.append(Rollen.ROL_BB)

            for func in rol_expandeer_functies:
                parent_tup = (Rollen.ROL_BB, None)
                for nwe_tup in func(Rollen.ROL_BB, None):
                    tup = (nwe_tup, parent_tup)
                    rollen_functies.append(tup)
                # for
            # for

        # analyseer de gekoppelde functies van dit account
        parent_tup = (None, None)
        for group in account.groups.all():
            rol = None
            if group.name[:4] == "BKO ":
                rol = Rollen.ROL_BKO
            elif group.name[:4] == "RKO ":
                rol = Rollen.ROL_RKO
            elif group.name[:4] == "RCL ":
                rol = Rollen.ROL_RCL
            elif group.name[:4] == "CWZ ":
                rol = Rollen.ROL_CWZ
            child_tup = (rol, group.pk)
            tup = (child_tup, parent_tup)
            rollen_functies.append(tup)
        # for

        # probeer elke rol nog verder te expanderen
        te_doorzoeken = rollen_functies[:]
        while len(te_doorzoeken) > 0:
            nwe_functies = list()
            for child_tup, dummy in te_doorzoeken:
                rol, group_pk = child_tup
                group = Group.objects.get(pk=group_pk)
                parent_tup = (rol, group_pk)
                for func in rol_expandeer_functies:
                    for nwe_tup in func(rol, group):
                        tup = (nwe_tup, parent_tup)
                        if tup not in rollen_functies:
                            rollen_functies.append(tup)
                            nwe_functies.append(tup)
                    # for
                # for
            # for

            if len(nwe_functies) > 0:
                te_doorzoeken = nwe_functies
            else:
                te_doorzoeken = list()
        # while

    if len(rollen_vast) + len(rollen_functies) > 0:
        sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = True
    elif account_needs_otp(account):
        # waarschijnlijk komen er meer rollen beschikbaar na de OTP controle
        sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = True
    else:
        sessionvars[SESSIONVAR_ROL_MAG_WISSELEN] = False

    rol = Rollen.ROL_NONE
    if account.nhblid:
        rollen_vast.append(Rollen.ROL_SCHUTTER)
        rol = Rollen.ROL_SCHUTTER

    sessionvars[SESSIONVAR_ROL_HUIDIGE] = rol
    sessionvars[SESSIONVAR_ROL_HUIDIGE_FUNCTIE] = None
    sessionvars[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(rol)

    sessionvars[SESSIONVAR_ROL_PALLET_VAST] = rollen_vast
    sessionvars[SESSIONVAR_ROL_PALLET_FUNCTIES] = rollen_functies

    return sessionvars  # allows unittest to do sessionvars.save()


def rol_zet_sessionvars_na_otp_controle(account, request):
    return rol_zet_sessionvars_na_login(account, request)


def rol_enum_pallet(request):
    """ Itereert over de mogelijke rollen in het pallet van deze gebruiker
        elke yield geeft twee tuples (Rollen.ROL_xx, Group) van het de rol en zijn 'ouder', waar de rol uit ontstaan is
        waarbij elk veld None is indien het niet van toepassing is.
    """
    try:
        rollen_vast = request.session[SESSIONVAR_ROL_PALLET_VAST]
        rollen_functies = request.session[SESSIONVAR_ROL_PALLET_FUNCTIES]
    except KeyError:
        pass
    else:
        for rol in rollen_vast:
            yield (rol, None), (None, None)
        # for
        # let op: session heeft de tuples omgezet in een lijst!
        for child_tup, parent_tup in rollen_functies:
            yield (tuple(child_tup), tuple(parent_tup))
        # for

def rol_unpack_functie(functie):
    """ Onderzoek een functie en zoek de bijbehorende Competitie, DeelCompetitie en NhbVereniging
        geeft None in de posities die niet van toepassing zijn
        Voorbeeld: BKO voor een Competitie geeft geen DeelCompetitie of NhbVereninging
                   CWZ geeft NhbVereniging maar geen Competitie/DeelCompetitie
    """
    return None, None, None


def rol_get_huidige(request):
    """ Deze functie wordt gebruikt door het menusysteem om te kijken welke optionele delen
        van het menu aangezet moeten worden. De gekozen vaste rol of functie resulteert in
        een rol uit de groep Rollen.ROL_xxx
    """
    try:
        return request.session[SESSIONVAR_ROL_HUIDIGE]
    except KeyError:
        pass
    return Rollen.ROL_NONE


def rol_get_huidige_functie(request):
    """ Deze functie wordt gebruikt door het menusysteem om te kijken welke optionele delen
        van het menu aangezet moeten worden. De gekozen vaste rol of functie resulteert in
        een rol uit de groep Rollen.ROL_xxx
    """
    try:
        return request.session[SESSIONVAR_ROL_HUIDIGE], request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE]
    except KeyError:
        pass
    return Rollen.ROL_NONE, None


def rol_get_beschrijving(request):
    try:
        return request.session[SESSIONVAR_ROL_BESCHRIJVING]
    except KeyError:
        return "?"


def rol_bepaal_beschrijving(rol, group_pk=None):
    if group_pk:
        group = Group.objects.get(pk=group_pk)
        grp_naam = group.name
        pos = grp_naam.find(" voor de ")
        if pos >= 0:
            grp_naam = grp_naam[:pos]
    else:
        grp_naam = ""

    if rol == Rollen.ROL_IT:
        beschr = 'IT beheerder'
    elif rol == Rollen.ROL_BB:
        beschr = 'Coordinator'
    elif rol in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
        beschr = grp_naam
    elif rol == Rollen.ROL_CWZ:
        beschr = 'CWZ'
    elif rol == Rollen.ROL_SCHUTTER:
        beschr = 'Schutter'
    else:   # ook rol == None
        # dit komt alleen voor als account geen nhblid is maar wel OTP mag koppelen (is_staff of is_BKO)
        beschr = "Gebruiker"
    return beschr


def rol_is_BB(request):
    """ Geeft True terug als de gebruiker BB rechten heeft en op dit moment BKO als rol gekozen heeft
        Wordt gebruikt om specifieke content voor de BB te tonen
    """
    return rol_get_huidige(request) == Rollen.ROL_BB


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
    return rol_get_huidige(request) in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)


def rol_mag_wisselen(request):
    """ Geeft True terug als deze gebruiker de wissel-van-rol getoond moet worden """
    try:
        return request.session[SESSIONVAR_ROL_MAG_WISSELEN]
    except KeyError:
        pass
    return False


def rol_activeer_rol(request, rolurl):
    """ Activeer een andere rol, als dit toegestaan is
        geen foutmelding of exceptions als het niet mag.
    """
    sessionvars = request.session

    try:
        nwe_rol = url2rol[rolurl]
    except KeyError:
        # onbekende rol
        #print("rol_activeer_rol: onbekende rolurl %s" % repr(rolurl))
        pass
    else:
        try:
            rollen_vast = sessionvars[SESSIONVAR_ROL_PALLET_VAST]
        except KeyError:
            #print("rol_activeer_rol: rollen_vast niet verkrijgbaar")
            pass
        else:
            # kijk of dit een toegestane rol is
            if nwe_rol == Rollen.ROL_NONE or nwe_rol in rollen_vast:
                sessionvars[SESSIONVAR_ROL_HUIDIGE_FUNCTIE] = None
                sessionvars[SESSIONVAR_ROL_HUIDIGE] = nwe_rol
                sessionvars[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(nwe_rol)
            #else:
            #    # TODO: remove this debug print
            #    print("rol_activeer_rol: gevraagde rol (%s) niet in rollen_vast" % rolurl)

    # not recognized --> no change
    return sessionvars  # allows unittest to do sessionvars.save()


def rol_activeer_functie(request, group_pk):
    """ Activeer een andere rol gebaseerd op een Functie
        geen foutmelding of exceptions als het niet mag.
    """
    sessionvars = request.session

    try:
        group_pk = int(group_pk)
    except ValueError:
        pass
    else:
        try:
            rollen_functies = sessionvars[SESSIONVAR_ROL_PALLET_FUNCTIES]
        except KeyError:
            pass
        else:
            # controleer dat de gebruiker deze functie mag hebben
            # (is al eerder vastgesteld en opgeslagen in de sessie)
            #done = False
            for child_tup, parent_tup in rollen_functies:
                functie_rol, functie_group_pk = child_tup
                if functie_group_pk == group_pk:
                    # volledig correcte wissel - sla alles nu op
                    sessionvars[SESSIONVAR_ROL_HUIDIGE] = functie_rol
                    sessionvars[SESSIONVAR_ROL_HUIDIGE_FUNCTIE] = group_pk
                    sessionvars[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(functie_rol, group_pk)
                    #done = True
                    break   # from the for
            # for

            # TODO: test code, to be disabled
            #if not done:
            #    print("rol_activeer_functie: mislukt.\n  TIP: Zit je account wel in de juist groep?\n  TIP: Heb je rol_zet_sessionvars_na_otp_controle aangroepen?\n  TIP: Heb je account_vhpg_is_geaccepteerd aangeroepen?")

    # not recognized --> no change
    return sessionvars  # allows unittest to do sessionvars.save()

# end of file
