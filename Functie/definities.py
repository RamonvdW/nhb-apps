# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import enum


class Rol(enum.IntEnum):
    # rollen staan in prio volgorde
    ROL_BB = 2          # Manager MH
    ROL_BKO = 3         # BK organisator, specifieke competitie
    ROL_RKO = 4         # RK organisator, specifieke competitie en rayon
    ROL_RCL = 5         # Regiocompetitieleider, specifieke competitie en regio
    ROL_HWL = 6         # Hoofdwedstrijdleider van een vereniging, alle competities
    ROL_WL = 7          # Wedstrijdleider van een vereniging, alle competities
    ROL_SEC = 10        # Secretaris van een vereniging
    ROL_LA = 11         # Leden-administrator van een vereniging
    ROL_SPORTER = 20    # Individuele sporter en (gast-)lid
    ROL_MWZ = 30        # Manager Wedstrijdzaken
    ROL_MO = 40         # Manager Opleidingen
    ROL_MWW = 50        # Manager Webwinkel
    ROL_MLA = 55        # Manager Ledenadministratie
    ROL_CS = 60         # Commissie Scheidsrechters
    ROL_SUP = 90        # Support
    ROL_NONE = 99       # geen rol (gebruik: niet ingelogd)

    """ LET OP!
        rol nummers worden opgeslagen in de sessie
            verwijderen = probleem voor terugkerende gebruiker
            hergebruiken = gevaarlijk: gebruiker 'springt' naar nieuwe rol! 
        indien nodig alle sessies verwijderen
    """


url2rol = {
    'BB': Rol.ROL_BB,
    'BKO': Rol.ROL_BKO,
    'RKO': Rol.ROL_RKO,
    'RCL': Rol.ROL_RCL,
    'HWL': Rol.ROL_HWL,
    'WL': Rol.ROL_WL,
    'SEC': Rol.ROL_SEC,
    'LA': Rol.ROL_LA,
    'MO': Rol.ROL_MO,
    'MWZ': Rol.ROL_MWZ,
    'MWW': Rol.ROL_MWW,
    'MLA': Rol.ROL_MLA,
    'CS': Rol.ROL_CS,
    'support': Rol.ROL_SUP,
    'sporter': Rol.ROL_SPORTER,
    'geen': Rol.ROL_NONE
}

# wordt beperkt gebruikt:
# - in activeer-rol, voor BB en Sporter
# - in wissel-van-rol template, <meta property="mh:rol" content="xxx"> voor e2e_check_rol()
rol2url = {value: key for key, value in url2rol.items()}

functie_rol_str2rol = {
    "BKO": Rol.ROL_BKO,
    "RKO": Rol.ROL_RKO,
    "RCL": Rol.ROL_RCL,
    "HWL": Rol.ROL_HWL,
    "WL": Rol.ROL_WL,
    "SEC": Rol.ROL_SEC,
    "LA": Rol.ROL_LA,
    "MO": Rol.ROL_MO,
    "MWZ": Rol.ROL_MWZ,
    "MWW": Rol.ROL_MWW,
    'MLA': Rol.ROL_MLA,
    "SUP": Rol.ROL_SUP,
    "CS": Rol.ROL_CS,
}


# end of file
