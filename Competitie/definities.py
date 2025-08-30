# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


AFSTANDEN = [('18', 'Indoor'),
             ('25', '25m 1pijl')]

AFSTAND2URL = {
    '18': 'indoor',
    '25': '25m1pijl'
}

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
    'WE': ("Weekend", "Weekend"),
    '': ("?", "?")
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
MUTATIE_AG_VASTSTELLEN_18M = 2      # TODO: remove after 2026-06
MUTATIE_AG_VASTSTELLEN_25M = 3      # TODO: remove after 2026-06
MUTATIE_AG_VASTSTELLEN = 4
MUTATIE_KAMP_CUT = 10
MUTATIE_KAMP_REINIT_TEST = 20
MUTATIE_KAMP_AFMELDEN_INDIV = 30
MUTATIE_KAMP_AANMELDEN_INDIV = 40
MUTATIE_KAMP_TEAMS_NUMMEREN = 45
MUTATIE_REGIO_TEAM_RONDE = 50
MUTATIE_DOORZETTEN_REGIO_NAAR_RK = 60
MUTATIE_EXTRA_RK_DEELNEMER = 61
MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK = 70
MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK = 71
MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV = 80
MUTATIE_KAMP_INDIV_AFSLUITEN = 90
MUTATIE_KAMP_TEAMS_AFSLUITEN = 91
MUTATIE_MAAK_WEDSTRIJDFORMULIEREN = 100
MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN = 101


MUTATIE_TO_STR = {
    MUTATIE_AG_VASTSTELLEN_18M: "AG vaststellen 18m",
    MUTATIE_AG_VASTSTELLEN_25M: "AG vaststellen 25m",
    MUTATIE_AG_VASTSTELLEN: "AG vaststellen",
    MUTATIE_COMPETITIE_OPSTARTEN: "competitie opstarten",
    MUTATIE_KAMP_REINIT_TEST: "(re-)init voor test",
    MUTATIE_KAMP_CUT: "RK/BK cut aanpassen",
    MUTATIE_KAMP_AFMELDEN_INDIV: "RK/BK afmelden",
    MUTATIE_KAMP_AANMELDEN_INDIV: "RK/BK aanmelden",
    MUTATIE_KAMP_TEAMS_NUMMEREN: "RK/BK teams nummeren",
    MUTATIE_REGIO_TEAM_RONDE: "regio team ronde",
    MUTATIE_DOORZETTEN_REGIO_NAAR_RK: "doorzetten regio naar RK",
    MUTATIE_EXTRA_RK_DEELNEMER: "extra RK deelnemer",
    MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK: "doorzetten indiv RK naar BK",
    MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK: "doorzetten teams RK naar BK",
    MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV: "verplaats deelnemer naar andere klasse",
    MUTATIE_KAMP_INDIV_AFSLUITEN: "afsluiten BK indiv",
    MUTATIE_KAMP_TEAMS_AFSLUITEN: "afsluiten BK teams",
    MUTATIE_MAAK_WEDSTRIJDFORMULIEREN: "maak wedstrijdformulieren",
    MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN: "update dirty wedstrijdformulieren",
}

KAMP_RANK_BLANCO = 100
KAMP_RANK_NO_SHOW = 32000
KAMP_RANK_RESERVE = 32001
KAMP_RANK_ALLEEN_TEAM = 32002       # wordt gebruikt bij aanmaken histcomp

# end of file
