# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import transaction
from Registreer.models import GastLidNummer, GAST_LID_NUMMER_FIXED_PK


def registratie_gast_volgende_lid_nr():
    """ Neem het volgende lid_nr voor gast accounts uit """
    with transaction.atomic():
        volgende = (GastLidNummer
                    .objects
                    .select_for_update()                 # lock tegen concurrency
                    .get(pk=GAST_LID_NUMMER_FIXED_PK))

        # het volgende nummer is het nieuwe unieke nummer
        volgende.volgende_lid_nr += 1
        volgende.save()

        nummer = volgende.volgende_lid_nr

    return nummer


def registratie_gast_is_open():
    """
        Deze functie vertelt of nieuwe gast-accounts aangemaakt mogen worden.
        Return value:
            True  = Registratie is open
            False = Geen nieuwe gast-accounts meer registreren
    """
    volgende = (GastLidNummer
                .objects
                .get(pk=GAST_LID_NUMMER_FIXED_PK))

    return volgende.kan_aanmaken


# end of file
