# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# accommodatie type

BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT = 'O'
BAAN_TYPE_BINNEN_BUITEN = 'H'               # H = half overdekt
BAAN_TYPE_ONBEKEND = 'X'
BAAN_TYPE_BUITEN = 'B'                      # lift mee op binnenbaan voor adres, plaats
BAAN_TYPE_EXTERN = 'E'
BAAN_TYPE = (('X', 'Onbekend'),
             ('O', 'Volledig overdekte binnenbaan'),
             ('H', 'Binnen-buiten schieten'),
             ('B', 'Buitenbaan'),
             ('E', 'Extern'))
BAANTYPE2STR = {
    'X': 'Onbekend',
    'O': 'Volledig overdekte binnenbaan',
    'H': 'Binnen-buiten schieten',
    'B': 'Buitenbaan',                  # buitenbaan bij de eigen accommodatie
    'E': 'Extern'                       # externe locatie
}

# end of file
