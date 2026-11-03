# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

VER_NR_BONDSBUREAU = 1368

TYPE_EXTERNE_SCORES_ONBEKEND = 0
TYPE_EXTERNE_SCORES_CENTAUR = 1
TYPE_EXTERNE_SCORES_ARROWCAST = 2       # HS Hilversum

TYPE_EXTERNE_SCORES_CHOICES = (
    (TYPE_EXTERNE_SCORES_ONBEKEND, "Onbekend"),
    (TYPE_EXTERNE_SCORES_CENTAUR, "Centaur"),
    (TYPE_EXTERNE_SCORES_ARROWCAST, "Arrowcast"))

TYPE2STR = {
    TYPE_EXTERNE_SCORES_ONBEKEND: "Onbekend",
    TYPE_EXTERNE_SCORES_CENTAUR: "Centaur",
    TYPE_EXTERNE_SCORES_ARROWCAST: "Arrowcast",
}


# end of file
