# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Scheidsrechter.definities import SCHEIDS_MUTATIE_BESCHIKBAARHEID_OPVRAGEN
from Scheidsrechter.models import ScheidsMutatie
from Overig.background_sync import BackgroundSync
import datetime
import time


""" Interface naar de achtergrondtaak, waar de mutaties uitgevoerd worden zonder concurrency gevaren """


scheids_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__SCHEIDS_MUTATIES)


def _scheids_ping_achtergrondtaak(mutatie, snel):

    # ping het achtergrond process
    scheids_mutaties_ping.ping()

    if not snel:  # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0  # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval  # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2  # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie = ScheidsMutatie.objects.get(pk=mutatie.pk)
        # while


def scheids_mutatieverzoek_beschikbaarheid_opvragen(wedstrijd, door_str, snel):
    """
        Beschikbaarheid van SR opvragen voor specifieke wedstrijd.

        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    recent = timezone.now() - datetime.timedelta(seconds=30)

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    try:
        mutatie, is_created = ScheidsMutatie.objects.get_or_create(
                                        when__gt=recent,
                                        mutatie=SCHEIDS_MUTATIE_BESCHIKBAARHEID_OPVRAGEN,
                                        door=door_str,
                                        wedstrijd=wedstrijd)
    except ScheidsMutatie.objects.MultipleObjectsReturned:      # pragma: no cover
        # al meerdere verzoeken in de queue
        mutatie = None
    else:
        mutatie.save()

        if is_created:                                          # pragma: no branch
            # wacht kort op de achtergrondtaak
            _scheids_ping_achtergrondtaak(mutatie, snel)

    return mutatie


# end of file
