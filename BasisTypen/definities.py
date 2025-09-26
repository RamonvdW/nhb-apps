# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# leden zijn aspirant tot en met het jaar waarin ze 13 worden (=Onder 14)
MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT = 13

# leden zijn jeugdlid tot en met het jaar waarin ze 20 worden
MAXIMALE_LEEFTIJD_JEUGD = 20

GESLACHT_MAN = 'M'          # geregistreerd geslacht / voor wedstrijdklassen
GESLACHT_VROUW = 'V'        # geregistreerd geslacht / voor wedstrijdklassen
GESLACHT_ANDERS = 'X'       # geregistreerd geslacht
GESLACHT_ALLE = 'A'         # genderneutraal voor wedstrijdklassen

GESLACHT2STR = {GESLACHT_MAN: 'Man',
                GESLACHT_VROUW: 'Vrouw',
                GESLACHT_ANDERS: 'Anders',
                GESLACHT_ALLE: 'Alle'}

# geregistreerde geslacht van sporters: M/V/X
GESLACHT_MVX = [(GESLACHT_MAN, 'Man'),
                (GESLACHT_VROUW, 'Vrouw'),
                (GESLACHT_ANDERS, 'Anders')]

# als voorkeur voor wedstrijden herkennen we alleen M/V
GESLACHT_MV = [(GESLACHT_MAN, 'Man'),
               (GESLACHT_VROUW, 'Vrouw')]

# keuzemogelijkheden bij het instellen van bovenstaande
GESLACHT_MV_MEERVOUD = [(GESLACHT_MAN, 'Mannen'),
                        (GESLACHT_VROUW, 'Vrouwen')]

# mogelijk geslacht van sporters in wedstrijden: M/V/A
WEDSTRIJDGESLACHT_MVA = [(GESLACHT_MAN, 'Man'),
                         (GESLACHT_VROUW, 'Vrouw'),
                         (GESLACHT_ALLE, 'Genderneutraal')]

BLAZOEN_40CM = '40'
BLAZOEN_60CM = '60'
BLAZOEN_60CM_4SPOT = '4S'
BLAZOEN_DT = 'DT'
BLAZOEN_WENS_DT = 'DTw'
BLAZOEN_WENS_4SPOT = '4Sw'

BLAZOEN2STR = {
    BLAZOEN_40CM: '40cm',
    BLAZOEN_60CM: '60cm',
    BLAZOEN_60CM_4SPOT: '60cm 4-spot',
    BLAZOEN_DT: 'Dutch Target',
    BLAZOEN_WENS_DT: 'Dutch Target (wens)',
    BLAZOEN_WENS_4SPOT: '60cm 4-spot (wens)'
}

BLAZOEN2STR_COMPACT = {
    BLAZOEN_40CM: '40cm',
    BLAZOEN_60CM: '60cm',
    BLAZOEN_60CM_4SPOT: '60cm 4spot',
    BLAZOEN_DT: 'DT',
    BLAZOEN_WENS_DT: 'DT wens',
    BLAZOEN_WENS_4SPOT: '4spot wens'
}

COMPETITIE_BLAZOENEN = {
    '18': (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_WENS_DT, BLAZOEN_60CM),
    '25': (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT)
}

BLAZOEN_CHOICES = [
    (BLAZOEN_40CM, '40cm'),
    (BLAZOEN_60CM, '60cm'),
    (BLAZOEN_60CM_4SPOT, '60cm 4-spot'),
    (BLAZOEN_DT, 'Dutch Target')
]

# organisatie, om boogtype, leeftijdsklassen etc. uit elkaar te kunnen houden binnen 1 tabel
ORGANISATIE_WA = 'W'            # World Archery
ORGANISATIE_KHSN = 'N'          # Nationaal
ORGANISATIE_IFAA = 'F'          # International Field Archery Association
ORGANISATIE_WA_STRIKT = 'S'     # WA klassen begrensd op eigen leeftijd (voor NK)

ORGANISATIES = [
    (ORGANISATIE_WA, 'World Archery'),
    (ORGANISATIE_KHSN, 'KHSN'),
    (ORGANISATIE_IFAA, 'IFAA'),
    (ORGANISATIE_WA_STRIKT, 'WA strikt'),
]

ORGANISATIES2SHORT_STR = {
    ORGANISATIE_WA: 'WA',
    ORGANISATIE_KHSN: 'KHSN',
    ORGANISATIE_IFAA: 'IFAA',
}

# wordt gebruikt in de zin:
# Beschikbare disciplines van ...
ORGANISATIES2LONG_STR = {
    ORGANISATIE_WA: 'World Archery',
    ORGANISATIE_KHSN: 'de KHSN',
    ORGANISATIE_IFAA: 'de IFAA',
}

BOOGTYPE_AFKORTING_RECURVE = 'R'


# rol van Scheidsrechter, bepaald via opleidingscodes
SCHEIDS_NIET = 'N'
SCHEIDS_BOND = 'B'
SCHEIDS_VERENIGING = 'V'
SCHEIDS_INTERNATIONAAL = 'I'
SCHEIDS_CHOICES = (
    (SCHEIDS_NIET, "Niet"),
    (SCHEIDS_BOND, "Bondsscheidsrechter"),
    (SCHEIDS_VERENIGING, "Verenigingsscheidsrechter"),
    (SCHEIDS_INTERNATIONAAL, "Internationaal Scheidsrechter"),
)
SCHEIDS_TO_STR = {
    SCHEIDS_BOND: "Bondsscheidsrechter",
    SCHEIDS_VERENIGING: "Verenigingsscheidsrechter",
    SCHEIDS_INTERNATIONAAL: "Internationaal Scheidsrechter",
}


# end of file
