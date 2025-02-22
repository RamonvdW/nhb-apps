# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Vereniging.definities import VER_NR_BONDSBUREAU

THUMB_SIZE = (96, 96)

KEUZE_STATUS_RESERVERING_MANDJE = 'M'        # in mandje; moet nog omgezet worden in een bestelling
KEUZE_STATUS_BESTELD = 'B'       # besteld; moet nog betaald worden
KEUZE_STATUS_BACKOFFICE = 'BO'               # betaling voldaan; ligt bij backoffice voor afhandeling
KEUZE_STATUS_GEANNULEERD = 'A'               # bestelling geannuleerd
# FUTURE: KEUZE_STATUS_VERSTUURD        # afgehandeld door backoffice en verstuurd
# FUTURE: track en trace code voor in de mail naar koper


KEUZE_STATUS_CHOICES = (
    (KEUZE_STATUS_RESERVERING_MANDJE, "Reservering"),
    (KEUZE_STATUS_BESTELD, "Besteld"),
    (KEUZE_STATUS_BACKOFFICE, "Betaald"),
    (KEUZE_STATUS_GEANNULEERD, "Geannuleerd")
)

KEUZE_STATUS_TO_STR = {
    KEUZE_STATUS_RESERVERING_MANDJE: 'Gereserveerd, in mandje',
    KEUZE_STATUS_BESTELD: 'Gereserveerd, wacht op betaling',
    KEUZE_STATUS_BACKOFFICE: 'Betaald; doorgegeven aan backoffice voor afhandeling',
    KEUZE_STATUS_GEANNULEERD: 'Geannuleerd'
}

KEUZE_STATUS_TO_SHORT_STR = {
    KEUZE_STATUS_RESERVERING_MANDJE: 'In mandje',
    KEUZE_STATUS_BESTELD: 'Besteld',
    KEUZE_STATUS_BACKOFFICE: 'Betaald',
    KEUZE_STATUS_GEANNULEERD: 'Geannuleerd'
}


VERZENDKOSTEN_PAKKETPOST = "pak"
VERZENDKOSTEN_BRIEFPOST = "brief"       # max 5 lang

VERZENDKOSTEN_CHOICES = (
    (VERZENDKOSTEN_PAKKETPOST, "Pakketpost"),
    (VERZENDKOSTEN_BRIEFPOST, "Briefpost"),
)

WEBWINKEL_VERKOPENDE_VER_NR = VER_NR_BONDSBUREAU

# end of file
