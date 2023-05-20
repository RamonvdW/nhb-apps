# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

HISTCOMP_RK = 'R'
HISTCOMP_BK = 'B'

HISTCOMP_CHOICES_RK_BK = (
    (HISTCOMP_RK, 'RK'),
    (HISTCOMP_BK, 'BK'),
)

HISTCOMP_TYPE_18 = '18'    # note: 18, 25 must be in sync with Competitie.definities.AFSTAND
HISTCOMP_TYPE_25 = '25'

HISTCOMP_TYPE = [
    (HISTCOMP_TYPE_18, 'Indoor'),
    (HISTCOMP_TYPE_25, '25m1pijl')
]

HISTCOMP_TYPE2STR = {
    HISTCOMP_TYPE_18: 'Indoor',
    HISTCOMP_TYPE_25: '25m1pijl'
}

HISTCOMP_TYPE2URL = {
    HISTCOMP_TYPE_18: 'indoor',
    HISTCOMP_TYPE_25: '25m1pijl'
}

URL2HISTCOMP_TYPE = {
    'indoor': HISTCOMP_TYPE_18,
    '18m': HISTCOMP_TYPE_18,
    '25m1pijl': HISTCOMP_TYPE_25,
    '25m1p': HISTCOMP_TYPE_25,
    '25m': HISTCOMP_TYPE_25,
}

HIST_BOGEN_DEFAULT = ('R', 'C', 'BB', 'TR', 'LB')

HIST_BOOG_DEFAULT = 'R'
HIST_BOOG2STR = {
    'R': 'Recurve',
    'C': 'Compound',
    'BB': 'Barebow',
    'IB': 'Instinctive',
    'LB': 'Longbow',
    'TR': 'Traditional',
}

HIST_BOOG2URL = {
    'R': 'recurve',
    'C': 'compound',
    'BB': 'barebow',
    'LB': 'longbow',
    'TR': 'traditional',
    'IB': 'instinctive'
}

URL2HIST_BOOG = {
    'recurve': 'R',
    'compound': 'C',
    'barebow': 'BB',
    'longbow': 'LB',
    'traditional': 'TR',
    'instinctive': 'IB',
}

HIST_TEAM_TYPEN_DEFAULT = ('R', 'C', 'BB', 'TR', 'LB')

HIST_TEAM_DEFAULT = 'R'
HIST_TEAM2STR = {
    'R': 'Recurve',
    'C': 'Compound',
    'BB': 'Barebow',
    'LB': 'Longbow',
    'TR': 'Traditional',
    'IB': 'Instinctive',
}

HIST_TEAM2URL = {
    'R': 'recurve',
    'C': 'compound',
    'BB': 'barebow',
    'LB': 'longbow',
    'TR': 'traditional',
    'IB': 'instinctive'
}

URL2HIST_TEAM = {
    'recurve': 'R',
    'compound': 'C',
    'barebow': 'BB',
    'longbow': 'LB',
    'traditional': 'TR',
    'instinctive': 'IB',
}

HIST_INTERLAND_BOGEN = ('R', 'C', 'BB', 'TR', 'LB')

HIST_KLASSE2VOLGORDE = {
    # indiv
    '': 1,      # oudere seizoenen hebben geen klasse indicatie
    'Recurve': 1,
    'Compound': 1,
    'Barebow': 1,
    'Instinctive': 1,
    'Longbow': 1,

    'Recurve klasse 1': 11,
    'Recurve klasse 2': 12,
    'Recurve klasse 3': 13,
    'Recurve klasse 4': 14,
    'Recurve klasse 5': 15,
    'Recurve klasse 6': 16,
    'Recurve klasse onbekend': 17,
    'Recurve Onder 21 klasse 1': 18,
    'Recurve Onder 21 klasse 2': 19,
    'Recurve Onder 21 klasse onbekend': 20,
    'Recurve Onder 18 klasse 1': 21,
    'Recurve Onder 18 klasse 2': 22,
    'Recurve Onder 18 klasse onbekend': 23,
    'Recurve Onder 14 Jongens': 24,
    'Recurve Onder 14 Meisjes': 25,
    'Recurve Onder 12 Jongens': 26,
    'Recurve Onder 12 Meisjes': 27,
    'Compound klasse 1': 30,
    'Compound klasse 2': 31,
    'Compound klasse onbekend': 32,
    'Compound Onder 21 klasse 1': 33,
    'Compound Onder 21 klasse 2': 34,
    'Compound Onder 21 klasse onbekend': 35,
    'Compound Onder 18 klasse 1': 36,
    'Compound Onder 18 klasse 2': 37,
    'Compound Onder 18 klasse onbekend': 38,
    'Compound Onder 14 Jongens': 39,
    'Compound Onder 14 Meisjes': 40,
    'Compound Onder 12 Jongens': 41,
    'Compound Onder 12 Meisjes': 42,
    'Barebow klasse 1': 50,
    'Barebow klasse 2': 51,
    'Barebow klasse onbekend': 52,
    'Barebow Jeugd klasse 1': 53,
    'Barebow Onder 14 Jongens': 54,
    'Barebow Onder 14 Meisjes': 55,
    'Barebow Onder 12 Jongens': 56,
    'Barebow Onder 12 Meisjes': 57,
    'Traditional klasse 1': 60,
    'Traditional klasse 2': 61,
    'Traditional klasse onbekend': 62,
    'Traditional Jeugd klasse 1': 63,
    'Traditional Onder 14 Jongens': 64,
    'Traditional Onder 14 Meisjes': 65,
    'Traditional Onder 12 Jongens': 66,
    'Traditional Onder 12 Meisjes': 67,
    'Longbow klasse 1': 70,
    'Longbow klasse 2': 71,
    'Longbow klasse onbekend': 72,
    'Longbow Jeugd klasse 1': 73,
    'Longbow Onder 14 Jongens': 74,
    'Longbow Onder 14 Meisjes': 75,
    'Longbow Onder 12 Jongens': 76,
    'Longbow Onder 12 Meisjes': 77,

    # teams
    'Recurve klasse ERE': 100,
    'Recurve klasse A': 101,
    'Recurve klasse B': 102,
    'Recurve klasse C': 103,
    'Recurve klasse D': 104,
    'Compound klasse ERE': 110,
    'Compound klasse A': 111,
    'Barebow klasse ERE': 120,
    'Traditional klasse ERE': 130,
    'Longbow klasse ERE': 140,
}


# end of file
