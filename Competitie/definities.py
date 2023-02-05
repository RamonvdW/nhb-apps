# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from decimal import Decimal


AG_NUL = Decimal('0.000')
AG_LAAGSTE_NIET_NUL = Decimal('0.001')

AFSTANDEN = [('18', 'Indoor'),
             ('25', '25m 1pijl')]

DAGDELEN = [('GN', "Geen voorkeur"),
            ('AV', "'s Avonds"),
            ('MA', "Maandag"),
            ('MAa', "Maandagavond"),
            ('DI', "Dinsdag"),
            ('DIa', "Dinsdagavond"),
            ('WO', "Woensdag"),
            ('WOa', "Woensdagavond"),
            ('DO', "Donderdag"),
            ('DOa', "Donderdagavond"),
            ('VR', "Vrijdag"),
            ('VRa', "Vrijdagavond"),
            ('ZAT', "Zaterdag"),
            ('ZAo', "Zaterdagochtend"),
            ('ZAm', "Zaterdagmiddag"),
            ('ZAa', "Zaterdagavond"),
            ('ZON', "Zondag"),
            ('ZOo', "Zondagochtend"),
            ('ZOm', "Zondagmiddag"),
            ('ZOa', "Zondagavond"),
            ('WE', "Weekend")]

DAGDEEL2LABEL = {
    'GN': ("Geen", "Geen voorkeur"),
    'AV': ("Avond", "'s Avonds"),
    'MA': ("M", "Maandag"),
    'MAa': ("M-Av", "Maandagavond"),
    'DI': ("Di", "Dinsdag"),
    'DIa': ("Di-Av", "Dinsdagavond"),
    'WO': ("W", "Woensdag"),
    'WOa': ("W-Av", "Woensdagavond"),
    'DO': ("Do", "Donderdag"),
    'DOa': ("Do-Av", "Donderdagavond"),
    'VR': ("V", "Vrijdag"),
    'VRa': ("V-Av", "Vrijdagavond"),
    'ZAT': ("Za", "Zaterdag"),
    'ZAo': ("Za-Och", "Zaterdagochtend"),
    'ZAm': ("Zo-Mi", "Zaterdagmiddag"),
    'ZAa': ("Za-Av", "Zaterdagavond"),
    'ZON': ("Zo", "Zondag"),
    'ZOo': ("Zo-Och", "Zondagochtend"),
    'ZOm': ("Zo-Mi", "Zondagmiddag"),
    'ZOa': ("Zo-Av", "Zondagavond"),
    'WE': ("Weekend", "Weekend")
}


# Let op: DAGDEEL_AFKORTINGEN moet in dezelfde volgorde zijn als DAGDELEN
DAGDEEL_AFKORTINGEN = tuple([afk for afk, _ in DAGDELEN])

INSCHRIJF_METHODE_1 = '1'       # direct inschrijven op wedstrijd
INSCHRIJF_METHODE_2 = '2'       # verdeel wedstrijdklassen over locaties
INSCHRIJF_METHODE_3 = '3'       # dagdeel voorkeur en quota-plaatsen

INSCHRIJF_METHODES = (
    (INSCHRIJF_METHODE_1, 'Kies wedstrijden'),
    (INSCHRIJF_METHODE_2, 'Naar locatie wedstrijdklasse'),
    (INSCHRIJF_METHODE_3, 'Voorkeur dagdelen')
)

TEAM_PUNTEN_MODEL_TWEE = '2P'                 # head-to-head, via een poule
TEAM_PUNTEN_MODEL_FORMULE1 = 'F1'
TEAM_PUNTEN_MODEL_SOM_SCORES = 'SS'

TEAM_PUNTEN_F1 = (10, 8, 6, 5, 4, 3, 2, 1)

TEAM_PUNTEN = (
    (TEAM_PUNTEN_MODEL_TWEE, 'Twee punten systeem (2/1/0)'),  # alleen bij head-to-head
    (TEAM_PUNTEN_MODEL_SOM_SCORES, 'Cumulatief: som van team totaal elke ronde'),
    (TEAM_PUNTEN_MODEL_FORMULE1, 'Formule 1 systeem (10/8/6/5/4/3/2/1)'),         # afhankelijk van score
)

DEEL_RK = 'RK'
DEEL_BK = 'BK'

DEELNAME_ONBEKEND = '?'
DEELNAME_JA = 'J'
DEELNAME_NEE = 'N'

DEELNAME_CHOICES = [
    (DEELNAME_ONBEKEND, 'Onbekend'),
    (DEELNAME_JA, 'Bevestigd'),
    (DEELNAME_NEE, 'Afgemeld')
]

DEELNAME2STR = {
    DEELNAME_ONBEKEND: 'Onbekend',
    DEELNAME_JA: 'Bevestigd',
    DEELNAME_NEE: 'Afgemeld'
}

MUTATIE_COMPETITIE_OPSTARTEN = 1
MUTATIE_AG_VASTSTELLEN_18M = 2
MUTATIE_AG_VASTSTELLEN_25M = 3
MUTATIE_INITIEEL = 20
MUTATIE_REGIO_TEAM_RONDE = 50
MUTATIE_DOORZETTEN_REGIO_NAAR_RK = 60
MUTATIE_KAMP_CUT = 10
MUTATIE_KAMP_AFMELDEN = 30
MUTATIE_KAMP_AANMELDEN = 40
MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK = 70

MUTATIE_TO_STR = {
    MUTATIE_AG_VASTSTELLEN_18M: "AG vaststellen 18m",
    MUTATIE_AG_VASTSTELLEN_25M: "AG vaststellen 25m",
    MUTATIE_COMPETITIE_OPSTARTEN: "competitie opstarten",
    MUTATIE_INITIEEL: "initieel",
    MUTATIE_KAMP_CUT: "RK/BK cut aanpassen",
    MUTATIE_KAMP_AFMELDEN: "RK/BK afmelden",
    MUTATIE_KAMP_AANMELDEN: "RK/BK aanmelden",
    MUTATIE_REGIO_TEAM_RONDE: "regio team ronde",
    MUTATIE_DOORZETTEN_REGIO_NAAR_RK: "doorzetten regio naar RK",
    MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK: "doorzetten indiv RK naar BK",
}

KAMP_RANK_UNKNOWN = 99
KAMP_RANK_NO_SHOW = 32000
KAMP_RANK_RESERVE = 32001

# end of file
