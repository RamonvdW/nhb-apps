# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import enum


class Rollen(enum.IntEnum):
    """ definitie van de rollen met codes
        vertaling naar beschrijvingen in Plein.views
    """

    # rollen staan in prio volgorde
    ROL_BB = 2          # Manager Competitiezaken
    ROL_BKO = 3         # BK organisator, specifieke competitie
    ROL_RKO = 4         # RK organisator, specifieke competitie en rayon
    ROL_RCL = 5         # Regiocompetitieleider, specifieke competitie en regio
    ROL_HWL = 6         # Hoofdwedstrijdleider van een vereniging, alle competities
    ROL_WL = 7          # Wedstrijdleider van een vereniging, alle competities
    ROL_SEC = 10        # Secretaris van een vereniging
    ROL_SPORTER = 20    # Individuele sporter en lid
    ROL_MWZ = 30        # Manager Wedstrijdzaken
    ROL_MO = 40         # Manager Opleidingen
    ROL_MWW = 50        # Manager Webwinkel
    ROL_SUP = 90        # Support
    ROL_NONE = 99       # geen rol (gebruik: niet ingelogd)

    """ LET OP!
        rol nummers worden opgeslagen in de sessie
            verwijderen = probleem voor terugkerende gebruiker
            hergebruiken = gevaarlijk: gebruiker 'springt' naar nieuwe rol! 
        indien nodig alle sessies verwijderen
    """


url2rol = {
    'BB': Rollen.ROL_BB,
    'BKO': Rollen.ROL_BKO,
    'RKO': Rollen.ROL_RKO,
    'RCL': Rollen.ROL_RCL,
    'HWL': Rollen.ROL_HWL,
    'WL': Rollen.ROL_WL,
    'SEC': Rollen.ROL_SEC,
    'MO': Rollen.ROL_MO,
    'MWZ': Rollen.ROL_MWZ,
    'MWW': Rollen.ROL_MWW,
    'support': Rollen.ROL_SUP,
    'sporter': Rollen.ROL_SPORTER,
    'geen': Rollen.ROL_NONE
}

rol2url = {value: key for key, value in url2rol.items()}


# end of file
