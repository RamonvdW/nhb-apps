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

HIST_BOOG_DEFAULT = 'R'
HIST_BOOG2STR = {
    'R': 'Recurve',
    'C': 'Compound',
    'BB': 'Barebow',
    'IB': 'Instinctive bow',
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

HIST_TEAM_DEFAULT = 'R'
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
}

HIST_KLASSE2VOLGORDE = {
    # indiv
    '': 1,      # oudere seizoenen hebben geen klasse indicatie

    'Recurve klasse 1': 0,
    'Recurve klasse 2': 0,
    'Recurve klasse 3': 0,
    'Recurve klasse 4': 0,
    'Recurve klasse 5': 0,
    'Recurve klasse 6': 0,
    'Recurve klasse onbekend': 0,
    'Recurve Onder 21 klasse 1': 0,
    'Recurve Onder 21 klasse 2': 0,
    'Recurve Onder 21 klasse onbekend': 0,
    'Recurve Onder 18 klasse 1': 0,
    'Recurve Onder 18 klasse 2': 0,
    'Recurve Onder 18 klasse onbekend': 0,
    'Recurve Onder 14 Jongens': 0,
    'Recurve Onder 14 Meisjes': 0,
    'Recurve Onder 12 Jongens': 0,
    'Recurve Onder 12 Meisjes': 0,
    'Compound klasse 1': 0,
    'Compound klasse 2': 0,
    'Compound klasse onbekend': 0,
    'Compound Onder 21 klasse 1': 0,
    'Compound Onder 21 klasse 2': 0,
    'Compound Onder 21 klasse onbekend': 0,
    'Compound Onder 18 klasse 1': 0,
    'Compound Onder 18 klasse 2': 0,
    'Compound Onder 18 klasse onbekend': 0,
    'Compound Onder 14 Jongens': 0,
    'Compound Onder 14 Meisjes': 0,
    'Compound Onder 12 Jongens': 0,
    'Compound Onder 12 Meisjes': 0,
    'Barebow klasse 1': 0,
    'Barebow klasse 2': 0,
    'Barebow klasse onbekend': 0,
    'Barebow Jeugd klasse 1': 0,
    'Barebow Onder 14 Jongens': 0,
    'Barebow Onder 14 Meisjes': 0,
    'Traditional klasse 1': 0,
    'Traditional klasse 2': 0,
    'Traditional klasse onbekend': 0,
    'Traditional Jeugd klasse 1': 0,
    'Traditional Onder 14 Jongens': 0,
    'Traditional Onder 14 Meisjes': 0,
    'Traditional Onder 12 Jongens': 0,
    'Traditional Onder 12 Meisjes': 0,
    'Longbow klasse 1': 0,
    'Longbow klasse 2': 0,
    'Longbow klasse onbekend': 0,
    'Longbow Jeugd klasse 1': 0,

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
