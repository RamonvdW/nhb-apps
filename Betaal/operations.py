# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Betaal.definities import TRANSACTIE_TYPE_HANDMATIG
from Betaal.models import BetaalActief, BetaalTransactie, BetaalMutatie
from datetime import timedelta
from decimal import Decimal


def betaal_opschonen(stdout):
    """ Database opschonen """

    now = timezone.now()

    # alles ouder dan 18 maanden kan weg
    # want refunds zijn soms na 365 dagen nog mogelijk
    max_age = now - timedelta(days=365 + 183)

    if True:
        objs = (BetaalMutatie
                .objects
                .filter(when__lt=max_age))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s oude betaal mutatie records' % count)
            objs.delete()

    if True:
        objs = (BetaalActief
                .objects
                .filter(when__lt=max_age))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s oude betaal-actief records' % count)
            objs.delete()

    if True:
        objs = (BetaalTransactie
                .objects
                .filter(when__lt=max_age))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s oude betaal-transactie records' % count)
            objs.delete()


def maak_transactie_handmatige_overboeking(bedrag_euro: Decimal):
    now = timezone.now()

    transactie = BetaalTransactie(
                    when=now,
                    transactie_type=TRANSACTIE_TYPE_HANDMATIG,
                    beschrijving='Overboeking ontvangen',
                    bedrag_handmatig=bedrag_euro)
    transactie.save()

    return transactie


# end of file
