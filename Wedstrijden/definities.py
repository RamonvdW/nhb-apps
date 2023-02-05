# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from BasisTypen.definities import ORGANISATIE_WA, ORGANISATIE_NHB, ORGANISATIE_IFAA

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

WEDSTRIJD_DISCIPLINE_OUTDOOR = 'OD'
WEDSTRIJD_DISCIPLINE_INDOOR = 'IN'
WEDSTRIJD_DISCIPLINE_25M1P = '25'
WEDSTRIJD_DISCIPLINE_CLOUT = 'CL'
WEDSTRIJD_DISCIPLINE_VELD = 'VE'
WEDSTRIJD_DISCIPLINE_RUN = 'RA'
WEDSTRIJD_DISCIPLINE_3D = '3D'

WEDSTRIJD_DISCIPLINES = (
    (WEDSTRIJD_DISCIPLINE_OUTDOOR, 'Outdoor'),
    (WEDSTRIJD_DISCIPLINE_INDOOR, 'Indoor'),               # Indoor = 18m/25m 3pijl
    (WEDSTRIJD_DISCIPLINE_25M1P, '25m 1pijl'),
    (WEDSTRIJD_DISCIPLINE_CLOUT, 'Clout'),
    (WEDSTRIJD_DISCIPLINE_VELD, 'Veld'),
    (WEDSTRIJD_DISCIPLINE_RUN, 'Run Archery'),
    (WEDSTRIJD_DISCIPLINE_3D, '3D')
)

# let op: dit is ook de volgorde waarin ze getoond worden
WEDSTRIJD_DISCIPLINE_TO_STR_WA = {
    WEDSTRIJD_DISCIPLINE_OUTDOOR: 'Outdoor',
    WEDSTRIJD_DISCIPLINE_INDOOR: 'Indoor',
    WEDSTRIJD_DISCIPLINE_VELD: 'Veld',
    WEDSTRIJD_DISCIPLINE_3D: '3D',
    WEDSTRIJD_DISCIPLINE_RUN: 'Run Archery',
    WEDSTRIJD_DISCIPLINE_CLOUT: 'Clout',
    # bewust weggelaten ivm niet gebruikt: flight (ver), ski
}

WEDSTRIJD_DISCIPLINE_TO_STR_NHB = {
    WEDSTRIJD_DISCIPLINE_OUTDOOR: 'Outdoor',
    WEDSTRIJD_DISCIPLINE_INDOOR: 'Indoor',
    WEDSTRIJD_DISCIPLINE_25M1P: '25m 1pijl',
    WEDSTRIJD_DISCIPLINE_VELD: 'Veld',
    WEDSTRIJD_DISCIPLINE_RUN: 'Run Archery',
    WEDSTRIJD_DISCIPLINE_3D: '3D',
    WEDSTRIJD_DISCIPLINE_CLOUT: 'Clout',
}

WEDSTRIJD_DISCIPLINE_TO_STR_IFAA = {
    WEDSTRIJD_DISCIPLINE_3D: '3D',
    WEDSTRIJD_DISCIPLINE_INDOOR: 'Indoor',
    WEDSTRIJD_DISCIPLINE_VELD: 'Veld',
}

ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS = {
    ORGANISATIE_WA: WEDSTRIJD_DISCIPLINE_TO_STR_WA,
    ORGANISATIE_NHB: WEDSTRIJD_DISCIPLINE_TO_STR_NHB,
    ORGANISATIE_IFAA: WEDSTRIJD_DISCIPLINE_TO_STR_IFAA
}


WEDSTRIJD_STATUS_ONTWERP = 'O'
WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING = 'W'
WEDSTRIJD_STATUS_GEACCEPTEERD = 'A'
WEDSTRIJD_STATUS_GEANNULEERD = 'X'

WEDSTRIJD_STATUS = (
    (WEDSTRIJD_STATUS_ONTWERP, 'Ontwerp'),
    (WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING, 'Wacht op goedkeuring'),
    (WEDSTRIJD_STATUS_GEACCEPTEERD, 'Geaccepteerd'),
    (WEDSTRIJD_STATUS_GEANNULEERD, 'Geannuleerd')
)

WEDSTRIJD_STATUS_TO_STR = {
    WEDSTRIJD_STATUS_ONTWERP: 'Ontwerp',
    WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING: 'Wacht op goedkeuring',
    WEDSTRIJD_STATUS_GEACCEPTEERD: 'Geaccepteerd',
    WEDSTRIJD_STATUS_GEANNULEERD: 'Geannuleerd'
}

WEDSTRIJD_WA_STATUS_A = 'A'
WEDSTRIJD_WA_STATUS_B = 'B'

WEDSTRIJD_WA_STATUS = (
    (WEDSTRIJD_WA_STATUS_A, 'A-status'),
    (WEDSTRIJD_WA_STATUS_B, 'B-status')
)

WEDSTRIJD_WA_STATUS_TO_STR = {
    WEDSTRIJD_WA_STATUS_A: 'A-status',
    WEDSTRIJD_WA_STATUS_B: 'B-status'
}

WEDSTRIJD_DUUR_MAX_DAGEN = 5
WEDSTRIJD_DUUR_MAX_UREN = 10         # maximale keuze voor de duur van een sessie

WEDSTRIJD_BEGRENZING_LANDELIJK = 'L'
WEDSTRIJD_BEGRENZING_VERENIGING = 'V'
WEDSTRIJD_BEGRENZING_REGIO = 'G'
WEDSTRIJD_BEGRENZING_RAYON = 'Y'

WEDSTRIJD_BEGRENZING = (
    (WEDSTRIJD_BEGRENZING_LANDELIJK, 'Landelijk'),
    (WEDSTRIJD_BEGRENZING_RAYON, 'Rayon'),
    (WEDSTRIJD_BEGRENZING_REGIO, 'Regio'),
    (WEDSTRIJD_BEGRENZING_VERENIGING, 'Vereniging'),
)

WEDSTRIJD_BEGRENZING_TO_STR = {
    WEDSTRIJD_BEGRENZING_LANDELIJK: 'Alle sporters (landelijk)',
    WEDSTRIJD_BEGRENZING_RAYON: 'Sporters in het rayon',
    WEDSTRIJD_BEGRENZING_REGIO: 'Sporters in de regio',
    WEDSTRIJD_BEGRENZING_VERENIGING: 'Sporters van de organiserende vereniging',
}

WEDSTRIJD_ORGANISATIE_TO_STR = {
    ORGANISATIE_WA: 'WA',
    ORGANISATIE_NHB: 'NHB',
    ORGANISATIE_IFAA: 'IFAA'
}

INSCHRIJVING_STATUS_RESERVERING_MANDJE = 'R'        # moet nog omgezet worden in een bestelling
INSCHRIJVING_STATUS_RESERVERING_BESTELD = 'B'       # moet nog betaald worden
INSCHRIJVING_STATUS_DEFINITIEF = 'D'                # is betaald
INSCHRIJVING_STATUS_AFGEMELD = 'A'

INSCHRIJVING_STATUS_CHOICES = (
    (INSCHRIJVING_STATUS_RESERVERING_MANDJE, "Reservering"),
    (INSCHRIJVING_STATUS_RESERVERING_BESTELD, "Besteld"),
    (INSCHRIJVING_STATUS_DEFINITIEF, "Definitief"),
    (INSCHRIJVING_STATUS_AFGEMELD, "Afgemeld")
)

INSCHRIJVING_STATUS_TO_STR = {
    INSCHRIJVING_STATUS_RESERVERING_MANDJE: 'Gereserveerd, in mandje',
    INSCHRIJVING_STATUS_RESERVERING_BESTELD: 'Gereserveerd, wacht op betaling',
    INSCHRIJVING_STATUS_DEFINITIEF: 'Inschrijving is definitief',
    INSCHRIJVING_STATUS_AFGEMELD: 'Afgemeld',
}

INSCHRIJVING_STATUS_TO_SHORT_STR = {
    INSCHRIJVING_STATUS_RESERVERING_MANDJE: 'In mandje',
    INSCHRIJVING_STATUS_RESERVERING_BESTELD: 'Besteld',
    INSCHRIJVING_STATUS_DEFINITIEF: 'Definitief',
    INSCHRIJVING_STATUS_AFGEMELD: 'Afgemeld',
}


WEDSTRIJD_KORTING_SPORTER = 's'
WEDSTRIJD_KORTING_VERENIGING = 'v'
WEDSTRIJD_KORTING_COMBI = 'c'

WEDSTRIJD_KORTING_SOORT_CHOICES = (
    (WEDSTRIJD_KORTING_SPORTER, 'Sporter'),
    (WEDSTRIJD_KORTING_VERENIGING, 'Vereniging'),
    (WEDSTRIJD_KORTING_COMBI, 'Combi')
)

WEDSTRIJD_KORTING_SOORT_TO_STR = {
    WEDSTRIJD_KORTING_SPORTER: 'Sporter',
    WEDSTRIJD_KORTING_VERENIGING: 'Vereniging',
    WEDSTRIJD_KORTING_COMBI: 'Combi'
}


# end of file
