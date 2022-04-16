# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Betaal.models import (BetaalMutatie, BETAAL_MUTATIE_START_ONTVANGST, BETAAL_MUTATIE_START_RESTITUTIE,
                           BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED)
from Overig.background_sync import BackgroundSync
import time


betalingen_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__BETALINGEN_MUTATIES)



def betalingen_start_ontvangst(tbd, snel):
    """
        Begin het afrekenen van een bestelling.

        boekingsnummer: Het nummer van de bestelling
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    mutatie = BetaalMutatie(
                    code=BETAAL_MUTATIE_START_ONTVANGST)        # TODO: more fields
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
            mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        # while


def betaal_payment_status_changed(payment_id, snel):
    """
        De status van een betaling is gewijzigd

        payment_id: de identificatie van de transactie
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    mutatie = BetaalMutatie(
                    code=BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED)     # TODO: more fields
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
            mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        # while


# end of file
