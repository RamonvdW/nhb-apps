# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Kalender.models import (KalenderMutatie, KALENDER_MUTATIE_AFMELDEN,
                             KalenderWedstrijdKortingscode, KALENDER_MUTATIE_KORTING)
from Overig.background_sync import BackgroundSync
import time


kalender_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__KALENDER_MUTATIES)


def kalender_kortingscode_toepassen(account, code, snel):
    """
        Voeg een kortingscode toe aan een inschrijving voor een wedstrijd

        account = voor welk account?
        code = de code (string)
        snel = True: niet wachten op reactie achtergrond taak (voor testen)

        Retourneert:
            True = gelukt, code is toegepast
            False = geen valide code, niet toegepast
    """

    # TODO: rate limiter

    result = False

    now = timezone.now()
    today = now.date()

    # doe een sanity-check of de code gebruikt mag worden
    for korting in (KalenderWedstrijdKortingscode               # pragma: no branch
                    .objects
                    .filter(code__iexact=code,  # case insensitive
                            geldig_tot_en_met__gte=today)):

        # laat het achtergrond process de code toepassen
        mutatie = KalenderMutatie(
                        code=KALENDER_MUTATIE_KORTING,
                        korting=korting,
                        korting_voor_account=account)
        mutatie.save()

        result = True

        # ping het achtergrond process
        kalender_mutaties_ping.ping()

        if not snel:                                             # pragma: no cover
            # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
            interval = 0.2                  # om steeds te verdubbelen
            total = 0.0                     # om een limiet te stellen
            while not mutatie.is_verwerkt and total + interval <= 3.0:
                time.sleep(interval)
                total += interval           # 0.0 --> 0.2, 0.6, 1.4, 3.0
                interval *= 2               # 0.2 --> 0.4, 0.8, 1.6, 3.2
                mutatie = KalenderMutatie.objects.get(pk=mutatie.pk)
            # while

        break       # from the for
    # for

    return result


def kalender_verwijder_reservering(inschrijving, snel):
    """
        Verwijder een nog niet betaalde reservering voor een kalenderwedstrijd

        inschrijving: de kalender inschrijving
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    mutatie = KalenderMutatie(
                    code=KALENDER_MUTATIE_AFMELDEN,         # TODO: Rename?
                    inschrijving=inschrijving)
    mutatie.save()

    # ping het achtergrond process
    kalender_mutaties_ping.ping()

    if not snel:         # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2      # om steeds te verdubbelen
        total = 0.0         # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie = KalenderMutatie.objects.get(pk=mutatie.pk)
        # while


# end of file
