# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Competitie.models import CompetitieMutatie
from Site.core.background_sync import BackgroundSync
import time

competitie_mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__COMPETITIE_MUTATIES)


def ping_achtergrondtaak(mutatie: CompetitieMutatie, snel: bool):
    """ wekt de achtergrondtaak en wacht (tenzij snel=True) tot de mutatie afgehandeld is """

    # ping de achtergrondtaak
    competitie_mutatie_ping.ping()

    if not snel:        # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0     # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie.refresh_from_db()
        # while


# end of file
