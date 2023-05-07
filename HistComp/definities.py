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
    HISTCOMP_TYPE_18: '18m Indoor',
    HISTCOMP_TYPE_25: '25m 1pijl'
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


# end of file
