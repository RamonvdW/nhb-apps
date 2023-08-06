# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie
from NhbStructuur.models import NhbRegio


def get_request_regio_nr(request, allow_admin_regio=True):
    """ Geeft het regionummer van de ingelogde sporter terug,
        of 101 als er geen regio vastgesteld kan worden

        Als de gebruiker een rol gekozen heeft, neem dat het regionummer wat bij die rol past
    """
    regio_nr = 101

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.vereniging:
            # HWL, WL
            regio_nr = functie_nu.vereniging.regio.regio_nr
        elif functie_nu.regio:
            # RCL
            regio_nr = functie_nu.regio.regio_nr
        elif functie_nu.rayon:
            # RKO
            regio = (NhbRegio
                     .objects
                     .filter(rayon=functie_nu.rayon,
                             is_administratief=False)
                     .order_by('regio_nr'))[0]
            regio_nr = regio.regio_nr

    elif rol_nu == Rollen.ROL_SPORTER:
        # sporter
        account = request.user
        if account.sporter_set.count() > 0:         # pragma: no branch
            sporter = account.sporter_set.select_related('bij_vereniging__regio').first()
            if sporter.is_actief_lid and sporter.bij_vereniging:
                regio_nr = sporter.bij_vereniging.regio.regio_nr

    if regio_nr == 100 and not allow_admin_regio:
        regio_nr = 101

    return regio_nr


def get_request_rayon_nr(request):
    """ Geeft het rayon nummer van de ingelogde gebruiker/beheerder terug,
        of 1 als er geen rayon vastgesteld kan worden
    """
    rayon_nr = 1

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.vereniging:
            # HWL, WL
            rayon_nr = functie_nu.vereniging.regio.rayon.rayon_nr
        elif functie_nu.regio:
            # RCL
            rayon_nr = functie_nu.regio.rayon.rayon_nr
        elif functie_nu.rayon:
            # RKO
            rayon_nr = functie_nu.rayon.rayon_nr

    elif rol_nu == Rollen.ROL_SPORTER:
        account = request.user
        if account.is_authenticated:                                    # pragma: no branch
            if account.sporter_set.count() > 0:                         # pragma: no branch
                sporter = account.sporter_set.first()
                if sporter.is_actief_lid and sporter.bij_vereniging:
                    rayon_nr = sporter.bij_vereniging.regio.rayon.rayon_nr

    return rayon_nr


def get_sporter_gekozen_bogen(sporter, alle_bogen):
    """ geeft een dictionary terug met een mapping van boog afkorting naar SporterBoog
        geeft een lijst terug met boog afkortingen waarmee wedstrijden geschoten willen worden
    """
    # stel vast welke boogtypen de sporter mee wil schieten (opt-in)
    boog_dict = dict()      # [afkorting] = BoogType()
    for boogtype in alle_bogen:
        boog_dict[boogtype.afkorting] = boogtype
    # for

    boog_afkorting_wedstrijd = list()
    boogafk2sporterboog = dict()       # [boog_afkorting] = SporterBoog()
    # typische 0 tot 20 records (5 WA + vele IFAA)
    for sporterboog in (sporter
                        .sporterboog_set
                        .select_related('boogtype')
                        .order_by('boogtype__volgorde')):
        if sporterboog.voor_wedstrijd:
            afkorting = sporterboog.boogtype.afkorting
            boog_afkorting_wedstrijd.append(afkorting)
            boogafk2sporterboog[afkorting] = sporterboog
    # for

    return boogafk2sporterboog, boog_afkorting_wedstrijd


# end of file
