# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

REGISTRATIE_FASE_BEGIN = 0
REGISTRATIE_FASE_EMAIL = 1      # wacht op bevestiging toegang e-mail
REGISTRATIE_FASE_PASSWORD = 2
REGISTRATIE_FASE_LAND = 3
REGISTRATIE_FASE_BOND = 4
REGISTRATIE_FASE_AGE = 5
REGISTRATIE_FASE_PHONE = 6
REGISTRATIE_FASE_DONE = 99

REGISTRATIE_FASE2STR = {
    REGISTRATIE_FASE_BEGIN: "Begin",
    REGISTRATIE_FASE_EMAIL: "Email",
    REGISTRATIE_FASE_LAND: "Land",
    REGISTRATIE_FASE_BOND: "Bond",
    REGISTRATIE_FASE_AGE: "Age",
    REGISTRATIE_FASE_PHONE: "Phone",
    REGISTRATIE_FASE_DONE: "Done",
}

# end of file
