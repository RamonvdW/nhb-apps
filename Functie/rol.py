# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Ondersteuning voor de rollen binnen de applicatie """

from django.contrib.sessions.backends.db import SessionStore
from Account.operations.otp import otp_is_controle_gelukt
from Account.models import AccountSessions, get_account
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import Kampioenschap
from Functie.definities import Rollen, rol2url, url2rol
from Functie.models import Functie
from Functie.operations import account_needs_vhpg, account_needs_otp
from Functie.scheids import zet_sessionvar_is_scheids
from Overig.helpers import get_safe_from_ip
from Vereniging.models import Vereniging
from types import SimpleNamespace
from typing import Tuple
import logging

my_logger = logging.getLogger('MH.Functie')

SESSIONVAR_ROL_PALLET_VAST = 'gebruiker_rol_pallet_vast'
SESSIONVAR_ROL_PALLET_FUNCTIES = 'gebruiker_rol_pallet_functies'
SESSIONVAR_ROL_MAG_WISSELEN = 'gebruiker_rol_mag_wisselen'
SESSIONVAR_ROL_HUIDIGE = 'gebruiker_rol_huidige'
SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK = 'gebruiker_rol_functie_pk'
SESSIONVAR_ROL_BESCHRIJVING = 'gebruiker_rol_beschrijving'


def functie_expandeer_rol(functie_cache, ver_cache, rol_in, functie_in):
    """ Plug-in van de Functie.rol module om een groep/functie te expanderen naar onderliggende functies
        Voorbeeld: RKO rayon 3 --> RCL regios 109, 110, 111, 112
        Deze functie yield (rol, functie_pk)
    """
    if rol_in == Rollen.ROL_BB:
        # deze rol mag de functie BKO (en nog een paar) aannemen
        for pk, obj in functie_cache.items():
            if obj.rol == 'BKO':
                yield Rollen.ROL_BKO, obj.pk
            elif obj.rol == 'MO':
                yield Rollen.ROL_MO, obj.pk
            elif obj.rol == 'MWZ':
                yield Rollen.ROL_MWZ, obj.pk
            elif obj.rol == 'MWW':
                yield Rollen.ROL_MWW, obj.pk
            elif obj.rol == 'SUP':
                yield Rollen.ROL_SUP, obj.pk
            elif obj.rol == 'CS':
                yield Rollen.ROL_CS, obj.pk
        # for

        # deze functie mag de HWL van vereniging in regio 100 aannemen
        for pk, obj in functie_cache.items():
            if obj.rol == 'HWL' and obj.koppel_aan_bb:
                yield Rollen.ROL_HWL, obj.pk
        # for

    if functie_in:
        if functie_in.rol == "BKO":
            # expandeer naar de RKO rollen
            for pk, obj in functie_cache.items():
                if obj.rol == 'RKO' and obj.comp_type == functie_in.comp_type:
                    yield Rollen.ROL_RKO, obj.pk
            # for

            # expandeer naar de HWL van verenigingen gekozen voor de BK's
            qset = (Kampioenschap
                    .objects
                    .filter(competitie__afstand=functie_in.comp_type,
                            deel=DEEL_BK)
                    .prefetch_related('rk_bk_matches'))
            ver_nrs = list()
            for deelkamp in qset:
                ver_nrs.extend(list(deelkamp
                                    .rk_bk_matches
                                    .select_related('vereniging')
                                    .values_list('vereniging__ver_nr', flat=True)))
            # for

            # zoek de HWL functies op
            for pk, obj in functie_cache.items():
                if obj.rol == 'HWL' and obj.ver_nr in ver_nrs:
                    yield Rollen.ROL_HWL, obj.pk
            # for

        if functie_in.rol == "RKO":
            # expandeer naar de RCL rollen binnen het rayon
            for pk, obj in functie_cache.items():
                if obj.rol == 'RCL' and obj.comp_type == functie_in.comp_type:
                    if obj.regio_rayon_nr == functie_in.rayon.rayon_nr:
                        yield Rollen.ROL_RCL, obj.pk
            # for

            # expandeer naar de HWL van verenigingen gekozen voor de RKs
            qset = (Kampioenschap
                    .objects
                    .filter(competitie__afstand=functie_in.comp_type,
                            deel=DEEL_RK,
                            rayon=functie_in.rayon)
                    .prefetch_related('rk_bk_matches'))
            ver_nrs = list()
            for deelkamp in qset:
                ver_nrs.extend(list(deelkamp
                                    .rk_bk_matches
                                    .select_related('vereniging')
                                    .values_list('vereniging__ver_nr', flat=True)))
            # for

            # zoek de HWL functies op
            for pk, obj in functie_cache.items():
                if obj.rol == 'HWL' and obj.ver_nr in ver_nrs:
                    yield Rollen.ROL_HWL, obj.pk
            # for

        if functie_in.rol == "RCL":
            # expandeer naar de HWL rollen van de verenigingen binnen de regio
            # vind alle verenigingen in deze regio
            if len(ver_cache) == 0:
                for ver in (Vereniging
                            .objects
                            .select_related('regio')
                            .only('ver_nr', 'regio__regio_nr')):
                    store = SimpleNamespace()
                    store.pk = ver.pk
                    store.ver_nr = ver.ver_nr
                    store.regio_nr = ver.regio.regio_nr
                    ver_cache[store.ver_nr] = store
                # for

                # voorkom herhaaldelijke queries tijdens test zonder vereniging
                if len(ver_cache) == 0:
                    ver_cache[0] = 0

            # zoek alle verenigingen in de regio van deze RCL
            verenigingen = list()
            for ver_nr, ver in ver_cache.items():
                if ver_nr != 0 and ver.regio_nr == functie_in.regio.regio_nr:
                    verenigingen.append(ver_nr)
            # for

            # zoek de HWL functies op
            for pk, obj in functie_cache.items():
                if obj.rol == 'HWL' and obj.ver_nr in verenigingen:
                    yield Rollen.ROL_HWL, obj.pk
            # for

        if functie_in.rol == 'SEC':
            # secretaris mag HWL worden, binnen de vereniging
            for pk, obj in functie_cache.items():
                if obj.rol == 'HWL' and obj.ver_nr == functie_in.vereniging.ver_nr:
                    yield Rollen.ROL_HWL, obj.pk

        if functie_in.rol == 'HWL':
            # expandeer naar de WL rollen binnen dezelfde vereniging
            for pk, obj in functie_cache.items():
                if obj.rol == 'WL' and obj.ver_nr == functie_in.vereniging.ver_nr:
                    yield Rollen.ROL_WL, obj.pk


def rol_bepaal_hulp_rollen(functie_cache, ver_cache, rol, functie_pk):
    """ Deze functie roept alle geregistreerde expandeer functies aan
        om de afgeleide rollen van een functie te krijgen.
    """
    nwe_functies = list()

    # WL is eindstation, dus geen tijd aan spenderen
    if rol != Rollen.ROL_WL:
        functie = functie_cache[functie_pk].obj
        parent_tup = (rol, functie_pk)
        for nwe_tup in functie_expandeer_rol(functie_cache, ver_cache, rol, functie):
            tup = (nwe_tup, parent_tup)
            nwe_functies.append(tup)
        # for

        # print("rol_bepaal_hulp_rechten:")
        # print("   in: rol=%s, functie_pk=%s" % (rol, functie_pk))
        # if len(nwe_functies):
        #     for tup in nwe_functies:
        #         print("  out: %s" % repr(tup))
        # else:
        #     print("  out: []")

    return nwe_functies


def rol_zet_sessionvars(account, request):
    """ zet een paar session variabelen die gebruikt worden om de rol te beheren
        deze functie wordt aangeroepen vanuit de Account.LoginView

        session variables
            gebruiker_rol_mag_wisselen: gebruik van de Plein.WisselVanRolView
    """
    rollen_vast = list()            # list of rol
    rollen_functies = list()        # list of tuple(rol, functie_pk)

    # lees de functie tabel eenmalig in en kopieer alle informatie
    # om verdere queries te voorkomen
    functie_cache = dict()
    functie_rcl = dict()        # [regio nummer] = (functie_pk, functie_pk)

    for obj in (Functie
                .objects
                .select_related('rayon',
                                'regio',
                                'regio__rayon',
                                'vereniging',
                                'vereniging__regio')
                .only('rol',
                      'comp_type',
                      'regio__regio_nr',
                      # 'regio__rayon_nr',      # warning: does not work!
                      'rayon__rayon_nr',
                      'regio__rayon__rayon_nr',
                      'vereniging__ver_nr',
                      'vereniging__regio__regio_nr')):
        func = SimpleNamespace()
        func.pk = obj.pk
        func.obj = obj
        func.rol = obj.rol
        func.koppel_aan_bb = False
        if func.rol == "BKO":
            func.comp_type = obj.comp_type
        elif func.rol == "RKO":
            func.rayon_nr = obj.rayon.rayon_nr
            func.comp_type = obj.comp_type
        elif func.rol == "RCL":
            func.regio_nr = obj.regio.regio_nr
            func.regio_rayon_nr = obj.regio.rayon.rayon_nr
            func.comp_type = obj.comp_type
            try:
                functie_rcl[func.regio_nr].append(func.pk)
            except KeyError:
                functie_rcl[func.regio_nr] = [func.pk]
        elif func.rol in ("HWL", "WL", "SEC"):
            func.ver_nr = obj.vereniging.ver_nr
            if func.rol == 'HWL' and obj.vereniging.regio.regio_nr == 100:
                func.koppel_aan_bb = True
        functie_cache[obj.pk] = func
    # for

    ver_cache = dict()          # wordt gevuld als er behoefte is

    if account.is_authenticated:        # pragma: no branch
        show_vhpg, _ = account_needs_vhpg(account)
        if otp_is_controle_gelukt(request) and not show_vhpg:
            if account.is_staff or account.is_BB:
                rollen_vast.append(Rollen.ROL_BB)
                parent_tup = (Rollen.ROL_BB, None)
                for nwe_tup in functie_expandeer_rol(functie_cache, ver_cache, Rollen.ROL_BB, None):
                    tup = (nwe_tup, parent_tup)
                    rollen_functies.append(tup)
                # for

            # analyseer de gekoppelde functies van dit account
            parent_tup = (None, None)
            for functie in account.functie_set.only('rol').all():
                rol = None
                if functie.rol == "BKO":
                    rol = Rollen.ROL_BKO
                elif functie.rol == "RKO":
                    rol = Rollen.ROL_RKO
                elif functie.rol == "RCL":
                    rol = Rollen.ROL_RCL
                elif functie.rol == "HWL":
                    rol = Rollen.ROL_HWL
                elif functie.rol == "WL":
                    rol = Rollen.ROL_WL
                elif functie.rol == "SEC":
                    rol = Rollen.ROL_SEC
                elif functie.rol == "MO":
                    rol = Rollen.ROL_MO
                elif functie.rol == "MWZ":
                    rol = Rollen.ROL_MWZ
                elif functie.rol == "MWW":
                    rol = Rollen.ROL_MWW
                elif functie.rol == "SUP":
                    rol = Rollen.ROL_SUP
                elif functie.rol == "CS":
                    rol = Rollen.ROL_CS

                if rol:
                    child_tup = (rol, functie.pk)
                    tup = (child_tup, parent_tup)
                    rollen_functies.append(tup)

                    if rol == Rollen.ROL_RCL:
                        # zoek de andere RCL functie van deze regio erbij
                        func = functie_cache[functie.pk]
                        rcl_pks = functie_rcl[func.regio_nr]
                        for pk in rcl_pks:
                            if pk != functie.pk:
                                buur_tup = (rol, pk)
                                tup = (buur_tup, child_tup)
                                rollen_functies.append(tup)
                        # for
            # for

            # probeer elke rol nog verder te expanderen
            te_doorzoeken = rollen_functies[:]
            while len(te_doorzoeken) > 0:
                next_doorzoeken = list()
                for child_tup, parent_tup in te_doorzoeken:
                    # print("\n" + "expanding: child=%s, parent=%s" % (repr(child_tup), (parent_tup)))
                    nwe_functies = rol_bepaal_hulp_rollen(functie_cache, ver_cache, *child_tup)

                    # voorkom dupes (zoals expliciete koppeling en erven van een rol)
                    for nwe_tup in nwe_functies:
                        if nwe_tup not in rollen_functies:
                            rollen_functies.append(nwe_tup)
                            next_doorzoeken.append(nwe_tup)
                    # for
                # for
                te_doorzoeken = next_doorzoeken
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
    if account.is_authenticated:        # pragma: no branch
        if account.sporter_set.count():
            # koppeling met Sporter, dus dit is een (potentiële) Schutter
            rollen_vast.append(Rollen.ROL_SPORTER)
            rol = Rollen.ROL_SPORTER

    request.session[SESSIONVAR_ROL_HUIDIGE] = rol
    request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = None
    request.session[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(rol)

    request.session[SESSIONVAR_ROL_PALLET_VAST] = rollen_vast
    request.session[SESSIONVAR_ROL_PALLET_FUNCTIES] = rollen_functies


def rol_enum_pallet(request):
    """ Doorloop over de mogelijke rollen in het pallet van deze gebruiker
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
            yield tuple(child_tup), tuple(parent_tup)
        # for


def rol_get_huidige(request):
    """ Deze functie wordt gebruikt door het menusysteem om te kijken welke optionele delen
        van het menu aangezet moeten worden. De gekozen vaste rol of functie resulteert in
        een rol uit de groep Rollen.ROL_xxx
    """
    rol = Rollen.ROL_NONE
    if request.user.is_authenticated:
        try:
            rol = request.session[SESSIONVAR_ROL_HUIDIGE]
        except KeyError:
            pass

    return rol


def rol_get_huidige_functie(request) -> Tuple[Rollen, Functie]:
    """ Deze functie wordt gebruikt door het menusysteem om te kijken welke optionele delen
        van het menu aangezet moeten worden. De gekozen vaste rol of functie resulteert in
        een rol uit de groep Rollen.ROL_xxx
    """
    rol = rol_get_huidige(request)
    functie = None
    if request.user.is_authenticated:
        try:
            functie_pk = request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK]
        except KeyError:
            # geen functie opgeslagen
            pass
        else:
            if functie_pk:      # filter None
                try:
                    functie_pk = int(functie_pk)
                    functie = (Functie
                               .objects
                               .select_related('rayon',
                                               'regio',
                                               'regio__rayon',
                                               'vereniging',
                                               'vereniging__regio')
                               .get(pk=functie_pk))
                except (ValueError, Functie.DoesNotExist):
                    # slecht getal of geen bestaande functie
                    pass
                else:
                    bad = ((functie.rol == 'HWL' and rol != Rollen.ROL_HWL) or
                           (functie.rol == 'SEC' and rol != Rollen.ROL_SEC) or
                           (functie.rol == 'RKO' and rol != Rollen.ROL_RKO) or
                           (functie.rol == 'BKO' and rol != Rollen.ROL_BKO) or
                           (functie.rol == 'RCL' and rol != Rollen.ROL_RCL) or
                           (functie.rol == 'MWZ' and rol != Rollen.ROL_MWZ) or
                           (functie.rol == 'MWW' and rol != Rollen.ROL_MWW) or
                           (functie.rol == 'WL' and rol != Rollen.ROL_WL))

                    if bad:
                        # afwijkende combinatie
                        my_logger.warning(
                            '{rol_get_huidige_functie} sessie zegt functie_pk=%s met rol=%s terwijl rol=%s' % (
                                functie_pk, repr(functie.rol), repr(rol)))

    return rol, functie


def rol_get_beschrijving(request):
    try:
        return request.session[SESSIONVAR_ROL_BESCHRIJVING]
    except KeyError:
        return "?"


def rol_bepaal_beschrijving(rol, functie_pk=None):
    if functie_pk:
        functie = Functie.objects.only('beschrijving').get(pk=functie_pk)
        functie_naam = functie.beschrijving
    else:
        functie_naam = ""

    if rol == Rollen.ROL_BB:
        beschr = 'Manager MH'
    elif rol in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL,
                 Rollen.ROL_HWL, Rollen.ROL_WL, Rollen.ROL_SEC,
                 Rollen.ROL_MO, Rollen.ROL_MWZ, Rollen.ROL_MWW,
                 Rollen.ROL_SUP):
        beschr = functie_naam
    elif rol == Rollen.ROL_CS:
        beschr = 'Commissie Scheidsrechters'
    elif rol == Rollen.ROL_SPORTER:
        beschr = 'Sporter'
    else:   # ook rol == None
        # dit komt alleen voor als account geen lid is maar wel OTP mag koppelen (is_staff of is_BB)
        beschr = 'Gebruiker'
    return beschr


def rol_mag_wisselen(request):
    """ Geeft True terug als deze gebruiker de wissel-van-rol getoond moet worden """
    try:
        check = request.session[SESSIONVAR_ROL_MAG_WISSELEN]
    except KeyError:
        return False

    if check == "nieuw":
        # dit wordt gebruikt om nieuwe beheerders het wissel-van-rol menu te laten krijgen
        account = get_account(request)
        rol_zet_sessionvars(account, request)
        check = request.session[SESSIONVAR_ROL_MAG_WISSELEN]

    return check


def rol_activeer_rol(request, rol_url):
    """ Activeer een andere rol, als dit toegestaan is
        geen foutmelding of exceptions als het niet mag.
    """
    try:
        nwe_rol = url2rol[rol_url]
    except KeyError:
        # onbekende rol
        from_ip = get_safe_from_ip(request)
        my_logger.error('%s ROL verzoek activeer onbekende rol %s' % (from_ip, repr(rol_url)))
    else:
        try:
            rollen_vast = request.session[SESSIONVAR_ROL_PALLET_VAST]
        except KeyError:
            pass
        else:
            # kijk of dit een toegestane rol is
            if nwe_rol == Rollen.ROL_NONE or nwe_rol in rollen_vast:
                request.session[SESSIONVAR_ROL_HUIDIGE] = nwe_rol
                request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = None
                request.session[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(nwe_rol)
            else:
                from_ip = get_safe_from_ip(request)
                my_logger.error('%s ROL verzoek activeer niet toegekende rol %s' % (from_ip, repr(rol_url)))

    # not recognized --> no change


def rol_activeer_functie(request, functie):
    """ Activeer een andere rol gebaseerd op een Functie
        geen foutmelding of exceptions als het niet mag.
    """

    try:
        rollen_functies = request.session[SESSIONVAR_ROL_PALLET_FUNCTIES]
    except KeyError:
        pass
    else:
        # controleer dat de gebruiker deze functie mag aannemen
        # (is al eerder vastgesteld en opgeslagen in de sessie)
        for child_tup, parent_tup in rollen_functies:
            mag_rol, mag_functie_pk = child_tup
            if mag_functie_pk == functie.pk:
                # volledig correcte wissel - sla alles nu op
                request.session[SESSIONVAR_ROL_HUIDIGE] = mag_rol
                request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = mag_functie_pk
                request.session[SESSIONVAR_ROL_BESCHRIJVING] = rol_bepaal_beschrijving(mag_rol, mag_functie_pk)
                return
        # for

        # IT en BB mogen wisselen naar elke SEC (dit is niet aan het pallet toegevoegd)
        if request.user.is_authenticated:                       # pragma: no branch
            if otp_is_controle_gelukt(request):                 # pragma: no branch
                account = get_account(request)
                if account.is_staff or account.is_BB:
                    # we komen hier alleen voor rollen die niet al in het pallet zitten bij IT/BB
                    if functie.rol == 'SEC':                    # pragma: no branch
                        request.session[SESSIONVAR_ROL_HUIDIGE] = Rollen.ROL_SEC
                        request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = functie.pk
                        request.session[SESSIONVAR_ROL_BESCHRIJVING] = functie.beschrijving
                        return

    # not recognized --> no change


def rol_bepaal_beschikbare_rollen(request, account):
    """ Deze functie wordt aangeroepen vanuit diverse punten in Account en Functie om de
        [mogelijk gewijzigde] rollen te laten evalueren en onthouden in session variabelen.

        Geen return value
    """
    rol_zet_sessionvars(account, request)
    zet_sessionvar_is_scheids(account, request)


def rol_bepaal_beschikbare_rollen_opnieuw(request):
    """ Deze functie kan gebruik worden als de beschikbare keuzes veranderd zijn,
        zoals na het aanmaken van een nieuwe competitie.
        Hierdoor hoeft de gebruiker niet opnieuw in te loggen om deze mogelijkheden te krijgen.
    """
    account = get_account(request)

    rol, functie = rol_get_huidige_functie(request)
    rol_zet_sessionvars(account, request)
    zet_sessionvar_is_scheids(account, request)
    if functie:
        rol_activeer_functie(request, functie)
    else:
        rol_activeer_rol(request, rol2url[rol])


def rol_activeer_wissel_van_rol_menu_voor_account(account):
    """ Deze functie zorgt ervoor dat nieuwe beheerders het Wissel van Rol menu in beeld krijgen

        Aangezien dit om performance redenen opgeslagen ligt in de sessie van de gebruiker,
        moeten we op zoek naar die sessie en daar een aanpassing in doen.
    """

    # de functie rol_mag_wisselen moet True terug geven en gebruikt informatie opgeslagen in de session vars
    # overschrijf SESSIONVAR_ROL_MAG_WISSELEN voor alle sessies van deze gebruiker met de waarde "nieuw"

    for obj in (AccountSessions
                .objects
                .filter(account=account)):
        session = SessionStore(obj.session.session_key)
        try:
            mag_wisselen = session[SESSIONVAR_ROL_MAG_WISSELEN]
        except KeyError:
            # expired sessions do not have keys
            pass
        else:
            if not mag_wisselen:
                session[SESSIONVAR_ROL_MAG_WISSELEN] = "nieuw"
            session.save()
    # for


# end of file
