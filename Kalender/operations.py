# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from BasisTypen.models import BoogType, KalenderWedstrijdklasse, ORGANISATIE_NHB, ORGANISATIE_WA


def get_toegestane_boogtypen(organisatie):

    if organisatie == ORGANISATIE_NHB:
        # nationaal is combinatie van WA en NAT
        organisaties = (ORGANISATIE_WA, ORGANISATIE_NHB)
    else:
        organisaties = (organisatie,)

    bogen = (BoogType
             .objects
             .filter(buiten_gebruik=False,
                     organisatie__in=organisaties)
             .order_by('volgorde'))

    return bogen


def get_toegestane_klassen(organisatie, filter_bogen=None):

    if organisatie == ORGANISATIE_NHB:
        # nationaal is combinatie van WA en NAT
        organisaties = (ORGANISATIE_WA, ORGANISATIE_NHB)
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
