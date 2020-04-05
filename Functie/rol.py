# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de rollen binnen de NHB applicaties """

from Account.rechten import account_add_plugin_rechten, account_rechten_is_otp_verified
from NhbStructuur.models import NhbVereniging
from Overig.helpers import get_safe_from_ip
from .models import Functie, account_needs_vhpg, account_needs_otp
import logging
import enum

my_logger = logging.getLogger('NHBApps.Functie')

SESSIONVAR_ROL_PALLET_VAST = 'gebruiker_rol_pallet_vast'
SESSIONVAR_ROL_PALLET_FUNCTIES = 'gebruiker_rol_pallet_functies'
SESSIONVAR_ROL_MAG_WISSELEN = 'gebruiker_rol_mag_wisselen'
SESSIONVAR_ROL_HUIDIGE = 'gebruiker_rol_huidige'
SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK = 'gebruiker_rol_functie_pk'
SESSIONVAR_ROL_BESCHRIJVING = 'gebruiker_rol_beschrijving'


class Rollen(enum.IntEnum):
    """ definitie van de rollen met codes
        vertaling naar beschrijvingen in Plein.views
    """
    # rollen staan in prio volgorde
    # dus als je 3 hebt mag je kiezen uit 3 of hoger
    ROL_IT = 1          # IT beheerder
    ROL_BB = 2          # Manager competitiezaken
    ROL_BKO = 3         # BK organisator, specifieke competitie
    ROL_RKO = 4         # RK organisator, specifieke competitie en rayon
    ROL_RCL = 5         # Regiocompetitieleider, specifieke competitie en regio
    ROL_CWZ = 6         # Coordinator wedstrijdzaken vereniging, alle competities
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


# TODO: wrap dit in een class

# plugin administratie

rol_expandeer_functies = list()
roltest_parked_expandeer_functies = None


def rol_zet_plugins(expandeer_functie):
    rol_expandeer_functies.append(expandeer_functie)


def roltest_park_plugins():
    """ Geeft de lijst met plugins mee"""
    global rol_expandeer_functies
    global roltest_parked_expandeer_functies
    roltest_parked_expandeer_functies = rol_expandeer_functies
    rol_expandeer_functies = list()


def roltest_restore_plugins():
    global rol_expandeer_functies
    global roltest_parked_expandeer_functies
    rol_expandeer_functies = roltest_parked_expandeer_functies
    roltest_parked_expandeer_functies = None


def rol_zet_sessionvars_na_login(account, request):
    """ zet een paar session variabelen die gebruikt worden om de rol te beheren
        deze functie wordt aangeroepen vanuit de Account.LoginView

        session variables
            gebruiker_rol_mag_wisselen: gebruik van de Plein.WisselVanRolView
    """
    rollen_vast = list()            # list of rol
    rollen_functies = list()        # list of tuple(rol, functie_pk)

    if account.is_authenticated:
        show_vhpg, _ = account_needs_vhpg(account)
        if account_rechten_is_otp_verified(request) and not show_vhpg:
            if account.is_staff:
                rollen_vast.append(Rollen.ROL_IT)

            if account.is_staff or account.is_BB:
                rollen_vast.append(Rollen.ROL_BB)
                rollen_vast.append(Rollen.ROL_NONE)      # Gebruiker (voor IT en BB)

                for func in rol_expandeer_functies:
                    parent_tup = (Rollen.ROL_BB, None)
                    for nwe_tup in func(Rollen.ROL_BB, None):
                        tup = (nwe_tup, parent_tup)
                        rollen_functies.append(tup)
                    # for
                # for

            # analyseer de gekoppelde functies van dit account
            parent_tup = (None, None)
            for functie in account.functie_set.all():
                rol = None
                if functie.rol == "BKO":
                    rol = Rollen.ROL_BKO
                elif functie.rol == "RKO":
                    rol = Rollen.ROL_RKO
                elif functie.rol == "RCL":
                    rol = Rollen.ROL_RCL
                elif functie.rol == "CWZ":
                    rol = Rollen.ROL_CWZ
                if rol:
                    child_tup = (rol, functie.pk)
                    tup = (child_tup, parent_tup)
                    rollen_functies.append(tup)
            # for

            # probeer elke rol nog verder te expanderen
            te_doorzoeken = rollen_functies[:]
            while len(te_doorzoeken) > 0:
                nwe_functies = list()
                for child_tup, dummy in te_doorzoeken:
                    rol, functie_pk = child_tup
                    functie = Functie.objects.get(pk=functie_pk)
                    parent_tup = (rol, functie_pk)
                    for func in rol_expandeer_functies:
                        for nwe_tup in func(rol, functie):
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
        # if user is otp verified
    # if user is authenticated

    if len(rollen_vast) + len(rollen_functies) > 0:
        request.session[SESSIONVAR_ROL_MAG_WISSELEN] = True
    elif account_needs_otp(account):
        # waarschijnlijk komen er meer rollen beschikbaar na de OTP controle
        request.session[SESSIONVAR_ROL_MAG_WISSELEN] = True
    else:
        request.session[SESSIONVAR_ROL_MAG_WISSELEN] = False

    rol = Rollen.ROL_NONE
    if account.is_authenticated:
        if len(account.nhblid_set.all()):
            # koppeling met NhbLid, dus dit is een (potentiële) Schutter
            rollen_vast.append(Rollen.ROL_SCHUTTER)
            rol = Rollen.ROL_SCHUTTER

    request.session[SESSIONVAR_ROL_HUIDIGE] = rol
    request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = None
    request.session[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(rol)

    request.session[SESSIONVAR_ROL_PALLET_VAST] = rollen_vast
    request.session[SESSIONVAR_ROL_PALLET_FUNCTIES] = rollen_functies


def rol_zet_sessionvars_na_otp_controle(account, request):
    return rol_zet_sessionvars_na_login(account, request)


def rol_plugin_rechten(request, account):
    """ Deze functie wordt aangeroepen vanuit diverse punten in Account.views
        om de [mogelijk gewijzigde] rechten te laten evalueren en onthouden in session variabelen.

        Geen return value
    """
    rol_zet_sessionvars_na_login(account, request)


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
    rol = rol_get_huidige(request)
    functie = None
    try:
        functie_pk = request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK]
    except KeyError:
        # geen functie opgeslagen
        pass
    else:
        try:
            functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # onverwacht!
            pass

    return rol, functie


def rol_get_beschrijving(request):
    try:
        return request.session[SESSIONVAR_ROL_BESCHRIJVING]
    except KeyError:
        return "?"


def rol_bepaal_beschrijving(rol, functie_pk=None):
    if functie_pk:
        functie = Functie.objects.get(pk=functie_pk)
        functie_naam = functie.beschrijving
    else:
        functie_naam = ""

    if rol == Rollen.ROL_IT:
        beschr = 'IT beheerder'
    elif rol == Rollen.ROL_BB:
        beschr = 'Manager competitiezaken'
    elif rol in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ):
        beschr = functie_naam
    elif rol == Rollen.ROL_SCHUTTER:
        beschr = 'Schutter'
    else:   # ook rol == None
        # dit komt alleen voor als account geen nhblid is maar wel OTP mag koppelen (is_staff of is_BB)
        beschr = "Gebruiker"
    return beschr


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
    try:
        nwe_rol = url2rol[rolurl]
    except KeyError:
        # onbekende rol
        from_ip = get_safe_from_ip(request)
        my_logger.error('%s ROL verzoek activeer onbekende rol %s' % (from_ip, repr(rolurl)))
    else:
        try:
            rollen_vast = request.session[SESSIONVAR_ROL_PALLET_VAST]
        except KeyError:
            #print("rol_activeer_rol: rollen_vast niet verkrijgbaar")
            pass
        else:
            # kijk of dit een toegestane rol is
            if nwe_rol == Rollen.ROL_NONE or nwe_rol in rollen_vast:
                request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = None
                request.session[SESSIONVAR_ROL_HUIDIGE] = nwe_rol
                request.session[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(nwe_rol)
            else:
                from_ip = get_safe_from_ip(request)
                my_logger.error('%s ROL verzoek activeer niet toegekende rol %s' % (from_ip, repr(rolurl)))

    # not recognized --> no change


def rol_activeer_functie(request, functie_pk):
    """ Activeer een andere rol gebaseerd op een Functie
        geen foutmelding of exceptions als het niet mag.
    """

    # conversie string (uit url) naar nummer
    try:
        functie_pk = int(functie_pk)
    except ValueError:
        pass
    else:
        try:
            rollen_functies = request.session[SESSIONVAR_ROL_PALLET_FUNCTIES]
        except KeyError:
            pass
        else:
            # controleer dat de gebruiker deze functie mag aannemen
            # (is al eerder vastgesteld en opgeslagen in de sessie)
            for child_tup, parent_tup in rollen_functies:
                mag_rol, mag_functie_pk = child_tup
                if mag_functie_pk == functie_pk:
                    # volledig correcte wissel - sla alles nu op
                    request.session[SESSIONVAR_ROL_HUIDIGE] = mag_rol
                    request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = mag_functie_pk
                    request.session[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(mag_rol, mag_functie_pk)
                    break   # from the for
            # for

    # not recognized --> no change


def rol_evalueer_opnieuw(request):
    """ Deze functie kan gebruik worden als de beschikbare keuzes veranderd zijn,
        zoals na het aanmaken van een nieuwe competitie.
        Hierdoor hoeft de gebruiker niet opnieuw in te loggen om deze mogelijkheden te krijgen.
    """

    rol, functie = rol_get_huidige_functie(request)
    rol_zet_sessionvars_na_otp_controle(request.user, request)
    if functie:
        rol_activeer_functie(request, functie.pk)
    else:
        rol_activeer_rol(request, rol2url[rol])


def functie_expandeer_rol(rol_in, functie_in):
    """ Plug-in van de Functie.rol module om een groep/functie te expanderen naar onderliggende functies
        Voorbeeld: RKO rayon 3 --> RCL regios 109, 110, 111, 112
        Deze functie yield (rol, functie_pk)
    """
    if rol_in == Rollen.ROL_BB:
        # deze rol mag de functie BKO aannemen
        for obj in Functie.objects.filter(rol='BKO'):
            yield Rollen.ROL_BKO, obj.pk
        # for

    if functie_in:
        if functie_in.rol == "BKO":
            # expandeer naar de RKO rollen
            for obj in Functie.objects.filter(comp_type=functie_in.comp_type, rol='RKO'):
                yield Rollen.ROL_RKO, obj.pk
            # for

        if functie_in.rol == "RKO":
            # expandeer naar de RCL rollen binnen het rayon
            for obj in Functie.objects.filter(comp_type=functie_in.comp_type, rol='RCL', nhb_regio__rayon=functie_in.nhb_rayon):
                yield Rollen.ROL_RCL, obj.pk
            # for

        if functie_in.rol == "RCL":
            # expandeer naar de CWZ rollen binnen de regio
            # vind alle verenigingen in deze regio
            for ver in NhbVereniging.objects.filter(regio=functie_in.nhb_regio):
                # zoek de CWZ functie van deze vereniging
                try:
                    functie = Functie.objects.get(rol='CWZ', nhb_ver=ver)
                except Functie.DoesNotExist:
                    pass
                else:
                    yield Rollen.ROL_CWZ, functie.pk
            # for


# registreer de interne rol-expansie functie
rol_zet_plugins(functie_expandeer_rol)

# registreer de rechten plugin
account_add_plugin_rechten(rol_plugin_rechten)

# end of file
