# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Betaal.definities import BETAAL_MUTATIE_START_ONTVANGST, BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED
from Betaal.models import BetaalMutatie
from Site.core.background_sync import BackgroundSync
import datetime
import time


""" Interface naar de achtergrondtaak, waar de mutaties uitgevoerd worden zonder concurrency gevaren """


betaal_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__BETAAL_MUTATIES)


def _betaal_ping_achtergrondtaak(mutatie, snel):

    # ping het achtergrond process
    betaal_mutaties_ping.ping()

    if not snel:  # pragma: no cover
        # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
        interval = 0.2  # om steeds te verdubbelen
        total = 0.0  # om een limiet te stellen
        while not mutatie.is_verwerkt and total + interval <= 3.0:
            time.sleep(interval)
            total += interval  # 0.0 --> 0.2, 0.6, 1.4, 3.0
            interval *= 2  # 0.2 --> 0.4, 0.8, 1.6, 3.2
            mutatie = BetaalMutatie.objects.get(pk=mutatie.pk)
        # while


def betaal_mutatieverzoek_start_ontvangst(bestelling, beschrijving, bedrag_euro, url_betaling_gedaan, snel):
    """
        Begin het afrekenen van een bestelling.

        boekingsnummer: Het nummer van de bestelling
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    recent = timezone.now() - datetime.timedelta(seconds=30)

    # zet dit verzoek door naar het mutaties process
    # voorkom duplicates (niet 100%)
    try:
        mutatie, is_created = BetaalMutatie.objects.get_or_create(
                                        when__gt=recent,
                                        code=BETAAL_MUTATIE_START_ONTVANGST,
                                        ontvanger=bestelling.ontvanger,
                                        beschrijving=beschrijving,
                                        bedrag_euro=bedrag_euro,
                                        url_betaling_gedaan=url_betaling_gedaan)
    except BetaalMutatie.objects.MultipleObjectsReturned:       # pragma: no cover
        # al meerdere verzoeken in de queue
        mutatie = None
    else:
        mutatie.save()

        # voorkom dat we nog een keer hetzelfde pad doorlopen
        bestelling.betaal_mutatie = mutatie
        bestelling.save(update_fields=['betaal_mutatie'])

        if is_created:                                      # pragma: no branch
            # wacht kort op de achtergrondtaak
            _betaal_ping_achtergrondtaak(mutatie, snel)

    return mutatie


def betaal_mutatieverzoek_payment_status_changed(payment_id):
    """
        De status van een betaling is gewijzigd

        payment_id: de identificatie van de transactie
        snel = True: niet wachten op reactie achtergrond taak (voor testen)
    """

    # zet dit verzoek door naar het mutaties process
    mutatie = BetaalMutatie(
                    code=BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED,
                    payment_id=payment_id)
    mutatie.save()

    # ping het achtergrond process maar wacht niet op een reactie
    betaal_mutaties_ping.ping()


# end of file
