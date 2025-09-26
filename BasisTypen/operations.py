# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from BasisTypen.definities import ORGANISATIE_KHSN, ORGANISATIE_WA, ORGANISATIE_WA_STRIKT
from BasisTypen.models import BoogType, TeamType, KalenderWedstrijdklasse


def get_organisatie_boogtypen(organisatie):

    if organisatie == ORGANISATIE_KHSN:
        # nationaal is combinatie van WA en KHSN
        organisaties = (ORGANISATIE_WA, ORGANISATIE_KHSN)
    else:
        organisaties = (organisatie,)

    bogen = (BoogType
             .objects
             .filter(buiten_gebruik=False,
                     organisatie__in=organisaties)
             .order_by('volgorde'))

    return bogen


def get_organisatie_teamtypen(organisatie):

    if organisatie == ORGANISATIE_KHSN:
        # nationaal is combinatie van WA en KHSN
        organisaties = (ORGANISATIE_WA, ORGANISATIE_KHSN)
    else:
        organisaties = (organisatie,)

    bogen = (TeamType
             .objects
             .filter(buiten_gebruik=False,
                     organisatie__in=organisaties)
             .order_by('volgorde'))

    return bogen


def get_organisatie_klassen(organisatie, ook_strikt: bool, filter_bogen=None):

    if organisatie == ORGANISATIE_KHSN:
        # nationaal is combinatie van WA en KHSN
        organisaties = (ORGANISATIE_WA, ORGANISATIE_KHSN)

    elif organisatie == ORGANISATIE_WA and ook_strikt:
        organisaties = (ORGANISATIE_WA, ORGANISATIE_WA_STRIKT)

    else:
        organisaties = (organisatie,)

    klassen = (KalenderWedstrijdklasse
               .objects
               .filter(buiten_gebruik=False,
                       organisatie__in=organisaties)
               .select_related('boogtype',
                               'leeftijdsklasse')
               .order_by('volgorde'))

    if filter_bogen:
        klassen = klassen.filter(boogtype__pk__in=filter_bogen)

    return klassen


# end of file
