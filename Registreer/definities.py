# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

REGISTRATIE_FASE_BEGIN = 0
REGISTRATIE_FASE_EMAIL = 2      # wacht op bevestiging toegang e-mail
REGISTRATIE_FASE_PASS = 4
REGISTRATIE_FASE_CLUB = 5
REGISTRATIE_FASE_LAND = 6
REGISTRATIE_FASE_AGE = 7
REGISTRATIE_FASE_TEL = 8
REGISTRATIE_FASE_WA_ID = 9
REGISTRATIE_FASE_GENDER = 10
REGISTRATIE_FASE_CONFIRM = 25
REGISTRATIE_FASE_COMPLEET = 99
REGISTRATIE_FASE_AFGEWEZEN = 100

REGISTRATIE_FASE2STR = {
    REGISTRATIE_FASE_BEGIN: "Begin",
    REGISTRATIE_FASE_EMAIL: "Email",
    REGISTRATIE_FASE_PASS: "Wachtwoord",
    REGISTRATIE_FASE_CLUB: "Club",
    REGISTRATIE_FASE_LAND: "Land",
    REGISTRATIE_FASE_AGE: "Age",
    REGISTRATIE_FASE_TEL: "Telefoon",
    REGISTRATIE_FASE_WA_ID: "WA ID",
    REGISTRATIE_FASE_GENDER: "Geslacht",
    REGISTRATIE_FASE_CONFIRM: "Bevestigen",
    REGISTRATIE_FASE_COMPLEET: "Compleet",
    REGISTRATIE_FASE_AFGEWEZEN: "Afgewezen"
}

# end of file
