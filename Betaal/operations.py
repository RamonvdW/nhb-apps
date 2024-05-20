# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from datetime import timedelta
from Betaal.models import BetaalActief, BetaalTransactie, BetaalMutatie


def betaal_opschonen(stdout):
    """ Database opschonen """

    if True:
        # alles ouder dan 6 maanden mag weg
        now = timezone.now()
        max_age = now - timedelta(days=182)

        objs = (BetaalMutatie
                .objects
                .filter(when__lt=max_age))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s oude betaal mutatie records' % count)
            objs.delete()

    if True:
        # alles ouder dan 6 maanden mag weg
        now = timezone.now()
        max_age = now - timedelta(days=182)

        objs = (BetaalActief
                .objects
                .filter(when__lt=max_age))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s oude betaal-actief records' % count)
            objs.delete()

    if True:
        # alles ouder dan 18 maanden kan weg
        now = timezone.now()
        max_age = now - timedelta(days=365 + 183)

        objs = (BetaalTransactie
                .objects
                .filter(when__lt=max_age))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s oude betaal-transactie records' % count)
            objs.delete()


# end of file
