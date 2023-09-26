# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from BasisTypen.definities import SCHEIDS_BOND, SCHEIDS_INTERNATIONAAL, SCHEIDS_VERENIGING


SCHEIDS2LEVEL = {
    SCHEIDS_INTERNATIONAAL: 'SR5',
    SCHEIDS_BOND: 'SR4',
    SCHEIDS_VERENIGING: 'SR3'
}


BESCHIKBAAR_JA = 'J'
BESCHIKBAAR_NEE = 'N'
BESCHIKBAAR_DENK = 'D'
BESCHIKBAAR_LEEG = '?'

BESCHIKBAAR_CHOICES = (
    (BESCHIKBAAR_LEEG, "Niet ingevuld"),
    (BESCHIKBAAR_JA, "Ja"),
    (BESCHIKBAAR_DENK, "Onzeker"),
    (BESCHIKBAAR_NEE, "Nee"),
)

BESCHIKBAAR2STR = {
    BESCHIKBAAR_LEEG: "Niet ingevuld",
    BESCHIKBAAR_JA: "Ja",
    BESCHIKBAAR_DENK: "Onzeker",
    BESCHIKBAAR_NEE: "Nee",
}


# end of file
