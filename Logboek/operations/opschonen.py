# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Logboek.models import LogboekRegel
import datetime


def logboek_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen logboek entries die meer dan 18 maanden oud zijn
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=548)        # requirement 18 months --> 365*1.5=548

    objs = (LogboekRegel
            .objects
            .filter(toegevoegd_op__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s oude logboek regels' % count)
        objs.delete()


# end of file
