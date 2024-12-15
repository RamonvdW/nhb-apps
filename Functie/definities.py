# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Functie.rol import Rollen


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
    'CS': Rollen.ROL_CS,
    'support': Rollen.ROL_SUP,
    'sporter': Rollen.ROL_SPORTER,
    'geen': Rollen.ROL_NONE
}

rol2url = {value: key for key, value in url2rol.items()}

functie_rol_str2rol = {
    "BKO": Rollen.ROL_BKO,
    "RKO": Rollen.ROL_RKO,
    "RCL": Rollen.ROL_RCL,
    "HWL": Rollen.ROL_HWL,
    "WL": Rollen.ROL_WL,
    "SEC": Rollen.ROL_SEC,
    "MO": Rollen.ROL_MO,
    "MWZ": Rollen.ROL_MWZ,
    "MWW": Rollen.ROL_MWW,
    "SUP": Rollen.ROL_SUP,
    "CS": Rollen.ROL_CS,
}


# end of file
