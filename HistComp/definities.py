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


COMP_TYPE = [('18', '18m Indoor'),      # note: 18, 25 must be in sync with Competitie.models.AFSTAND
             ('25', '25m1pijl')]

comptype2str = {'18': '18m Indoor',
                '25': '25m 1pijl'}

# end of file
