# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.models import Competitie
from Functie.rol import Rollen


def is_competitie_openbaar_voor_rol(comp: Competitie, rol_nu: Rollen):
    """ geeft True terug als de competitie voor het openbaar is,
                         of rol_nu beheerder is voor deze competitie.
    """

    # BB en BKO mogen alles zien
    if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
        return True

    # beheerders die de competitie opzetten zien competities die opgestart zijn
    if rol_nu in (Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL):
        return True

    # modale gebruiker ziet alleen competities vanaf open-voor-inschrijving
    return comp.is_openbaar_voor_publiek()


# end of file