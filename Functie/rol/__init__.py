# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .activeer import rol_activeer_rol, rol_activeer_functie
from .bepaal import RolBepaler, rol_eval_rechten_simpel
from .beschrijving import rol_zet_beschrijving, rol_get_beschrijving
from .huidige import rol_get_huidige, rol_get_huidige_functie
from .mag_wisselen import (rol_mag_wisselen, rol_zet_mag_wisselen,
                           rol_zet_mag_wisselen_voor_account)
from .scheids import gebruiker_is_scheids

__all__ = [
    'rol_activeer_rol',
    'rol_activeer_functie',

    'rol_zet_beschrijving',
    'rol_get_beschrijving',

    'rol_get_huidige',
    'rol_get_huidige_functie',

    'rol_mag_wisselen',
    'rol_zet_mag_wisselen',
    'rol_zet_mag_wisselen_voor_account',
    'rol_eval_rechten_simpel',

    'RolBepaler',

    'gebruiker_is_scheids',
]

# end of file
