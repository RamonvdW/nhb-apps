# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from DataApi.models import DataApiLidmaatschap
import datetime


def dataapi_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        we verwijderen lidmaatschappen die meer dan 5 jaar geleden afgemeld zijn
    """

    now = datetime.datetime.now()
    oudste_afmeld_datum = now - datetime.timedelta(days=settings.DDI_LMS_KEEP_HISTORY_DAYS)
    oudste_mutatie_datum = now - datetime.timedelta(days=settings.DDI_LMS_KEEP_MUTATED_DAYS)

    qset = DataApiLidmaatschap.objects.exclude(afmeld_datum='')
    qset = qset.exclude(mutatie_datum__gte=oudste_mutatie_datum)
    qset = qset.exclude(afmeld_datum__gte=oudste_afmeld_datum)

    count = qset.count()
    stdout.write('[INFO] Opschonen DataApi: %s lidmaatschappen worden verwijderd' % qset.count())

    if count > 0:
        qset.delete()

# end of file
