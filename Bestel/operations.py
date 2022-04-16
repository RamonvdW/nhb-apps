# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import transaction
from Bestel.models import BestelHoogsteBestelNr, BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK


def bestel_get_volgende_bestel_nr():

    """ Neem een uniek bestelnummer uit """

    with transaction.atomic():
        hoogste = (BestelHoogsteBestelNr
                   .objects
                   .select_for_update()         # lock tegen concurrency
                   .get(pk=BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK))

        # het volgende nummer is het nieuwe unieke nummer
        hoogste.hoogste_gebruikte_bestel_nr += 1
        hoogste.save()

        nummer = hoogste.hoogste_gebruikte_bestel_nr

    return nummer


# end of file
