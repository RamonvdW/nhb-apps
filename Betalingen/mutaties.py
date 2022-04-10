# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Betalingen.models import (BetalingenMutatie, BETALINGEN_MUTATIE_AFREKENEN,
                               BetalingenHoogsteBoekingsnummer, BETALINGEN_HOOGSTE_PK)
from Overig.background_sync import BackgroundSync
import time


betalingen_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__BETALINGEN_MUTATIES)


def betaling_get_volgende_boekingsnummer():
    """ Neem een uniek boekingsnummer uit """

    hoogste = (BetalingenHoogsteBoekingsnummer
               .objects
               .select_for_update()         # lock tegen concurrency
               .get(pk=BETALINGEN_HOOGSTE_PK))

    # het volgende nummer is het nieuwe unieke nummer
    hoogste.hoogste_gebruikte_boekingsnummer += 1
    hoogste.save()

    return hoogste.hoogste_gebruikte_boekingsnummer


def betalingen_start_afrekenen(boekingsnummer, snel):
    """
        Verwijder een nog niet betaalde reservering voor een kalenderwedstrijd

        inschrijving: de kalender inschrijving
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    mutatie = BetalingenMutatie(
                    code=BETALINGEN_MUTATIE_AFREKENEN,
                    boekingsnummer=boekingsnummer)
    mutatie.save()

    # ping het achtergrond process
    betalingen_mutaties_ping.ping()

    if not snel:         # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2      # om steeds te verdubbelen
        total = 0.0         # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie = BetalingenMutatie.objects.get(pk=mutatie.pk)
        # while


# end of file
